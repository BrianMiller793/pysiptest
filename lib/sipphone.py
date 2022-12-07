# vim: ai ts=4 sw=4 et
'''
Protocol factory supporting SIP phone.
'''

import asyncio
import copy
import logging
import os
import sys

import support
sys.path.append(os.getenv('PYSIP_LIB_PATH'))
# pylint: disable=E0401,C0413
import headerfield as hf
import sipmsg

class SipPhoneUdpClient:
    '''
    Factory transport class to support SIP protocol.
    '''
    def __init__(self, **kwargs):
        '''Initialize the echo client'''
        self.on_con_lost = kwargs['on_con_lost'] \
            if 'on_con_lost' in kwargs else None
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
        if self.on_con_lost is not None:
            self.on_con_lost.set_result(True)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        logging.info('SipPhoneUdpClient:datagram_received')
        sip_msg = data.decode()
        logging.debug('SipPhoneUdpClient:datagram_received: sip_msg=%s', sip_msg)
        self.recvd_pkts.append(copy.copy(sip_msg))
        self.rcv_queue.put_nowait(copy.copy(sip_msg))

    def sendto(self, sip_msg: sipmsg.SipMessage):
        '''Send SIP message to UAS.'''
        logging.info('SipPhoneUdpClient:sendto')
        logging.debug('SipPhoneUdpClient:sendto: sipmsg=%s', str(sip_msg))
        self.sent_msgs.append(sip_msg)
        self.transport.sendto(str(sip_msg).encode())

    def error_received(self, exc):
        '''Datagram protcol: Called when an error is received.'''
        logging.info('SipPhoneUdpClient:error_received: %s', str(exc))

class KeepAlive(SipPhoneUdpClient):
    '''Provide OPTIONS keep-alive for an auto-answer endpoint.'''
    def __init__(self, **kwargs):
        '''Initialization

        :param on_con_lost:
        :param user_info:
        :param loop: Async IO loop
        :param rtp_sockname: RTP address tuple from getsockname()
        :param call_future:
        '''
        super().__init__(**kwargs)
        assert 'loop' in kwargs
        self.loop = kwargs['loop']
        assert 'user_info' in kwargs
        self.user_info = kwargs['user_info']
        self.options_msg = None
        self.fire_at = None
        self.branch = None

    def connection_made(self, transport):
        super().connection_made(transport)
        addr = transport.get_extra_info('socket').getsockname()

        # Create OPTIONS message, and save branch
        self.options_msg = support.sip_options(self.user_info, addr)
        self.branch = self.options_msg.field('Via').via_params['branch']
        self.fire_at = self.loop.time() + 10
        self.loop.call_at(self.fire_at, self.callback_event)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram Protocol: intercept OK from UAS.'''
        msg_dict = hf.msg2fields(data.decode())
        if self.branch not in msg_dict['Via']:
            logging.debug('KeepAlive:datagram_received')
            super().datagram_received(data, addr)

    def callback_event(self):
        '''This is event is fired to send the OPTIONS packet.'''
        self.sendto(self.options_msg)
        self.options_msg.field('CSeq').value += 1
        self.fire_at += 10
        self.loop.call_at(self.fire_at, self.callback_event)

class AutoReply(KeepAlive):
    '''Automatically reply for INFO, NOTIFY, OPTIONS and UPDATE.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_reply = ['INFO', 'NOTIFY', 'OPTIONS', 'UPDATE']

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        logging.debug('AutoReply:datagram_received')
        sip_msg = data.decode()
        sip_method = sip_msg.split(maxsplit=1)[0]
        if sip_method in self.auto_reply:
            logging.info('AutoReply:datagram_received: auto reply to %s', sip_method)
            response = sipmsg.Response(status_code=200, reason_phrase='OK')
            response.method = sip_method
            response.init_from_msg(sip_msg)
            response.sort()
            self.sendto(response)
            return

        super().datagram_received(data, addr)

class AutoAnswer(AutoReply):
    # State machine is currently implicit between steps and handler.
    '''Answer an incoming call.
       The RTP socket has been allocated, and the client is waiting for
       an INVITE.
    # wait for INVITE
    # send 100 Trying
    # send 180 Ringing
    # send 200 OK
    # wait for ACK
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.to_tag = None

        self.rtp_sockname = kwargs['rtp_sockname'] \
            if 'rtp_sockname' in kwargs else None
        self.call_future = kwargs['call_future'] \
            if 'call_future' in kwargs else None
        self.in_a_call = False

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        logging.debug('AutoAnswer:datagram_received')
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
            response.body = support.sip_sdp(owner=self.user_info['name'],
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
