'''Provide steps supporting call parking using REFER request method.'''
# vim: ts=4 sw=4 et ai

from asyncio import sleep
import copy
import logging

# pylint: disable=E0401,E0102,C0413
from pysiptest.rtpecho import RtpEcho
from pysiptest.rtpplay import RtpPlay

import pysiptest.headerfield as hf
from pysiptest import sipmsg
from pysiptest import support

from assertpy import assert_that
from behave import given, then, step    # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context

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
        lambda: RtpPlay(context.udp_transport.loop, on_con_lost=None,
            file_name='/home/bmiller/sipp_call.pcap'),
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

# UAC > UAS: SIP: INVITE sip:teo_ucm@192.168.0.156:5060 SIP/2.0 + SDP
# UAS > UAC: SIP: SIP/2.0 100 Trying
# UAS > UAC: SIP: SIP/2.0 200 OK + SDP
# UAC > UAS: SIP: ACK sip:teo_ucm@192.168.0.156:5060 SIP/2.0
# UAC > UAS: SIP: REFER sip:teo_ucm@192.168.0.156:5060 SIP/2.0
# UAS > UAC: SIP: SIP/2.0 202 Accepted
# UAS > UAC: NOTIFY sip:2001@192.168.0.247:5060 SIP/2.0 + sipfrag (auto)
# UAC > UAS: OK
# UAS > UAC: SIP: BYE sip:2001@192.168.0.247:5060 SIP/2.0 (auto)
# UAC > UAS: SIP: SIP/2.0 200 OK
# RFC 3515, Contact a third party, RFC 4488, RFC 4508, RFC 7614
@then('"{receiver}" parks "{caller}" on "{park_ext}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, receiver, caller, park_ext):
    # in-dialog INVITE to change SDP
    user_protocol = context.sip_xport[receiver][1]
    prev_ack = user_protocol.get_prev_rcvd('ACK')
    assert prev_ack is not None
    pa_fields = hf.HeaderFieldValues(prev_ack)
    req_uri = pa_fields.getfield('Contact')[0].strip('<>')
    park_invite = support.sip_invite(
        user_protocol.local_addr,
        context.test_users[receiver],
        context.test_users[caller],
        user_protocol.rtp_endpoint.local_addr,
        request_uri=req_uri)
    park_invite.field('From').tag = pa_fields.getfield('To')[0].split('=')[-1]
    park_invite.field('To').tag = pa_fields.getfield('From')[0].split('=')[-1]
    park_invite.field('CSeq').value = user_protocol.cseq_in_dialog
    park_invite.field('Call_ID').value = pa_fields.getfield('Call-ID')[0]
    park_invite.field('Contact').from_string(
        f'<sip:{user_protocol.user_info["extension"]}@{user_protocol.local_addr[0]}:{user_protocol.local_addr[1]}>')

    sent_sdp_msg = [m for m in user_protocol.sent_msgs if m.body is not None]
    sdp_body = copy.copy(sent_sdp_msg[-1].body)
    park_invite.body = sdp_body.replace('sendrecv', 'sendonly')
    park_invite.sort()
    user_protocol.sendto(park_invite)

    # Wait for 200
    response = await user_protocol.rcv_queue.get()
    while response is not None:
        code = int(sipmsg.Response.get_code(response))
        logging.info('__ parks __ on __: received %i', code)
        assert_that(code).described_as('response').is_less_than(300)
        if code >= 200:
            break
        response = await user_protocol.rcv_queue.get()

    assert_that(sipmsg.Response.get_code(response)).described_as('response').is_equal_to('200')
    park_ack = support.sip_ack(response, user_protocol.user_info, user_protocol.local_addr)
    user_protocol.sendto(park_ack)

    # Waiting point to receive BYE
    user_protocol.wait = context.udp_transport.loop.create_future()

    park_refer = support.sip_refer(
        from_user=context.test_users[receiver],
        to_user=context.test_users[caller],
        sockname=user_protocol.local_addr, park_ext=park_ext,
        request_uri=req_uri)
    park_refer.field('From').tag = pa_fields.getfield('To')[0].split('=')[-1]
    park_refer.field('To').tag = pa_fields.getfield('From')[0].split('=')[-1]
    park_refer.field('Call_ID').value = pa_fields.getfield('Call-ID')[0]
    park_refer.field('CSeq').value = user_protocol.cseq_in_dialog
    user_protocol.sendto(park_refer)

    r202accepted = await user_protocol.rcv_queue.get()
    assert_that(sipmsg.Response.get_code(r202accepted)).described_as('response').is_equal_to('202')

    # Wait for BYE
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

# .155 > .156: SIP: INVITE sip:*72500@teo;user=phone SIP/2.0
# .156 > .155: SIP: SIP/2.0 100 Trying
# .156 > .155: SIP: SIP/2.0 407 Proxy Authentication Required
# .155 > .156: SIP: ACK sip:*72500@teo;user=phone SIP/2.0
# .155 > .156: SIP: INVITE sip:*72500@teo;user=phone SIP/2.0
# .156 > .155: SIP: SIP/2.0 100 Trying
# .156 > .155: SIP: SIP/2.0 200 OK
# .155 > .156: SIP: ACK sip:*72500@192.168.0.156:5060;transport=udp SIP/2.0
@then('"{dest_user}" unparks "{caller}" from "{park_sipaddr}"')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, dest_user, caller, park_sipaddr):
    park_ext = {
        'name': '',
        'extension': park_sipaddr.split('@')[0][4:],
        'domain': 'teo',
        'sipuri': park_sipaddr,
        'server': 'Biloxi',
        'password': None,
        'transport': None}
    user_protocol = context.sip_xport[dest_user][1]

    # Create RTP playback endpoint
    _, protocol = await context.udp_transport.loop.create_datagram_endpoint(
        lambda: RtpPlay(context.udp_transport.loop, on_con_lost=None,
            file_name='/home/bmiller/sipp_call.pcap'),
        local_addr=(context.test_host, 0)) # server mode
    user_protocol.rtp_endpoint = protocol

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.dial(park_ext)
    # Wait for call to complete
    await user_protocol.wait
    assert user_protocol.wait.result() is True
    user_protocol.wait = None

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
