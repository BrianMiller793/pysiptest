# vim: ai ts=4 sw=4 et
'''
Protocol factory supporting SIP phone.
'''

import asyncio
import logging
import os
import sys
sys.path.append(os.getenv('PYSIP_LIB_PATH'))
# pylint: disable=E0401,C0413
import sipmsg

class SipPhoneUdpClient:
    '''
    Factory transport class to support SIP protocol.
    '''
    def __init__(self, on_con_lost):
        '''Initialize the echo client'''
        logging.info('__init__')
        self.on_con_lost = on_con_lost
        self.transport = None
        self.recvd_pkts = []                # all received packets (string)
        self.sent_msgs = []                 # all sent SIP messages
        self.rcv_queue = asyncio.Queue()    # received packets for Behave

    def connection_made(self, transport):
        '''Base protcol: Called when a connection is made.'''
        logging.info('connection_made')
        self.transport = transport

    def connection_lost(self, exc):             # pylint: disable=W0613
        '''Base protcol: Called when a connection is lost or closed.'''
        logging.info('connection_lost')
        self.on_con_lost.set_result(True)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        logging.info('datagram_received')
        self.recvd_pkts.append(data.decode())
        self.rcv_queue.put_nowait(data.decode())

    def sendto(self, sip_msg: sipmsg.SipMessage):
        '''Send SIP message to UAS.'''
        logging.info('sendto')
        self.sent_msgs.append(sip_msg)
        self.transport.sendto(str(sip_msg).encode())

    def error_received(self, exc):              # pylint: disable-msg=R0201,W0613
        '''Datagram protcol: Called when an error is received.'''
        logging.info('error_received')

class AutoReply(SipPhoneUdpClient):
    '''
    Automatically reply with OK, such as INFO, NOTIFY, OPTIONS and UPDATE.
    '''
    def __init__(self, on_con_lost):
        super().__init__(on_con_lost)
        self.auto_reply = ['INFO', 'NOTIFY', 'OPTIONS', 'UPDATE']

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        sip_msg = data.decode()
        self.recvd_pkts.append(sip_msg)
        sip_method = sip_msg.split(maxsplit=1)[0]
        logging.info('datagram_received: %s', sip_method)
        if sip_method in self.auto_reply:
            logging.info('datagram_received: auto reply to %s', sip_method)
            logging.debug('datagram_received: %s', sip_msg)
            response = sipmsg.Response(status_code=200, reason_phrase='OK')
            response.method = sip_method
            response.init_from_msg(sip_msg)
            response.sort()
            self.sendto(response)
        else:
            self.rcv_queue.put_nowait(sip_msg)
