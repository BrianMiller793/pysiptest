# vi: ai ts=4 sw=4 et
'''
Functions to support steps Feature: Registration, RFC 3665, Section 2
'''

import os
import sys

# pylint: disable=E0401,C0413,C0116,E0102
sys.path.append(os.getenv('PYSIP_LIB_PATH'))

from digestauth import SipDigestAuth
import headerfield as hf
import sipmsg

def digest_auth(challenge:str, request_method:str, userinfo:dict, uri:str=None):
    '''Create response to challenge WWW-Authenticate or Proxy-Authenticate.

    :param challenge: Challenge value from *-Authenticate
    :param request: Request method issuing challenge
    :param userinfo: User info from environment.py
    :param uri: Destination URI
    :return Authorization: Completed Authorization header
    '''
    if uri is None:
        uri = f'sip:{userinfo["domain"]}'
    sda = SipDigestAuth() # Create digest authentication
    sda.parse_challenge(challenge)
    return sda.get_auth_digest(request_method, uri,
        userinfo['extension'], userinfo['password'])

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

def sip_register(context, userinfo, expires=60) -> sipmsg.SipMessage :
    '''Provide default values for REGISTER request.'''
    register = sipmsg.Register()
    register.request_uri = f'sip:{userinfo["domain"]}'
    register.init_mandatory()
    register.field('CSeq').method = register.method
    register.field('CSeq').value = int.from_bytes(os.urandom(2), 'little')
    register.hdr_fields.append(hf.User_Agent(
        value='pysip/123456_DEADBEEFCAFE'))
    register.field('To').value = f'{userinfo["name"]} <{userinfo["sipuri"]}>'
    register.field('From').value = f'{userinfo["name"]} <{userinfo["sipuri"]}>'
    register.field('Via').via_params['transport'] = 'UDP'
    addr = context.sip_xport[userinfo['name']][0]._sock.getsockname() # pylint: disable=W0212
    register.field('Via').via_params['address'] = f'{addr[0]}:{addr[1]}'
    register.hdr_fields.append(hf.Contact(
        value=f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]}>'))
    register.hdr_fields.append(hf.Expires(value=expires))
    register.sort()
    return register

def sip_invite(context, caller_info, receiver_info, rtp_socket, request_uri:str=None) -> sipmsg.SipMessage :
    '''Create INVITE for call'''
    invite = sipmsg.Invite()
    invite.request_uri = request_uri if request_uri is not None else \
            f'{receiver_info["sipuri"]}'
    invite.init_mandatory()
    invite.field('CSeq').method = invite.method
    invite.field('CSeq').value = int.from_bytes(os.urandom(2), 'little')
    invite.hdr_fields.append(hf.Content_Type(value='application/sdp'))
    invite.hdr_fields.append(hf.Content_Disposition(value='session'))
    invite.hdr_fields.append(hf.User_Agent(
        value='pysip/123456_DEADBEEFCAFE'))
    invite.field('From').value = \
        f'{caller_info["name"]} <{caller_info["sipuri"]}>'
    invite.field('To').value = \
        f'{receiver_info["name"]} <{receiver_info["sipuri"]}>'
    invite.field('Via').via_params['transport'] = 'UDP'
    sockname = context.sip_xport[caller_info['name']][0]._sock.getsockname() # pylint: disable=W0212
    invite.field('Via').via_params['address'] = f'{sockname[0]}:{sockname[1]}'
    invite.field('Supported').value = 'timer, precondition, path, replaces'
    invite.body = sip_sdp(caller_info['name'], rtp_socket)
    invite.sort()
    return invite

def sip_ack(sdp_msg:str, userinfo:dict, addr:tuple) -> sipmsg.SipMessage:
    '''Create ACK message'''
    ack = sipmsg.Ack(request_uri=userinfo['sipuri'])

    ack.init_from_msg(sdp_msg)
    ack.hdr_fields.append(hf.Contact(
        value=f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]}>'))
    ack.field('CSeq').method = 'ACK'
    ack.sort()
    return ack

def sip_bye(sdp_msg:str, userinfo:dict, addr:tuple, contact:str=None) -> sipmsg.SipMessage:
    '''Create BYE message

    :param sdp_msg: SDP message starting the call.
    :param contact: SIP contact address for message
    :param userinfo: User information from test environment.
    :param addr: Socket address.'''
    sdp_dict = hf.msg2fields(sdp_msg)
    if contact is None:
        contact = sdp_dict['Contact'].strip('<>').split(';')[0]
    bye = sipmsg.Bye(request_uri=contact)
    bye.init_mandatory()
    bye.field('Via').via_params['transport'] = 'UDP'
    bye.field('Via').via_params['address'] = f'{addr[0]}:{addr[1]}'
    bye.field('From').from_string(sdp_dict['From'])
    bye.field('To').from_string(sdp_dict['To'])
    bye.hdr_fields.append(hf.Contact(
        value=f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]}>'))
    bye.field('CSeq').from_string(sdp_dict['CSeq'])
    bye.field('CSeq').value += 1
    bye.field('CSeq').method = bye.method
    bye.field('Call_ID').value = sdp_dict['Call-ID']
    bye.sort()
    return bye

def sip_options(userinfo:dict, addr:tuple) -> sipmsg.SipMessage:
    '''Create OPTIONS request message for keep-alive, outside of dialog.

    :param userinfo: User information from test environment.
    :param addr: Socket address.
    '''
    addr_contact = f'<sip:{userinfo["extension"]}@{addr[0]}:{addr[1]}>'
    options = sipmsg.Options(request_uri=addr_contact, transport='UDP')
    options.init_mandatory()
    options.field('Via').via_params['transport'] = 'UDP'
    options.field('Via').via_params['address'] = f'{addr[0]}:{addr[1]}'
    options.field('CSeq').method = options.method
    options.field('From').value = f'{userinfo["name"]} <{userinfo["sipuri"]}>'
    options.field('To').value = f'{userinfo["name"]} <{userinfo["sipuri"]}>'
    options.hdr_fields.append(hf.Contact(value=addr_contact))
    options.sort()
    return options
