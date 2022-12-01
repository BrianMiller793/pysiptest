# vim: ai ts=4 sw=4 et
'''
Protocol factory supporting SIP phone.
'''

import asyncio
import copy
import logging
import os
import random
import sys
sys.path.append(os.getenv('PYSIP_LIB_PATH'))
# pylint: disable=E0401,C0413
import headerfield as hf
import sipmsg

def sip_sdp(owner, sockname=None, network='IN IP4') -> str:
    '''Create SDP info

    :param owner: Domain, extension, user name, or manufacturer
    :param sockname: Tuple returned by getsockname()
    :return str:'''

    assert sockname is not None
    assert isinstance(sockname, tuple)
    logging.debug('sip_sdp:sockname=%s', sockname)
    ipaddr = sockname[0]
    audio_port = sockname[1]
    random.seed()
    session_id = random.randint(32768, 65535)
    version = random.randint(32768, 65535)

    return f'''v=0
o={owner} {session_id} {version} {network} {ipaddr}
s=A conversation
c=IN IP4 {ipaddr}
t=0 0
m=audio {audio_port} RTP/AVP 0 9 101
a=rtpmap:0 PCMU/8000
a=rtpmap:9 G722/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-15
a=sendrecv
'''.replace('\n', '\r\n')

class SipPhoneUdpClient:
    '''
    Factory transport class to support SIP protocol.
    '''
    def __init__(self, on_con_lost:asyncio.Future):
        '''Initialize the echo client'''
        logging.info('__init__')
        self.on_con_lost = on_con_lost
        self.transport = None
        self.recvd_pkts = []                # all received packets (string)
        self.sent_msgs = []                 # all sent SIP messages
        self.rcv_queue = asyncio.Queue()    # received packets for Behave

    def get_prev_sent(self, method:str) -> sipmsg.SipMessage:
        '''Get a copy of a previously sent message.

        :param method: Method name to match, from last sent message.
        :retval sipmsg.SipMessage: Message matching method, or None.'''
        for i in range(len(self.sent_msgs)-1, -1, -1):
            if self.sent_msgs[i].method == method:
                return copy.deepcopy(self.sent_msgs[i])
        return None

    def get_prev_rcvd(self, method:str) -> str:
        '''Get a copy of a previously received message.

        :param method: Method name or code, starting from last received message.
        :retval str: Matching message, or None.'''
        for i in range(len(self.recvd_pkts)-1, -1, -1):
            msg_line = self.recvd_pkts[i].splitlines()[0].split()[0:2]
            logging.debug('get_prev_rcvd:msg_line=%s', msg_line)
            if method in msg_line:
                return copy.deepcopy(self.recvd_pkts[i])
        return None

    def connection_made(self, transport):
        '''Base protcol: Called when a connection is made.'''
        logging.info('SipPhoneUdpClient:connection_made')
        self.transport = transport

    def connection_lost(self, exc):             # pylint: disable=W0613
        '''Base protcol: Called when a connection is lost or closed.'''
        logging.info('SipPhoneUdpClient:connection_lost')
        self.on_con_lost.set_result(True)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        logging.info('SipPhoneUdpClient:datagram_received')
        sip_msg = data.decode()
        logging.debug('SipPhoneUdpClient:datagram_received: sip_msg=%s', sip_msg)
        self.recvd_pkts.append(sip_msg)
        self.rcv_queue.put_nowait(sip_msg)

    def sendto(self, sip_msg: sipmsg.SipMessage):
        '''Send SIP message to UAS.'''
        logging.info('SipPhoneUdpClient:sendto')
        logging.debug('SipPhoneUdpClient:sendto: sipmsg=%s', str(sip_msg))
        self.sent_msgs.append(sip_msg)
        self.transport.sendto(str(sip_msg).encode())

    def error_received(self, exc):
        '''Datagram protcol: Called when an error is received.'''
        logging.info('SipPhoneUdpClient:error_received: %s', str(exc))

class AutoReply(SipPhoneUdpClient):
    '''Automatically reply for INFO, NOTIFY, OPTIONS and UPDATE.
    '''
    def __init__(self, on_con_lost, user_info:dict=None,
        rtp_sockname=None, call_future=None):
        super().__init__(on_con_lost)
        self.auto_reply = ['INFO', 'NOTIFY', 'OPTIONS', 'UPDATE']
        self.user_info = user_info
        self.rtp_sockname = rtp_sockname
        self.in_a_call = False
        self.call_future = call_future

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        sip_msg = data.decode()
        self.recvd_pkts.append(sip_msg)
        sip_method = sip_msg.split(maxsplit=1)[0]
        logging.info('AutoReply:datagram_received: %s', sip_method)
        logging.debug('AutoReply:datagram_received: %s', sip_msg)
        if sip_method in self.auto_reply:
            logging.info('AutoReply:datagram_received: auto reply to %s', sip_method)
            response = sipmsg.Response(status_code=200, reason_phrase='OK')
            response.method = sip_method
            response.init_from_msg(sip_msg)
            response.sort()
            self.sendto(response)
        else:
            self.rcv_queue.put_nowait(sip_msg)

class AutoAnswer(AutoReply):
    # State machine is currently implicit between steps and handler.
    '''Answer an incoming call.
    # wait for INVITE
    # send 100 Trying
    # send 180 Ringing
    # send 200 OK
    # wait for ACK
    '''
    def __init__(self, on_con_lost, user_info:dict=None,
        rtp_sockname=None, call_future=None):
        super().__init__(on_con_lost, user_info, rtp_sockname, call_future)
        self.to_tag = None

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        super().datagram_received(data, addr)
        # At this point, the INVITE or ACK packet may be in the queue.
        # If not, put packet back on queue and continue as normal.
        if self.rcv_queue.empty() or self.user_info is None:
            if self.user_info is None:
                logging.debug('AutoAnswer:datagram_received: user_info is None')
            return

        sip_msg = self.rcv_queue.get_nowait() # sip_msg is str
        sip_method = sip_msg.split(maxsplit=1)[0]
        if sip_method == 'INVITE':
            assert self.rtp_sockname is not None
            # TODO: get destination RTP port
            logging.info('AutoAnswer:datagram_received:INVITE')

            logging.info('AutoAnswer:datagram_received:sending:Trying')
            response = sipmsg.Response(
                prev_msg=sip_msg, status_code='100', reason_phrase='Trying')
            response.sort()
            self.sendto(str(response))

            logging.info('AutoAnswer:datagram_received:sending:Ringing')
            self.to_tag = hf.gen_tag()
            response = sipmsg.Response(
                prev_msg=sip_msg, status_code='180', reason_phrase='Ringing')
            response.field('To').tag = self.to_tag
            response.sort()
            self.sendto(str(response))

            logging.info('AutoAnswer:datagram_received:sending:OK')
            response = sipmsg.Response(
                prev_msg=sip_msg, status_code='200', reason_phrase='OK')
            response.field('To').tag = self.to_tag
            response.hdr_fields.append(hf.Content_Type(value='application/sdp'))
            response.hdr_fields.append(hf.Content_Disposition(value='session'))
            response.body = sip_sdp(owner=self.user_info['name'],
                sockname=self.rtp_sockname)
            response.sort()
            self.sendto(str(response))
        elif sip_method == 'ACK':
            logging.info('AutoAnswer:datagram_received:ACK')
            self.in_a_call = True
            if self.call_future is not None:
                logging.debug('AutoAnswer:datagram_received:call_future:True')
                self.call_future.set_result(True)
        else:
            self.rcv_queue.put_nowait(sip_msg)

    def sendto(self, sip_msg: sipmsg.SipMessage):
        # After call is through, user will need to recreate asyncio.Future
        # if it is still needed.
        if isinstance(sip_msg, sipmsg.SipMessage):
            if sip_msg.method == 'BYE':
                self.in_a_call = False
        super().sendto(sip_msg)
