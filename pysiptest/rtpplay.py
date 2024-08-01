# vim: ai ts=4 sw=4 et
'''
Datagram transport protocol, impementing echo for RTP.
RFC 3550 - RTP: A Transport Protocol for Real-Time Applications
RFC 1889 - obsoleted by 3550
'''

import asyncio
import logging
from time import time

import dpkt
import ntplib

def short(sys_time):
    '''Convert system time to NTP short format.'''
    ntp_time = ntplib.system_to_ntp_time(sys_time)
    # pylint: disable=W0212
    return (ntplib._to_int(ntp_time) << 16 & 0xFFFFFFFF) | \
        ntplib._to_frac(ntp_time, 16)

class RtpPlay:
    '''Base datagram transport protocol for replay of pcap file.'''
    # pylint: disable=R0902
    def __init__(self, loop:asyncio.unix_events._UnixSelectorEventLoop,
        on_con_lost:asyncio.Future=None, file_name:str=None):
        '''Class initialization.'''
        # on_con_lost: Future object for completion
        self.on_con_lost = on_con_lost
        self.file_name = file_name
        self.loop = loop
        self.transport = None
        self.rtp_queue = asyncio.Queue()
        self.buffer_count = 0
        self.fire_at = 0
        self.timestamp = 0
        self.dest_addr = None
        self.local_addr = None
        self.is_playing = True

        # pylint: disable=R1732
        assert self.file_name is not None
        self.pcap_file = open(self.file_name, mode='rb')
        self.pcap_rdr = dpkt.pcap.Reader(self.pcap_file)
        for _ in range(5):
            self._read_rtp()

    def _read_rtp(self):
        '''Read an RTP packet from a pcap file.'''
        # PCAP file may contain non-RTP packets
        found_rtp = False
        while not found_rtp:
            try:
                _, buf = next(iter(self.pcap_rdr))
            except StopIteration as _:
                self.pcap_file.seek(0)
                self.pcap_rdr = dpkt.pcap.Reader(self.pcap_file)
                _, buf = next(iter(self.pcap_rdr))
            ether = dpkt.ethernet.Ethernet(buf)
            if isinstance(ether.data, dpkt.ip.IP):
                ip = ether.data # pylint: disable=C0103
                if isinstance(ip.data, dpkt.udp.UDP):
                    udp = ip.data
                    try:
                        packet = dpkt.rtp.RTP()
                        packet.unpack(udp.data)
                        if packet.version == 2 and \
                            packet.pt == 0 and \
                            len(packet) == 172:
                            self.rtp_queue.put_nowait(packet)
                            found_rtp = True
                    except dpkt.UnpackError as _:
                        pass

    def begin(self):
        '''Begin RTP stream.'''
        logging.debug('RtpPlay:begin')
        self.fire_at = self.loop.time() + 0.02
        self.timestamp = short(time())
        self.loop.call_at(self.fire_at, self.callback_event)

    def end(self):
        '''End RTP stream.'''
        logging.debug('RtpPlay:end')
        self.is_playing = False
        self.transport.close()
        # Interface place holder.

    def connection_made(self, transport):
        '''Base transport'''
        logging.debug('RtpPlay:connection_made')
        self.transport = transport
        self.local_addr = transport.get_extra_info('socket').getsockname()

    def connection_lost(self, exc):
        '''Base transport'''
        logging.debug('RtpPlay:connection_lost: %s', str(exc))
        if self.on_con_lost:
            self.on_con_lost.set_result(True)
        self.is_playing = False

    def datagram_received(self, data, addr):
        '''Datagram transport'''
        # Play ignores all received data

    def error_received(self, exc):
        '''Error handler for protocol.'''
        logging.error('RtpPlay:error_received: %s', str(exc))
        # self.transport.close()

    def callback_event(self):
        '''The callback sends data at roughly 20ms intervals.'''
        if not self.rtp_queue.empty() and self.is_playing:
            rtp_pkt = self.rtp_queue.get_nowait()
            rtp_pkt.ts = self.timestamp
            self.timestamp += 0xA0
            self.transport.sendto(rtp_pkt.pack(), addr=self.dest_addr)
            self.fire_at += 0.02
            self.loop.call_at(self.fire_at, self.callback_event)
            self._read_rtp()
