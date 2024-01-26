# vi: ai ts=4 sw=4 et
'''
Behave steps to for Feature: Registration, RFC 3665, Section 2
'''

from asyncio import sleep
import copy
import logging
from behave import given, when, then # pylint: disable=E0611
from behave.api.async_step import async_run_until_complete
from assertpy import assert_that

# pylint: disable=E0401,C0413,C0116,E0102

import pysiptest.headerfield as hf
from pysiptest import sipmsg
from pysiptest.support import sip_register

def get_digest_auth(sip_digest_auth, challenge:str, request_method:str, userinfo:dict, uri:str=None):
    '''Create response to challenge WWW-Authenticate or Proxy-Authenticate.

    :param challenge: Challenge value from *-Authenticate
    :param request: Request method issuing challenge
    :param userinfo: User info from environment.py
    :param uri: Destination URI
    :return Authorization: Completed Authorization header
    '''
    assert isinstance(challenge, str)
    assert isinstance(request_method, str)
    assert isinstance(userinfo, dict)

    if uri is None:
        uri = f'sip:{userinfo["domain"]}'
    sip_digest_auth.parse_challenge(challenge)
    return sip_digest_auth.get_auth_digest(request_method, uri,
        userinfo['extension'], userinfo['password'])

@given('new connection with user "{user_name}" and server "{server_name}"')
@async_run_until_complete
async def step_dispatch_async_call(context, user_name, server_name): # pylint: disable=W0613
    assert_that(context.test_servers).contains_key(server_name)
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
        logging.info('sends request REGISTER: creating pending_msg')
        context.pending_msg = sip_register(
            context.sip_xport[user_name][1].local_addr,
            context.test_users[user_name])
        context.pending_msg.field('Contact').value = context.pending_msg.field('From').value

@then('"{user_name}" receives response "{codes}"')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name, codes): # pylint: disable=W0613
    if context.pending_msg is not None:
        context.sip_xport[user_name][1].sendto(context.pending_msg)
        context.pending_msg = None

    sip_msg = await context.sip_xport[user_name][1].rcv_queue.get()

    # pylint: disable=C0209
    assert_that(sipmsg.Response.get_code(sip_msg))\
        .described_as('%s response %s'
        % (user_name, sip_msg.split(maxsplit=1)[0]))\
        .is_not_none()
    assert_that(codes).described_as('response').contains(sipmsg.Response.get_code(sip_msg))
    context.pending_msg = copy.deepcopy(
        context.sip_xport[user_name][1].sent_msgs[-1])

@when('with header field "{field_name}" value "{field_value}"')
def step(context, field_name, field_value): # pylint: disable=W0613
    assert context.pending_msg is not None
    field_name = field_name.replace('-', '_')
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
    contact_field.contact_params[contact_addr]['expires'] = '0'

@when('with header field Authorization for "{user_name}"')
def step(context, user_name):
    assert context.pending_msg is not None
    assert len(context.sip_xport[user_name][1].recvd_pkts) > 0
    sip_dict = hf.msg2fields(context.sip_xport[user_name][1].recvd_pkts[-1])
    assert 'WWW-Authenticate' in sip_dict.keys()
    www_authenticate = sip_dict['WWW-Authenticate']
    sip_request = sip_dict['CSeq'].split()[-1] # Request name is in CSeq
    context.pending_msg.hdr_fields.append(
        hf.Authorization(value=\
            get_digest_auth(context.test_users[user_name]['digestauth'],
            www_authenticate, sip_request, context.test_users[user_name])))

    # New transaction, increment CSeq
    context.pending_msg.field('CSeq').value += 1
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
    fields = hf.msg2fields(context.sip_xport[user_name][1].recvd_pkts[-1])
    assert_that(fields).contains(field_name)
    assert_that(fields[field_name]).contains(field_value)

@then('"{user_name}" response does not contain field "{header_field}"')
def step(context, user_name, header_field): # pylint: disable=W0613
    fields = hf.msg2fields(context.sip_xport[user_name][1].recvd_pkts[-1])
    assert_that(fields).does_not_contain(header_field)

@when('"{user_name}" Contact field port is set to {portnum}')
def step(context, user_name, portnum):
    assert context.invite_msg is not None
    extension = context.test_users[user_name]["extension"]
    addr = context.sip_xport[user_name][1].local_addr
    context.invite_msg.field('Contact').from_string(
        f'<sip:{extension}@{addr[0]}:{portnum}>')

@then('"{user_name}" receives "{method}"')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name, method):
    # Wait BYE
    req_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    method = sipmsg.Request.get_method(req_msg)
    assert_that(method).described_as('request').is_equal_to('BYE')

    # Send OK
    response = sipmsg.Response(status_code=200, reason_phrase='OK')
    response.method = method
    response.init_from_msg(req_msg)
    response.sort()
    context.sip_xport[user_name][1].sendto(response)
    assert_that(context.sip_xport[user_name][1].in_a_call).is_false()

@then('pause for {pause} seconds')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, pause):
    await sleep(int(pause))
