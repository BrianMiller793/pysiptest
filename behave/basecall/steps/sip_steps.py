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
from pysiptest import headerfield as hf

from behave import given, then, step    # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context


# pylint: disable=W0613,C0116

async def wait_for_response(protocol, expected_codes):
    '''Wait for a response, and assert its value.'''
    if not protocol.wait.done():
        response = await protocol.rcv_queue.get()
    while response is not None:
        logging.debug('wait_for_response: received %s', sipmsg.Response.get_code(response))
        code = int(sipmsg.Response.get_code(response))
        if code in expected_codes:
            return response
        assert_that(code).described_as('response').is_less_than(300)
        if code >= 200:
            break
        if not protocol.wait.done():
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
        logging.debug('registers %s: wait=loop.create_future()', name)
        user_protocol.wait = context.udp_transport.loop.create_future()
        user_protocol.start_registration(expires=1800)
        if not user_protocol.wait.done():
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

    logging.debug('calls %s, %s: wait=loop.create_future()', caller, receiver)
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.dial(context.test_users[receiver])
    # Wait for call to complete
    if not user_protocol.wait.done():
        await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ calls __').is_true()
    user_protocol.wait = None

@then('"{from_name}" transfers to "{to_name_uri}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, from_name, to_name_uri):
    '''REFER transfers call to another extension.'''
    # Same flow as BYE, expect 202, then wait for BYE
    # Refer-to may require encoding
    assert to_name_uri in context.test_users
    user_protocol = context.sip_xport[from_name][1]
    refer_to = f"<{context.test_users[to_name_uri]['sipuri']}>"

    refer_msg = refer_from_ack(refer_to,
            user_protocol.get_prev_rcvd('ACK'),
            user_protocol)
    logging.debug('%s transfers to %s: wait=loop.create_future()', from_name, to_name_uri)
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.sendto(refer_msg)
    if not user_protocol.wait.done():
        await user_protocol.wait
    assert_that(user_protocol.wait.result()).described_as('refer').is_true()
    user_protocol.wait = None

def refer_from_ack(refer_to:str, ack_msg:str, user_protocol):
    '''Create a REFER request from a previous received ACK'''
    ack_hdrs = hf.HeaderFieldValues(ack_msg)
    refer_msg = sipmsg.Refer(
        request_uri=ack_hdrs.getfield('Contact')[0].strip('<>'),
        transport='UDP')
    refer_msg.init_mandatory()
    refer_msg.field('Via').via_params['address'] = \
            f"{user_protocol.local_addr[0]}:{user_protocol.local_addr[1]}"
    refer_msg.field('Via').via_params['transport'] = refer_msg.transport
    refer_msg.field('From').from_string(ack_hdrs.getfield('To')[0])
    refer_msg.field('To').from_string(ack_hdrs.getfield('From')[0])
    refer_msg.field('Call_ID').value = ack_hdrs.getfield('Call-ID')[0]
    refer_msg.field('CSeq').method = refer_msg.method
    refer_msg.field('CSeq').value = user_protocol.cseq_in_dialog
    contact = f"<{ack_hdrs.getfield('ACK')[0].split()[0]}>"
    refer_msg.field('Contact').value = contact
    refer_msg.field('Referred_By').value = contact
    refer_msg.field('Refer_To').value = refer_to
    refer_msg.sort()
    return refer_msg

@step('"{name}" expects a call')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    logging.debug('waits for a call %s: wait=loop.create_future', name)
    user_protocol.wait = context.udp_transport.loop.create_future()
    async_context = use_or_create_async_context(context, 'udp_transport')
    _, protocol = \
        await context.udp_transport.loop.create_datagram_endpoint(
            lambda: RtpEcho(async_context.loop, on_con_lost=None),
            local_addr=(context.test_host, 0)) # server mode

    user_protocol.rtp_endpoint = protocol
    # SipPhone state machine should now be primed for INVITE

@then('"{name}" answers the call')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    '''Step waits on Future object'''
    user_protocol = context.sip_xport[name][1]
    logging.debug('answers the call %s:wait= %s', name,
        'None' if user_protocol.wait is None else 'not None')
    if not user_protocol.wait.done():
        logging.debug('answers the call %s:waiting', name)
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
    logging.debug('hangs up %s: wait=loop.create_future()', name)
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.hangup()
    if not user_protocol.wait.done():
        await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ hangs up').is_true()
    user_protocol.wait = None

@then('"{name}" starts waiting')
def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    logging.debug('starts waiting %s: wait=loop.create_future()', name)
    user_protocol.wait = context.udp_transport.loop.create_future()

@then('"{name}" waits for hangup')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    user_protocol = context.sip_xport[name][1]
    assert_that(user_protocol.wait)\
        .described_as('__ waits for hangup:future').is_not_none()
    if not user_protocol.wait.done():
        await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ waits for hangup').is_true()
    user_protocol.wait = None

@then('"{name}" unregisters')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    user_protocol = context.sip_xport[name][1]

    logging.debug('unregisters %s: wait=loop.create_future()', name)
    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_unregistration()
    if not user_protocol.wait.done():
        await user_protocol.wait
    assert_that(user_protocol.wait.result())\
        .described_as('__ unregisters').is_true()
    user_protocol.wait = None
