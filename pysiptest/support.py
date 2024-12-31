# vi: ai ts=4 sw=4 et
# pylint: disable=E0401,C0413,C0116,E0102,R0913,R0917
'''
Functions to support steps Feature: Registration, RFC 3665, Section 2
'''

#import logging
import fcntl
import os
import random
import socket
import struct
import subprocess

import pysiptest.headerfield as hf
from pysiptest import sipmsg

def sip_sdp(username, sockname=None) -> str:
    '''Create SDP info, RFC 4566, Obsoletes: 2327, 3266

    :param owner: Domain, extension, user name, or manufacturer
    :param sockname: Tuple returned by getsockname()
    :return str:'''

    assert sockname is not None
    assert isinstance(sockname, tuple)
    ipaddr = sockname[0]
    audio_port = sockname[1]
    random.seed()
    # <username> is the user's login on the originating host, or it is "-"
    session_id = random.randint(32768, 65535) # Unique
    version = 0 # "This memo defines version 0."
    # <nettype> : network
    # <addrtype> : network
    # <unicast-address> : sockname

    return f'''v=0
o={username} {session_id} {version} IN IP4 {ipaddr}
s=test SDP stream
c=IN IP4 {ipaddr}
t=0 0
m=audio {audio_port} RTP/AVP 0 9 101
a=rtpmap:0 PCMU/8000
a=rtpmap:9 G722/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-15
a=sendrecv
'''.replace('\n', '\r\n')

def insert_behave_fields(behave_fields, sip_msg):
    '''Insert headers from Behave tests into message, where valid.'''
    assert isinstance(behave_fields, dict)
    if behave_fields:
        for hfk, hfv in behave_fields.items():
            sip_msg.add_set_valid_field(hfk, hfv)

def sip_register(sock_addr:tuple, userinfo:dict, expires:int=60,
        header_fields=None, transport='UDP') -> sipmsg.SipMessage:
    '''Provide default values for REGISTER request.'''
    assert isinstance(sock_addr, tuple)
    assert isinstance(userinfo, dict)
    assert isinstance(expires, int)

    register = sipmsg.Register()
    register.request_uri = f'sip:{userinfo["domain"]}'
    register.init_mandatory()
    register.field('CSeq').method = register.method
    register.field('CSeq').value = int.from_bytes(os.urandom(2), 'little')
    register.field('To').from_string(f'{userinfo["name"]} <{userinfo["sipuri"]}>')
    register.field('From').from_string(f'{userinfo["name"]} <{userinfo["sipuri"]}>')
    register.field('Via').via_params['transport'] = transport
    register.field('Via').via_params['address'] = f'{sock_addr[0]}'
    register.add_set_valid_field('Contact',
        f'<sip:{userinfo["extension"]}@{sock_addr[0]}:{sock_addr[1]};transport={transport}>')
    register.add_set_valid_field('Expires', expires)
    register.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    insert_behave_fields(header_fields, register)
    register.sort()
    return register

def sip_invite(sock_addr:tuple, caller_info:hash, receiver_info:hash,
        rtp_socket:tuple, request_uri:str=None, header_fields=None, transport='UDP') \
        -> sipmsg.SipMessage:
    '''Create INVITE for call

    :param sock_addr: Local SIP socket address
    :param caller_info: Caller information, from context
    :param receiver_info: Receiver information, from context
    :param rtp_socket: Local RTP socket address
    :param request_uri: Receiver SIP URI, optional
    '''
    assert isinstance(sock_addr, tuple)
    assert isinstance(caller_info, dict)
    assert isinstance(receiver_info, dict)
    assert isinstance(rtp_socket, tuple)
    invite = sipmsg.Invite()
    invite.request_uri = request_uri if request_uri is not None else \
            f'{receiver_info["sipuri"]}'
    invite.init_mandatory()
    invite.field('CSeq').method = invite.method
    invite.field('CSeq').value = int.from_bytes(os.urandom(2), 'little')
    invite.add_set_valid_field('Content_Type', 'application/sdp')
    invite.add_set_valid_field('Accept', 'application/sdp')
    invite.add_set_valid_field('Allow_Events', 'presence,dialog,message-summary,refer')
    invite.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')

    invite.field('From').from_string(
        f'{caller_info["name"]} <{caller_info["sipuri"]}>')
    invite.field('To').from_string(
        f'{receiver_info["name"]} <{receiver_info["sipuri"]}>')
    invite.field('Via').via_params['transport'] = transport
    invite.field('Via').via_params['address'] = f'{sock_addr[0]}'

    invite.body = sip_sdp(caller_info['name'], rtp_socket)
    insert_behave_fields(header_fields, invite)
    invite.sort()
    return invite

def sip_ack(sdp_msg:str, userinfo:dict, addr:tuple, req_uri=None, \
        header_fields=None, transport='UDP') \
        -> sipmsg.SipMessage:
    '''Create ACK message'''
    assert isinstance(sdp_msg, str)
    assert isinstance(userinfo, dict)
    assert isinstance(addr, tuple)

    if req_uri is None:
        req_uri = userinfo['sipuri']
    ack = sipmsg.Ack(request_uri=req_uri)
    ack.init_from_msg(sdp_msg)
    ack.add_set_valid_field('Contact',
        f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]};transport={transport}>')
    ack.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    ack.add_set_valid_field('Allow_Events', 'presence,dialog,message-summary,refer')
    ack.field('Via').via_params['transport'] = transport
    ack.field('CSeq').method = 'ACK'
    insert_behave_fields(header_fields, ack)
    ack.sort()
    return ack

def sip_bye(sdp_msg:str, userinfo:dict, addr:tuple, contact:str=None,
        header_fields=None, transport='UDP') -> sipmsg.SipMessage:
    '''Create BYE message

    :param sdp_msg: SDP message starting the call.
    :param contact: SIP contact address for message
    :param userinfo: User information from test environment.
    :param addr: Socket address.'''
    assert isinstance(sdp_msg, str)
    assert isinstance(userinfo, dict)
    assert isinstance(addr, tuple)

    sdp_dict = hf.msg2fields(sdp_msg)
    if contact is None:
        contact = sdp_dict['Contact'].strip('<>').split(';')[0]
    bye = sipmsg.Bye(request_uri=contact)
    bye.init_mandatory()
    bye.field('Via').via_params['transport'] = transport
    bye.field('Via').via_params['address'] = f'{addr[0]}'
    bye.field('From').from_string(sdp_dict['From'])
    bye.field('To').from_string(sdp_dict['To'])
    bye.add_set_valid_field('Contact',
        f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]};transport={transport}>')
    bye.field('CSeq').from_string(sdp_dict['CSeq'])
    bye.field('CSeq').value += 1
    bye.field('CSeq').method = bye.method
    bye.field('Call_ID').value = sdp_dict['Call-ID']
    bye.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    insert_behave_fields(header_fields, bye)
    bye.sort()
    return bye

def sip_options(userinfo:dict, svr_addr:tuple, local_addr:tuple,
    header_fields=None, transport='UDP') -> sipmsg.SipMessage:
    '''Create OPTIONS request message for keep-alive, outside of dialog.

    :param userinfo: User information from test environment.
    :param svr_addr: Socket address.
    :param local_addr: Socket address.
    '''
    assert isinstance(userinfo, dict)
    assert isinstance(svr_addr, tuple)

    options = sipmsg.Options(
        request_uri=f'sip:{userinfo["extension"]}@{svr_addr[0]}:{svr_addr[1]}',
        transport=transport)
    options.init_mandatory()
    options.field('Via').via_params['transport'] = transport
    if local_addr[0]:
        options.field('Via').via_params['address'] = f'{local_addr[0]}'
    options.field('CSeq').method = options.method
    options.field('From').from_string(f'{userinfo["name"]} <{userinfo["sipuri"]}>')
    options.field('To').from_string(f'{userinfo["name"]} <{userinfo["sipuri"]}>')
    options.add_set_valid_field('Contact',
        f'<sip:{userinfo["extension"]}@{local_addr[0]}:{local_addr[1]};transport={transport}>')
    #options.add_set_valid_field('Allow',
    #    'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    insert_behave_fields(header_fields, options)
    options.sort()
    return options

def sip_refer(from_user:dict, to_user:str,
        sockname:tuple, refer_to:str, request_uri:str,
        header_fields=None, transport='UDP') -> sipmsg.SipMessage:
    '''Create REFER request. RFC 3515. REFER handled same as BYE.

    :param from_user: Context test_user
    :param to_user: string
    :param sockname: Local SIP socket address tuple
    :param refer_to: Section 2.1, examples governed by SIP msg flow.
    :param request_uri: May be address of UC, or To: URI address.
    '''
    # Fanvil:
    # <sip:1002@teo?
    #      Replaces=230711715225292-215582680159797@192.168.0.196:
    #      to-tag=06HUU31Sa1e7c:
    #      from-tag=1970457965>
    # <sip:Dest@Realm?Replaces=NewCallID@UAC_IP:to-tag=NewTag:from-tag=NewTag>
    # Then URI encode Replaces= data
    assert isinstance(from_user, dict)
    assert isinstance(to_user, str)
    assert isinstance(sockname, tuple)
    assert isinstance(refer_to, str)
    assert isinstance(request_uri, str)

    refer = sipmsg.Refer(request_uri=request_uri, transport=transport)
    refer.init_mandatory()
    refer.field('Via').via_params['transport'] = refer.transport
    refer.field('Via').via_params['address'] = f'{sockname[0]}'
    refer.field('From').from_string(
        f'{from_user["name"]} <{from_user["sipuri"]}>')
    refer.field('To').from_string(
        f'{to_user["name"]} <{to_user["sipuri"]}>')
    refer.field('Contact').from_string(
        f'<sip:{from_user["extension"]}@{sockname[0]}:{sockname[1]};transport={transport}>')
    refer.field('CSeq').method = refer.method
    refer.field('Refer_To').value = refer_to
    refer.field('Referred_By').value = \
        str(refer.field('Contact')).split(maxsplit=1)[-1]
    refer.add_set_valid_field('Event', 'refer')
    refer.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    insert_behave_fields(header_fields, refer)
    refer.sort()
    return refer

# pylint: disable=R0913
def sip_subscribe(from_user:dict, to_sipuri:str, request_uri:str,
        sockname:tuple, event:str, accept:str, supported:str=None, expires:int=300, \
        call_id:str=None, header_fields=None, transport='UDP'):
    '''Create SUBSCRIBE request

    :param from_user: User URI generating request.
    :param to_sipuri: The endpoint generating events.
    :param request_uri: May be address of UC, or To: URI address.
    :param sockname: UDP sockname value
    :param event: Subscribed event, such as presence, message-summary, etc.
    :param accept: Accept field
    :param supported: Supported field
    :param expires: Expires field'''
    assert isinstance(from_user, dict)
    assert isinstance(to_sipuri, str)
    assert isinstance(sockname, tuple)
    assert isinstance(event, str)
    assert isinstance(accept, str)
    assert isinstance(request_uri, str)
    if supported is not None:
        assert isinstance(supported, str)
    if expires is not None:
        assert isinstance(expires, int)

    subscribe = sipmsg.Subscribe(request_uri=request_uri, transport=transport)
    subscribe.init_mandatory()

    subscribe.field('Via').via_params['transport'] = subscribe.transport
    subscribe.field('Via').via_params['address'] = f'{sockname[0]}'
    subscribe.field('From').from_string(f'<{from_user["sipuri"]}>')
    subscribe.field('To').from_string(f'<{to_sipuri}>')
    subscribe.field('Contact').from_string(
        f'<sip:{from_user["extension"]}@{sockname[0]}:{sockname[1]};transport={transport}>')
    subscribe.field('CSeq').method = subscribe.method
    if call_id:
        subscribe.field('Call_ID').value = call_id
    subscribe.field('Event').value = event
    if supported is not None:
        subscribe.add_set_valid_field('Supported', supported)
    subscribe.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    subscribe.add_set_valid_field('Supported', 'eventlist, replaces, callerid')
    subscribe.add_set_valid_field('Expires', expires)
    insert_behave_fields(header_fields, subscribe)
    subscribe.sort()
    return subscribe

def sip_publish(from_user:dict, request_uri:str, sockname:tuple,
        event:str, accept:str=None, supported:str=None, expires:int=None, \
        header_fields=None, transport='UDP'):
    '''Create PUBLISH request, RFC 3903.
    Need to track SIP-ETag returned in 2xx response.
    Initial request does not contain SIP-If-Match. Subsequent event updates
    MUST contain SIP-If-Match from previous response to update event.

    :param from_user: User URI generating request.
    :param request_uri: May be address of UC, or To: URI address.
    :param sockname: UDP sockname value
    :param event: Subscribed event, such as presence, message-summary, etc.
    :param accept: Accept field
    :param supported: Supported field
    :param expires: Expires field'''
    assert isinstance(from_user, dict)
    assert isinstance(request_uri, str)
    assert isinstance(sockname, tuple)
    assert isinstance(event, str)
    if accept is not None:
        assert isinstance(accept, str)
    if supported is not None:
        assert isinstance(supported, str)
    if expires is not None:
        assert isinstance(expires, int)

    publish = sipmsg.Publish(request_uri=request_uri, transport=transport)
    publish.init_mandatory()

    publish.field('Via').via_params['transport'] = publish.transport
    publish.field('Via').via_params['address'] = f'{sockname[0]}'
    publish.field('From').from_string(f'<{from_user["sipuri"]}>')
    publish.field('To').from_string(f'<{from_user["sipuri"]}>')
    publish.field('CSeq').method = publish.method
    publish.field('Event').value = event
    if accept is not None:
        publish.add_set_valid_field('Accept', accept)
    if supported is not None:
        publish.add_set_valid_field('Supported', supported)
    publish.add_set_valid_field('Allow',
        'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE')
    publish.add_set_valid_field('Supported', 'eventlist, replaces, callerid')
    if expires is not None:
        publish.add_set_valid_field('Expires', expires)
    publish.add_set_valid_field('Content_Type', 'application/pidf+xml')
    insert_behave_fields(header_fields, publish)
    publish.sort()
    return publish

# from socket.h
AF_INET = 2
SIOCGIFADDR	= 0x8915

def get_ip(if_name):
    '''Get the IP address for an interface name.'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    ifreq = struct.pack('16sH14s', if_name.encode(), AF_INET, b'\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except IOError:
        return None
    ip = struct.unpack('15sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

def available_ips():
    '''Get the available IPs for all non-loopback interfaces.'''
    return [if_ip
        for if_ip in [get_ip(ifname[1])
            for ifname in socket.if_nameindex() if not ifname[1] == 'lo']
        if if_ip]

def get_stun_address(server='stun.freeswitch.org'):
    '''Get the external IP address based on stun. Requires stun utility.'''
    stun_out = subprocess\
        .run(f'stun {server} 1 -v', shell=True, capture_output=True, check=False)\
        .stderr.decode('ASCII')\
        .splitlines()
    mapped = [s for s in stun_out if 'MappedAddress' in s]
    return mapped[-1].split()[-1].split(':')[0]
