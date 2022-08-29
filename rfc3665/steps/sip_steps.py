# vi: ai ts=4 sw=4 et
'''
Behave steps to support Feature: Registration, RFC 3665, Section 2
'''

import copy
import logging
import os
import sys
from behave import given, when, then # pylint: disable=E0611
from behave.api.async_step import async_run_until_complete
import hamcrest as hc

# pylint: disable=E0401,C0413,C0116,E0102
sys.path.append(os.getenv('PYSIP_LIB_PATH'))

from digestauth import SipDigestAuth
import headerfield as hf
import sipmsg

#from sipphone import SipPhoneUdpClient

def sip_register(context, userinfo, expires=60) -> sipmsg.SipMessage :
    '''Provide default values for REGISTER request.'''
    register = sipmsg.Register()
    register.request_uri = 'sip:teo'
    register.cseq = int.from_bytes(os.urandom(2), 'little')
    register.init_mandatory()
    register.hdr_fields.append(hf.User_Agent(
        oldvalue='Teo 9102/2.2.0.3727_DEADBEEFCAFE'))
        #oldvalue='Teo 9102/2.2.0.3727_' + os.urandom(6).hex()))
    register.field('To').value = f'{userinfo[0]} <sip:{userinfo[1]}>'
    register.field('From').value = f'{userinfo[0]} <sip:{userinfo[1]}@teo>'
    register.field('Via').via_params['transport'] = 'UDP'
    addr = context.sip_xport[0]._sock.getsockname() # pylint: disable=W0212
    register.field('Via').via_params['address'] = f'{addr[0]}:{addr[1]}'
    register.hdr_fields.append(hf.Contact(
        oldvalue=f'<sip:{userinfo[1]}@{addr[0]}:{addr[1]}>'))
    register.hdr_fields.append(hf.Expires(oldvalue=expires))
    register.sort()
    return register

def check_msg(context, expected_method, sip_msg) -> dict : # pylint: disable=W0613
    '''Answer incoming requests with OK response.'''
    sip_method = sip_msg.split(maxsplit=1)[0].split()[0]

    if sip_method != expected_method:
        logging.info('Sending automatic response for %s', sip_dict[-1].__str__())
        response = sipmsg.Response(status_code=200, reason_phrase='OK')
        response.method = sip_msg
        response.init_from_msg(sip_msg)
        context.sip_xport[1].sendto(response)
        return False

    return True

# TODO move to SipMessage or phone
def get_last_header(messages, hdr_name) -> hf.HeaderField:
    for m in messages:
        for hv in m.hdr_fields:
            if hdr_name == hv._longname:
                return copy.deepcopy(hv)
    return None

@given('new connection with user "{user_name}" and server "{server_name}"')
@async_run_until_complete
async def step_dispatch_async_call(context, user_name, server_name): # pylint: disable=W0613
    assert server_name in context.test_servers.keys()
    assert hasattr(context, 'sip_xport')
    context.pending_msg = None
    logging.info('step_dispatch_async_call address=%s', context.test_servers[server_name][0])

@given('existing connection with user "{user_name}" and server "{server_name}"')
def step(context, user_name, server_name): # pylint: disable=W0613
    assert hasattr(context, 'sip_xport')

@when('"{user_name}" sends request REGISTER')
def step(context, user_name):
    # The 'sends' steps never send a packet, only put it in 'pending'
    if hasattr(context, 'pending_msg') is False or context.pending_msg is None:
        context.pending_msg = sip_register(
            context, context.test_users[user_name])

@then('"{user_name}" receives response "{codes}"')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name, codes): # pylint: disable=W0613
    if context.pending_msg is not None:
        print(str(context.pending_msg))
        context.sip_xport[1].sendto(context.pending_msg)
        context.pending_msg = None

    is_msg_rcvd = False
    wait_for = 'SIP/2.0'
    while is_msg_rcvd == False:
        logging.info('Waiting for %s', wait_for)
        sip_msg = await context.sip_xport[1].rcv_queue.get()
        print(sip_msg)
        is_msg_rcvd = check_msg(context, wait_for, sip_msg)

    # TODO Generalize for request/response
    sip_dict = hf.msg2fields(sip_msg)
    assert 'SIP/2.0' in sip_dict.keys() # Response starts with
    assert sip_dict['SIP/2.0'].split(' ', 1)[0] in codes
    context.pending_msg = copy.deepcopy(context.sip_xport[1].sent_msgs[-1])

@when('with header field "{field_name}" value "{field_value}"')
def step(context, field_name, field_value): # pylint: disable=W0613
    assert context.pending_msg is not None
    field = context.pending_msg.field(field_name)
    if field is None:
        field = hf.by_name(field_name)() # by_name returns class
        context.pending_msg.hdr_fields.append(field)
    context.pending_msg.field(field_name).from_string(field_value)

@when('with Contact field expires 0')
def step(context):
    assert context.pending_msg is not None
    contact_field = context.pending_msg.field('Contact')
    assert contact_field is not None
    contact_addr = next(iter(contact_field.contact_params))
    contact_field.contact_params[contact_addr].append(('expires', '0'))

@when('with header field Authorization for "{user_name}"')
def step(context, user_name):
    assert context.pending_msg is not None
    assert len(context.sip_xport[1].recvd_pkts) > 0
    sip_dict = hf.msg2fields(context.sip_xport[1].recvd_pkts[-1])
    assert 'WWW-Authenticate' in sip_dict.keys()
    www_authenticate = sip_dict['WWW-Authenticate']
    sda = SipDigestAuth() # Create digest authentication
    sda.parse_challenge(www_authenticate)
    authorization_value = sda.get_auth_digest(
        'REGISTER',
        'sip:teo', # registration URI
        context.test_users[user_name][1], # user name
        context.test_users[user_name][2]) # user password
    context.pending_msg.hdr_fields.append(
        hf.Authorization(oldvalue=authorization_value))
    # New transaction, increment CSeq
    context.pending_msg.cseq += 1
    context.pending_msg.sort()

@when('without header field "{header_field}"')
def step(context, header_field): # pylint: disable=W0613
    assert context.pending_msg is not None
    field = context.pending_msg.field(header_field)
    if field is not None:
        context.pending_msg.hdr_fields.remove(field)

@then('"{user_name}" is registered at the server')
def step(context, user_name): # pylint: disable=W0613
    pass

@then('"{user_name}" is unregistered')
def step(context, user_name): # pylint: disable=W0613
    pass

@then('"{user_name}" response contains "{field_name}" field, value "{field_value}"')
def step(context, user_name, field_name, field_value): # pylint: disable=W0613
    fields = hf.msg2fields(context.sip_xport[1].recvd_pkts[-1])
    hc.assert_that(fields.keys(), hc.has_item(field_name))
    hc.assert_that(fields[field_name], hc.contains_string(field_value))

@then('"{user_name}" response does not contain field "{header_field}"')
def step(context, user_name, header_field): # pylint: disable=W0613
    fields = hf.msg2fields(context.sip_xport[1].recvd_pkts[-1])
    hc.assert_that(header_field not in fields.keys(),
        'Found %s in headers: %s' % (header_field, str(fields.keys())))
