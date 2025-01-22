# vim: ts=4 sw=4 et ai
'''
FreeSWITCH event socket 
'''

import asyncio
import logging
import os

logger = logging.getLogger()

class EventSocket:
    '''Connection factory for FreeSWITCH event socket.'''
    def __init__(self):
        self.password = os.environ.get('FSES_PASSWORD', 'ClueCon')
        self.transport = None
        self.messages = asyncio.Queue()

    def begin(self):
        '''Start event socket, log in and start initial events'''
        logger.debug('EventSocket:begin()')

    def end(self):
        '''Shut down connection'''
        logger.debug('EventSocket:end()')
        self.transport.close()

    # Factory methods:
    def connection_made(self, transport):
        '''Base transport'''
        logger.debug('EventSocket:connection_made()')
        self.transport = transport

    def connection_lost(self, exc):
        '''Base transport'''
        logger.debug('EventSocket:connection_lost(), %s', exc)

    def data_received(self, data):
        '''Handler for incoming chunked data'''
        strdata = data.decode('ASCII')
        logger.debug('EventSocket:data_received()=%s', strdata)
        self.messages.put_nowait(strdata)

    def eof_received(self):
        '''Handler for final data, connection will be closed'''
        logger.debug('EventSocket:eof_received()')

    def write(self, data):
        '''Event socket write, adds double new-line'''
        logger.debug('EventSocket:write(), data=%s', data)
        xmit_data = (data + '\n\n').encode('ASCII')
        self.transport.write(xmit_data)
