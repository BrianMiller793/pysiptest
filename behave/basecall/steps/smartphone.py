# vi: ai ts=4 sw=4 et

import asyncio
import logging

class SmartPhone():
    ''' Emulate functionality of a smart phone. '''
    def __init__(self, ip='127.0.0.1', port=9999, user_agent='Python SIP test agent'):
        self.active_calls = []
        self.user_agent = user_agent
        self.transport = None
        self.protocol = None

    def dial(self):
        self.transport.sendto('dial'.encode())
        logging.info("dial")

    def answer(self):
        self.transport.sendto('answer'.encode())
        logging.info("answer")

    def hangup(self):
        self.transport.sendto('hangup'.encode())
        logging.info("hangup")

    def register(self):
        self.transport.sendto('register'.encode())
        logging.info("register")

    def request(self):
        '''Make a request to the other endpoint'''
        logging.info("request")

    def response_handler(self):
        '''Respond to a received request'''
        logging.info("response_handler")

class UdpSip(SmartPhone):
    '''SIP connection handler for UDP'''
    # to send: instance.transport.sendto(msg.encode())
    def __init__(self, on_con_lost):
        '''Initialize the instance'''
        self.transport = None
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        '''Event handler for initial connection.'''
        self.transport = transport
        logging.info("connected")

    def datagram_received(self, data, addr):
        '''Event handler for receiving a datagram'''
        message = data.decode()
        logging.info(message)
        # The following is from the ECHO demo code
        #self.transport.sendto(data, addr)

    def error_received(self, exc):
        '''Event handler for receiving an error'''
        logging.info("error_received")

    def connection_lost(self, exc):
        '''Event handler for losing the connection'''
        self.on_con_lost.set_result(True)
        logging.info("disconnected")
