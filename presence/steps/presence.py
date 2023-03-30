'''Provide steps supporting call parking using REFER request method.'''
# vim: ts=4 sw=4 et ai

from asyncio import sleep
import copy
import logging
import os
import sys
from behave import given, then    # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context
from assertpy import assert_that

# pylint: disable=E0401,E0102,C0413
sys.path.append(os.getenv('PYSIP_LIB_PATH'))
from rtpecho import RtpEcho
from rtpplay import RtpPlay

import headerfield as hf
import sipmsg
import support

# pylint: disable=W0613,C0116

# REGISTER sip:teo SIP/2.0
# SIP/2.0 401 Unauthorized
# REGISTER sip:teo SIP/2.0
# SIP/2.0 200 OK
@given('"{name}" registers')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    user_protocol = context.sip_xport[name][1]
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_registration()
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

# INVITE sip:2001@teo SIP/2.0
# SIP/2.0 100 Trying
# SIP/2.0 407 Proxy Authentication Required
# ACK sip:2001@teo SIP/2.0
# INVITE sip:2001@teo SIP/2.0
# SIP/2.0 100 Trying
@then('"{caller}" calls "{receiver}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, caller, receiver):
    user_protocol = context.sip_xport[caller][1]

    # Create RTP playback endpoint
    _, protocol = await context.udp_transport.loop.create_datagram_endpoint(
        lambda: RtpPlay(on_con_lost=None,
            file_name='/home/bmiller/sipp_call.pcap',
            loop=context.udp_transport.loop),
        local_addr=(context.test_host, 0)) # server mode
    user_protocol.rtp_endpoint = protocol

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.dial(context.test_users[receiver])
    # Wait for call to complete
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

@step('"{name}" waits for a call')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    user_protocol.wait = context.udp_transport.loop.create_future()
    async_context = use_or_create_async_context(context, 'udp_transport')
    _, protocol = \
        await context.udp_transport.loop.create_datagram_endpoint(
            lambda: RtpEcho(async_context.loop, on_con_lost=None),
            local_addr=(context.test_host, 0)) # server mode

    user_protocol.rtp_endpoint = protocol
    # SipPhone state machine should now be primed for INVITE

@then('"{receiver}" answers the call')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, receiver):
    user_protocol = context.sip_xport[receiver][1]
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

@then('pause for {time} seconds')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, time):
    await sleep(int(time))

@then('"{name}" hangs up')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.hangup()
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

@then('"{name}" starts waiting')
def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    user_protocol.wait = context.udp_transport.loop.create_future()

@then('"{name}" waits for hangup')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    assert user_protocol.wait is not None
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

@then('"{name}" unregisters')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    user_protocol = context.sip_xport[name][1]

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_unregistration()
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

@then('"{name}" subscribes to "{user_or_uri}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, user_or_uri):
    # user_or_uri is user name or full SIP URI
    user_protocol = context.sip_xport[name][1]
    if user_or_uri in context.test_users:
        req_uri = context.test_users[user_or_uri]['sipuri']
    else:
        req_uri = user_or_uri

    presence_sub = support.sip_subscribe(context.test_users[name],
        context.test_users[user_or_uri]['sipuri'], req_uri,
        sockname=user_protocol.local_addr, event='presence',
        accept='multipart/related, application/rlmi+xml, application/pidf+xml')
    user_protocol.sendto(presence_sub)
    wait_for_response(user_protocol, '202')

@then('"{name}" unsubscribes from "{user_or_uri}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, user_or_uri):
    user_protocol = context.sip_xport[name][1]
    # For unsubscribe, always use the extension and the UC URI
    server = context.test_servers[context.test_users[name]['server']]
    if user_or_uri in context.test_users:
        req_uri = f'sip:{context.test_users[user_or_uri]["extension"]}@{server[0]}:{server[1]}'
    else:
        req_uri = f'sip:{user_or_uri}@{server[0]}:{server[1]}'

    presence_unsub = support.sip_subscribe(context.test_users[name],
        context.test_users[user_or_uri]['sipuri'], req_uri,
        sockname=user_protocol.local_addr, event='presence',
        accept='multipart/related, application/rlmi+xml, application/pidf+xml',
        expires=0)
    user_protocol.sendto(presence_unsub)
    wait_for_response(user_protocol, '202')

async def wait_for_response(protocol, expected_code):
    response = await protocol.rcv_queue.get()
    while response is not None:
        code = int(sipmsg.Response.get_code(response))
        logging.info('wait_for_response: received %i', code)
        assert_that(code).described_as('response').is_less_than(300)
        if code >= 200:
            break
        response = await protocol.rcv_queue.get()

    assert_that(sipmsg.Response.get_code(response)).\
        described_as('response').is_equal_to(expected_code)

@then('"{subscriber}" has received "{state}" notification for "{source}"')
def step_impl(context, subscriber, state, source):
    user_protocol = context.sip_xport[subscriber][1]
    notifications = user_protocol.get_rcvd('NOTIFY')
    assert len(notifications) != 0
    notifications.reverse()
    assert state in notifications[0]
    assert state in notifications[1]
