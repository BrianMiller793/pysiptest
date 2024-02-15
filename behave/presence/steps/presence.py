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
import copy
import logging
from assertpy import assert_that

# pylint: disable=E0401,E0102,C0413
from pysiptest.rtpecho import RtpEcho
from pysiptest.rtpplay import RtpPlay
import pysiptest.headerfield as hf
from pysiptest import sipmsg
from pysiptest import support

from behave import given, then, step    # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context

import publish_msg as psm
from mass_presence import ext2name

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

@then('"{name}" subscribes to "{user_or_uri}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, user_or_uri):
    # user_or_uri is user name or full SIP URI
    user_protocol = context.sip_xport[name][1]
    if user_or_uri in context.test_users:
        req_uri = context.test_users[user_or_uri]['sipuri']
    else:
        req_uri = user_or_uri
    if 'sip_auth_uri' in context.test_users[name]:
        sip_auth_uri = context.test_users[name]['sip_auth_uri']
    else:
        sip_auth_uri = f"sip:{context.test_users[name]['domain']}"

    # RFC 3265 3.3.4, RFC 6665 4.4.1, Dialog creation and termination
    # Dialog is Call-ID, To, and Event
    # context.test_users[name]['subscriptions'][0] is Call-ID
    #                                          [1] is Proxy-Authenticate
    #                                          [2] is To
    logging.debug('subscribes to: initial subscription')
    if 'subscriptions' not in context.test_users[name]:
        context.test_users[name]['subscriptions'] = {}
    context.test_users[name]['subscriptions'][user_or_uri] = ('', '', '')

    subscribe_sub = support.sip_subscribe(context.test_users[name],
        context.test_users[user_or_uri]['sipuri'], req_uri,
        sockname=user_protocol.local_addr, event='presence', expires=120,
        accept='multipart/related, application/rlmi+xml, application/pidf+xml')

    subscribe_sub.field('CSeq').value = user_protocol.cseq_out_of_dialog
    user_protocol.sendto(subscribe_sub)
    response = await wait_for_response(user_protocol, [202, 407])
    rfields = hf.HeaderFieldValues(response)
    # Call-ID & Proxy-Authenticate dialog creation
    context.test_users[name]['subscriptions'][user_or_uri] = \
        (subscribe_sub.field('Call_ID').value,
        '',
        rfields.getfield('To')[0])

    response_status = rfields.getfield('SIP/2.0')[0].split(maxsplit=1)[0]
    logging.debug('subscribes to: response, status=%s', response_status)

    if response_status == '407':
        subscribe_auth = copy.copy(subscribe_sub)
        # RFC 8760 -- there may be more than one Authenticate
        proxy_authenticate = rfields.getfield('Proxy-Authenticate')[0]
        context.test_users[name]['subscriptions'][user_or_uri] = \
            (subscribe_sub.field('Call_ID').value,
            proxy_authenticate,
            rfields.getfield('To')[0])

        logging.debug('challenge=%s, request_method=%s, userinfo:%s, uri=%s',
                proxy_authenticate,
                subscribe_auth.method, str(context.test_users[name]), sip_auth_uri)
        subscribe_auth.hdr_fields.append(
            hf.Proxy_Authorization(value=user_protocol.get_digest_auth(
                proxy_authenticate,
                subscribe_auth.method, context.test_users[name], uri=sip_auth_uri)))
        subscribe_auth.field('CSeq').value = user_protocol.cseq_out_of_dialog
        subscribe_auth.sort()
        user_protocol.sendto(subscribe_auth)
        await wait_for_response(user_protocol, [202])
    assert user_or_uri in \
            context.test_users[name]['subscriptions']
    logging.debug('subscribes to: keys=%s', str(context.test_users[name]['subscriptions'].keys()))

@then('"{name}" renews subscription with cached authentication to "{user_or_uri}" and expect "{expected_code}"') # pylint: disable=C0301
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, user_or_uri, expected_code):
    # user_or_uri is user name or full SIP URI
    user_protocol = context.sip_xport[name][1]
    assert 'subscriptions' in context.test_users[name]

    if user_or_uri in context.test_users:
        req_uri = context.test_users[user_or_uri]['sipuri']
        to_user_name = user_or_uri
    else:
        req_uri = user_or_uri
        extension = user_or_uri[4:].split('@')[0]
        print('extension={extension}')
        to_user_name = context.test_users[ext2name(context, extension)]['name']

    assert 'subscriptions' in context.test_users[name]
    assert to_user_name in context.test_users[name]['subscriptions']

    if 'sip_auth_uri' in context.test_users[name]:
        sip_auth_uri = context.test_users[name]['sip_auth_uri']
    else:
        sip_auth_uri = f"sip:{context.test_users[name]['domain']}"

    # RFC 3265 3.3.4, RFC 6665 4.4.1, Dialog creation and termination
    # Dialog is Call-ID, To, and Event
    # context.test_users[name]['subscriptions'][0] is Call-ID
    #                                          [1] is Proxy-Authenticate
    subscribe_sub = support.sip_subscribe(context.test_users[name],
        context.test_users[to_user_name]['sipuri'], req_uri,
        sockname=user_protocol.local_addr, event='presence', expires=120,
        accept='multipart/related, application/rlmi+xml, application/pidf+xml')

    # Call-ID & Proxy-Authenticate
    subscribe_sub.field('Call_ID').value = \
        context.test_users[name]['subscriptions'][to_user_name][0]

    logging.debug('___ subscribes to ___: renewal')
    if context.test_users[name]['subscriptions'][to_user_name][1]:
        subscribe_sub.hdr_fields.append(
            hf.Proxy_Authorization(value=user_protocol.get_digest_auth(
                context.test_users[name]['subscriptions'][to_user_name][1],
                subscribe_sub.method, context.test_users[name],
                uri=sip_auth_uri)))
    subscribe_sub.field('Call_ID').value = \
        context.test_users[name]['subscriptions'][to_user_name][0]
    subscribe_sub.field('To').from_string(
        context.test_users[name]['subscriptions'][to_user_name][2])

    subscribe_sub.field('CSeq').value = user_protocol.cseq_out_of_dialog
    user_protocol.sendto(subscribe_sub)
    await wait_for_response(user_protocol, [int(expected_code)])

@then('"{name}" unsubscribes from "{user_or_uri}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, user_or_uri):
    assert user_or_uri in \
            context.test_users[name]['subscriptions']
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
        expires=0, call_id=context.test_users[name]['subscriptions'][user_or_uri][0])
    user_protocol.sendto(presence_unsub)
    response = await wait_for_response(user_protocol, [202, 407])

    rfields = hf.HeaderFieldValues(response)
    response_status = rfields.getfield('SIP/2.0')[0].split(maxsplit=1)[0]
    logging.debug('__ unsubscribes from __: response, status=%s', response_status)
    # RFC 8760 - there may be more than one authenticate
    if response_status == '407':
        unsub_auth = copy.copy(presence_unsub)
        sip_auth_uri = f"sip:{context.test_users[name]['domain']}"
        logging.debug('challenge=%s, request_method=%s, userinfo:%s, uri=%s',
                rfields.getfield('Proxy-Authenticate')[0],
                unsub_auth.method, str(context.test_users[name]), sip_auth_uri)
        unsub_auth.hdr_fields.append(
            hf.Proxy_Authorization(value=user_protocol.get_digest_auth(
                rfields.getfield('Proxy-Authenticate')[0],
                unsub_auth.method, context.test_users[name], uri=sip_auth_uri)))
        unsub_auth.field('CSeq').value = user_protocol.cseq_out_of_dialog
        unsub_auth.sort()
        user_protocol.sendto(unsub_auth)
        await wait_for_response(user_protocol, [202])

@then('"{subscriber}" has received "{state}" notification for "{source}"')
def step_impl(context, subscriber, state, source):
    assert source in context.test_users[subscriber]['subscriptions']
    user_protocol = context.sip_xport[subscriber][1]
    source_addr = context.test_users[source]['sipuri']
    notifications = [ m for m in user_protocol.get_rcvd('NOTIFY')
        if source_addr in m ]
    assert_that(len(notifications)).described_as('received NOTIFY')\
        .is_not_zero()
    notifications.reverse()
    assert_that(notifications[0]).described_as('state in NOTIFY')\
        .contains(state)

@then('"{name}" sets presence to "{state}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name, state):
    user_protocol = context.sip_xport[name][1]
    publish = support.sip_publish(
        context.test_users[name],
        context.test_users[name]['sipuri'], #request_uri
        user_protocol.local_addr, 'presence')
    publish.field('CSeq').value = user_protocol.cseq_in_dialog
    publish.body = psm.status(state, context.test_users[name]['sipuri'])

    # First PUBLISH will have no SIP-ETag value for SIP_If_Match
    if hasattr(context, 'SIP_ETag'):
        publish.hdr_fields.append(hf.SIP_If_Match(value=context.SIP_ETag))
        publish.sort()
    logging.debug('__ sets presence to __: publish=%s', str(publish))
    user_protocol.sendto(publish)

    response = await wait_for_response(user_protocol, [200])
    rfields = hf.HeaderFieldValues(response)
    assert_that(rfields.field_names).described_as('PUBLISH response').contains('SIP-ETag')
    context.SIP_ETag = rfields.getfield('SIP-ETag')[0]

@then('fail')
def step_impl(context):
    assert False

@then('"{user_name}" sets "{key}" to "{value}"')
def step_impl(context, user_name, key, value):
    assert user_name in context.test_users
    context.test_users[user_name][key] = value
