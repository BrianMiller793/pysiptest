# vim: ai ts=4 sw=4 et
'''
Datagram transport protocol, implementing echo for RTP.
RFC 3550 - RTP: A Transport Protocol for Real-Time Applications
RFC 1889 - obsoleted by 3550
'''

import asyncio
import logging

logger = logging.getLogger()

class RtpEcho:
    '''Base datagram transport protocol for delayed echo.'''
    # pylint: disable=R0902
    def __init__(self, loop:asyncio.unix_events._UnixSelectorEventLoop,
        on_con_lost:asyncio.Future=None, stun_addr=None):
        '''Class initialization.'''
        self.loop = loop
        self.on_con_lost = on_con_lost
        self.transport = None
        self.echo_queue = asyncio.Queue()
        self.fire_at = 0
        self.error_count = 0
        self.buffer_count = 0
        self.is_buffered = False
        self.dest_addr = None
        self.local_addr = None
        self.stun_addr = stun_addr

    @property
    def sdp_sockname(self):
        '''Represents either the local sockname or STUN sockname.'''
        return self.stun_addr if self.stun_addr else self.local_addr

    def begin(self):
        '''Begin RTP stream.'''
        # Interface place holder.

    def end(self):
        '''End RTP stream.'''
        # Interface place holder.

    def connection_made(self, transport):
        '''Base transport'''
        logger.debug('RtpEcho:connection_made')
        self.transport = transport
        self.local_addr = transport.get_extra_info('socket').getsockname()

    def connection_lost(self, exc):
        '''Base transport'''
        logger.debug('RtpEcho:connection_lost: %s', str(exc))
        if self.on_con_lost:
            self.on_con_lost.set_result(True)

    def datagram_received(self, data, addr): # pylint: disable=W0613
        '''Datagram transport'''
        self.echo_queue.put_nowait((data, addr))

        if self.buffer_count < 5:
            self.buffer_count += 1
            return

        if self.is_buffered is False:
            if self.fire_at == 0:
                self.fire_at = self.loop.time()
            self.fire_at += 0.02
            self.loop.call_at(self.fire_at, self.callback_event)
            self.is_buffered = True

    def error_received(self, exc):
        '''Error handler for protocol.'''
        logger.error('RtpEcho:error_received: %s', str(exc))
        self.error_count += 1
        if self.error_count > 4:
            logger.error('RtpEcho:error_received:closing')
            self.transport.close()

    def callback_event(self):
        '''The callback sends data at roughly 20ms intervals.'''
        if not self.echo_queue.empty():
            packet = self.echo_queue.get_nowait()
            self.transport.sendto(packet[0], addr=packet[1])
            self.fire_at += 0.02
            self.loop.call_at(self.fire_at, self.callback_event)
