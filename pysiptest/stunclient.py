'''Basic UDP STUN protocol handler. RFC 3849, RFC 5389, RFC 8489'''
# vim: set ts=4 sw=4 et ai:

from os import urandom
import asyncio
import struct

# Message header types
BINDING_REQUEST = 0x0001
BINDING_RESPONSE = 0x0101
BINDING_ERROR_RESPONSE = 0x0111
SHARED_SECRET_REQUEST = 0x0002
SHARED_SECRET_RESPONSE = 0x0102
SHARED_SECRET_ERROR_RESPONSE = 0x0112

# Message Attributes
MAPPED_ADDRESS = 0x0001
RESPONSE_ADDRESS = 0x0002 # RFC 5389: Reserved
CHANGE_REQUEST = 0x0003 # RFC 5389: Reserved
SOURCE_ADDRESS = 0x0004 # RFC 5389: Reserved
CHANGED_ADDRESS = 0x0005 # RFC 5389: Reserved
USERNAME = 0x0006
PASSWORD = 0x0007 # RFC 5389: Reserved
MESSAGE_INTEGRITY = 0x0008
ERROR_CODE = 0x0009
UNKNOWN_ATTRIBUTES = 0x000a
REFLECTED_FROM = 0x000b # RFC 5389: Reserved
# RFC 5389
REALM = 0x0014
NONCE = 0x0015
XOR_MAPPED_ADDRESS = 0x0020
SOFTWARE = 0x8022
ALTERNATE_SERVER = 0x8023
FINGERPRINT = 0x8028

CHANGE_IP = 0x0004
CHANGE_PORT = 0x0002

def to_tlv(dtype, data):
    '''Create a new TLV.'''
    return struct.pack(f'!HH{len(data)}s', dtype, len(data), data)

TL_LEN = 4
def from_tlv(data):
    '''Decode data from TLV to Type, Length, Value, and remaing data.'''
    type_len = struct.unpack('!HH', data[:TL_LEN])
    updata = data[TL_LEN:type_len[1]+TL_LEN]
    if len(data) <= type_len[1]+TL_LEN:
        return type_len[0], type_len[1], updata, None
    return type_len[0], type_len[1], updata, data[type_len[1]+TL_LEN:]

TID_LEN=16
def encode_request(header_type, msg_attr_type, msg_attr):
    '''Encode a new binding request.'''
    request_data = to_tlv(msg_attr_type, struct.pack('!I', msg_attr))
    transaction_id = urandom(TID_LEN)
    return struct.pack(
        f'!HH16s{len(request_data)}s',
        header_type,
        len(request_data),
        transaction_id,
        request_data), transaction_id

def header_to_string(hdr_type):
    '''Convert header value to text.'''
    match hdr_type:
        case 0x0001:
            text = 'Binding Request'
        case 0x0101:
            text = 'Binding Response'
        case 0x0111:
            text = 'Binding Error Response'
        case 0x0002:
            text = 'Shared Secret Request'
        case 0x0102:
            text = 'Shared Secret Response'
        case 0x0112:
            text = 'Shared Secret Error Response'
    return text

def msgattr_to_string(msgattr):
    '''Convert message attribute value to string.'''
    match msgattr:
        case 0x0001:
            text = 'MAPPED-ADDRESS'
        case 0x0002:
            text = 'RESPONSE-ADDRESS'
        case 0x0003:
            text = 'CHANGE-REQUEST'
        case 0x0004:
            text = 'SOURCE-ADDRESS'
        case 0x0005:
            text = 'CHANGED-ADDRESS'
        case 0x0006:
            text = 'USERNAME'
        case 0x0007:
            text = 'PASSWORD'
        case 0x0008:
            text = 'MESSAGE-INTEGRITY'
        case 0x0009:
            text = 'ERROR-CODE'
        case 0x000a:
            text = 'UNKNOWN-ATTRIBUTES'
        case 0x000b:
            text = 'REFLECTED-FROM'
        case 0x0014:
            text = 'REALM'
        case 0x0015:
            text = 'NONCE'
        case 0x0020:
            text = 'XOR-MAPPED-ADDRESS'
        case 0x8022:
            text = 'SOFTWARE'
        case 0x8023:
            text = 'ALTERNATE_SERVER'
        case 0x8028:
            text = 'FINGERPRINT'
        case _:
            text = 'NOT LISTED'
    return text

def decode_msgattr(msgattr, msgdata):
    '''Decode message attribute response.'''
    match msgattr:
        case 0x0001:
            rv = decode_addr(msgdata)
        case 0x0002:
            rv = decode_addr(msgattr)
        # CHANGE-REQUEST is only used by the client
        case 0x0003:
            rv = 'CHANGE-REQUEST'
        case 0x0004:
            rv = decode_addr(msgdata)
        case 0x0005:
            rv = decode_addr(msgdata)
        case 0x0006:
            rv = 'USERNAME'
        case 0x0007:
            rv = 'PASSWORD'
        case 0x0008:
            rv = 'MESSAGE-INTEGRITY'
        case 0x0009:
            rv = 'ERROR-CODE'
        case 0x000a:
            rv = 'UNKNOWN-ATTRIBUTES'
        case 0x000b:
            rv = decode_addr(msgdata)
        case 0x0014:
            rv = None
        case 0x0015:
            rv = None
        case 0x0020:
            rv = None
        case 0x8022:
            rv = msgdata.decode()
        case 0x8023:
            rv = None
        case 0x8028:
            rv = None
        case _:
            rv = None
    return rv

def decode_response(data):
    '''Decode response packet to tuple and remaining data.'''
    return struct.unpack('!HH16s', data[:20]), data[20:]

def decode_addr(data):
    '''Decode a STUN address to string.'''
    # Returns Family, socket name tuple
    chd = struct.unpack('!xBHBBBB', data)
    return chd[0], (f'{chd[2]}.{chd[3]}.{chd[4]}.{chd[5]}', chd[1])

class StunRfc3849Client():
    '''UDP protocol handlers for minimal RFC 3849 STUN.'''
    # RFC 3849, RFC 5389, RFC 8489
    # pylint: disable=R0902
    def __init__(self, loop, done):
        ''' Initialize transport '''
        self.loop = loop
        self.done = done
        self.unsent = asyncio.Queue()        # unset packets
        self.pending = {}       # pending requests
        self.responses = []     # response data
        self.transport = None
        self.local_address = None
        self.peer_address = None
        self.retry_at = None
        self.retry_interval = 0.040
        self.retry_count = 4

    def connection_made(self, transport):
        '''Handler for initial connection state.'''
        self.transport = transport
        self.local_address = transport.get_extra_info('socket').getsockname()
        self.peer_address = transport.get_extra_info('peername')
        self.start_requests()

        self.retry_at = self.loop.time() + self.retry_interval
        self.loop.call_at(self.retry_at, self.retry_sendto)

    def datagram_received(self, data, addr): # pylint: disable=W0613
        '''Handler for incoming UDP data.'''
        header, more_data = decode_response(data)
        if header[2] in self.pending:
            del self.pending[header[2]]
            self.responses.append(more_data)
        if not self.pending:
            try:
                self.done.set_result(True)
            except asyncio.InvalidStateError:
                pass

    def error_received(self, exc): # pylint: disable=W0613
        ''' Handler for socket error '''
        try:
            self.done.set_result(True)
        except asyncio.InvalidStateError:
            pass

    def connection_lost(self, exc): # pylint: disable=W0613
        ''' Handler for closing socket '''
        self.transport.close()

    ###############
    def start_requests(self):
        '''Start sending sequence of BINDING_REQUEST packets to server.'''
        for req_attrib in [0, CHANGE_IP, CHANGE_PORT]:
            binding_req, x_id = encode_request(BINDING_REQUEST, CHANGE_REQUEST, req_attrib)
            self.pending[x_id] = binding_req
            self.sendto(binding_req)

    def sendto(self, data):
        '''Send data at small interval to avoid DOS trigger'''
        if self.unsent.empty():
            delay = self.loop.time() + 0.01
            self.loop.call_at(delay, self.delayed_sendto)
        self.unsent.put_nowait(data)

    def delayed_sendto(self):
        '''Callback for delayed send'''
        if not self.unsent.empty():
            data = self.unsent.get_nowait()
            self.transport.sendto(data)
            delay = self.loop.time() + 0.01
            self.loop.call_at(delay, self.delayed_sendto)

    def retry_sendto(self):
        '''Retry at relatively large interval'''
        if self.pending and self.retry_count:
            for _,v in self.pending.items():
                self.sendto(v)
            self.retry_at += self.retry_interval
            self.loop.call_at(self.retry_at, self.retry_sendto)
            self.retry_count -= 1
        else:
            try:
                self.done.set_result(True)
            except asyncio.InvalidStateError:
                pass

async def _main_async():
    '''Asynchronous main test.'''
    loop = asyncio.get_running_loop()

    done = loop.create_future()
    #server = 'stun.freeswitch.org'
    server = 'stun1.l.google.com'

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: StunRfc3849Client(loop, done),
            remote_addr=(server, 3478))

    try:
        await done
    finally:
        transport.close()

    print(protocol.local_address)
    print(protocol.peer_address)
    print(len(protocol.responses))
    for resp in protocol.responses:
        _print_response_set(resp)

def _test_decode_response(response:bytes):
    ''' Decode full reponse packet '''
    header, data = decode_response(response)
    print(f'{header_to_string(header[0])}, {header[1]}, {header[2].hex()}')
    _print_response_set(data)

def _print_response_set(response):
    ''' Convert a data set in a response to text. '''
    attr_type, _, attr_data, next_attr = from_tlv(response)
    print(f'{msgattr_to_string(attr_type)} {decode_msgattr(attr_type, attr_data)}')
    while next_attr:
        attr_type, _, attr_data, next_attr = from_tlv(next_attr)
        print(f'{msgattr_to_string(attr_type)} {decode_msgattr(attr_type, attr_data)}')

if __name__ == "__main__":
    asyncio.run(_main_async())
