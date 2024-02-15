'''Provide steps supporting SUBSCRIBE and PUBLISH request methods.'''
# vim: ts=4 sw=4 et ai

# RFC 6665, SIP-Specific Event Notification
# RFC 5262, Presence Information Data Format (PIDF) Extension for
#           Partial Presence
# RFC 4662, A Session Initiation Protocol (SIP) Event Notification
#           Extension for Resource Lists
# RFC 3903, Session Initiation Protocol (SIP) Extension
#           for Event State Publication
# RFC 3265, Session Initiation Protocol (SIP)-Specific Event Notification,
#           obsoleted by 6665

from asyncio import sleep
import logging
from assertpy import assert_that

# pylint: disable=E0401,E0102,C0413
from pysiptest.rtpecho import RtpEcho
from pysiptest.rtpplay import RtpPlay
from pysiptest import sipmsg

from behave import given, then, step    # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context


# pylint: disable=W0613,C0116

async def wait_for_response(protocol, expected_codes):
    '''Wait for a response, and assert its value.'''
    response = await protocol.rcv_queue.get()
    while response is not None:
        logging.debug('wait_for_response: received %s', sipmsg.Response.get_code(response))
        code = int(sipmsg.Response.get_code(response))
        if code in expected_codes:
            return response
        assert_that(code).described_as('response').is_less_than(300)
        if code >= 200:
            break
        response = await protocol.rcv_queue.get()

    assert_that(sipmsg.Response.get_code(response)).is_in(*expected_codes)
    return response

# REGISTER sip:teo SIP/2.0
# SIP/2.0 401 Unauthorized
# REGISTER sip:teo SIP/2.0
# SIP/2.0 200 OK
@given('"{name}" registers')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    assert name in context.sip_xport
    user_protocol = context.sip_xport[name][1]
    if not user_protocol.is_registered:
        user_protocol.wait = context.udp_transport.loop.create_future()
        user_protocol.start_registration(expires=1800)
        await user_protocol.wait
        assert user_protocol.wait.result() is True
        user_protocol.wait = None
        assert user_protocol.is_registered

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
            file_name='sipp_call.pcap',
            loop=context.udp_transport.loop),
        local_addr=(context.test_host, 0)) # server mode
    user_protocol.rtp_endpoint = protocol

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.dial(context.test_users[receiver])
    # Wait for call to complete
    await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ calls __').is_true()
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
    assert_that(user_protocol.wait.result())\
        .described_as('__ answers the call').is_true()
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
    assert_that(user_protocol.wait.result())\
        .described_as('__ hangs up').is_true()
    user_protocol.wait = None

@then('"{name}" starts waiting')
def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    user_protocol.wait = context.udp_transport.loop.create_future()

@then('"{name}" waits for hangup')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    assert_that(user_protocol.wait)\
        .described_as('__ waits for hangup:future').is_not_none()
    await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ waits for hangup').is_true()
    user_protocol.wait = None

@then('"{name}" unregisters')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    user_protocol = context.sip_xport[name][1]

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_unregistration()
    await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ unregisters').is_true()
    user_protocol.wait = None
