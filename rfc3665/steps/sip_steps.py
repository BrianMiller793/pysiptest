# vi: ai ts=4 sw=4 et
'''
Behave steps to for Feature: Registration, RFC 3665, Section 2
'''

from asyncio import sleep
import copy
import logging
import os
import socket
import sys
from behave import given, when, then # pylint: disable=E0611
from behave.api.async_step import \
    async_run_until_complete, use_or_create_async_context
from assertpy import assert_that

# pylint: disable=E0401,C0413,C0116,E0102
sys.path.append(os.getenv('PYSIP_LIB_PATH'))

import headerfield as hf
import sipmsg
from rtpecho import RtpEcho
from rtpplay import RtpPlay
from support import digest_auth, sip_register,\
    sip_invite, sip_ack, sip_bye

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
            context, context.test_users[user_name])

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
        hf.Authorization(value=digest_auth(www_authenticate, sip_request,
            context.test_users[user_name])))

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

@given('"{user_name}" waits for a call')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name):
    assert hasattr(context, 'sip_xport')
    assert user_name in context.sip_xport.keys()
    # Start RTP client for echo
    async_context = use_or_create_async_context(context, 'udp_transport')
    context.sip_xport[user_name][1].call_future = \
        async_context.loop.create_future()
    transport, _ = \
        await async_context.loop.create_datagram_endpoint(
            lambda: RtpEcho(async_context.loop, on_con_lost=None),
            local_addr=(context.test_host, 0))

    context.sip_xport[user_name][1].rtp_sockname = \
        transport.get_extra_info('socket').getsockname()

@when('"{caller_name}" calls "{receiver_name}"')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, caller_name, receiver_name):
    # Start RTP client for playback
    assert hasattr(context, 'test_host')
    async_context = use_or_create_async_context(context, 'udp_transport')
    transport, protocol = \
        await async_context.loop.create_datagram_endpoint(
            lambda: RtpPlay(on_con_lost=None,
                file_name='/home/bmiller/sipp_call.pcap',
                loop=async_context.loop),
            local_addr=(context.test_host, 0))

    logging.debug('... calls ...: RtpPlay sockname=%s',
        transport.get_extra_info('socket').getsockname())
    context.sip_xport[caller_name][1].rtp_sockname = \
        transport.get_extra_info('socket').getsockname()
    context.rtp_play = (transport, protocol)

    context.invite_msg = sip_invite(context,
        context.test_users[caller_name],
        context.test_users[receiver_name],
        context.rtp_play[0].get_extra_info('socket').getsockname())
    addr = context.sip_xport[caller_name][0].get_extra_info('socket').getsockname()
    contact_info = context.test_users[caller_name]
    context.invite_msg.field('Contact').from_string(
        f'<sip:{contact_info["extension"]}@{addr[0]}:{addr[1]}>')
    context.invite_msg.sort()

@when('"{user_name}" Contact field port is set to {portnum}')
def step(context, user_name, portnum):
    assert context.invite_msg is not None
    extension = context.test_users[user_name]["extension"]
    addr = context.sip_xport[user_name][0].get_extra_info('socket').getsockname()
    context.invite_msg.field('Contact').from_string(
        f'<sip:{extension}@{addr[0]}:{portnum}>')

@when('"{user_name}" makes the call')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name):
    '''Make a call with authentication.  context.invite_msg is ready.'''
    # Send INVITE w/SDP
    # Wait 100 Trying
    # Wait 407 Proxy Authentication Required
    # Send ACK
    # Send INVITE with Proxy-Authorization w/SDP
    # Wait 100 Trying
    # Wait 180 Ringing
    # Wait 200 OK
    # Send ACK
    assert context.invite_msg is not None
    # Send INVITE, expect SIP/2.0 407 Proxy Authentication Required
    logging.info('%s makes the call: send INVITE', user_name)
    context.sip_xport[user_name][1].sendto(context.invite_msg)

    # Wait 100 Trying
    raw_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    if sipmsg.Response.get_code(raw_msg) == 100:
        # Wait 407 Proxy Authentication Required
        raw_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    assert_that(sipmsg.Response.get_code(raw_msg)).described_as('response').is_equal_to('407')
    # send ACK
    logging.info('%s makes the call: create ACK', user_name)
    addr = context.sip_xport[user_name][0].get_extra_info('socket').getsockname()
    auth_ack = sip_ack(raw_msg, context.test_users[user_name], addr)
    logging.info('%s makes the call: ACK: %s', user_name, str(auth_ack))
    context.sip_xport[user_name][1].sendto(auth_ack)

    # Send INVITE with Proxy-Authorization
    sip_dict = hf.msg2fields(context.sip_xport[user_name][1].recvd_pkts[-1])
    assert 'Proxy-Authenticate' in sip_dict.keys()
    proxy_authenticate = sip_dict['Proxy-Authenticate']
    sip_request = sip_dict['CSeq'].split()[-1] # Request name is in CSeq
    context.invite_msg.hdr_fields.append(
        hf.Proxy_Authorization(value=digest_auth(proxy_authenticate,
            sip_request, context.test_users[user_name],
            uri=context.test_users[user_name]['sipuri'])))
    context.invite_msg.field('CSeq').value += 1
    context.invite_msg.sort()
    logging.info('%s makes the call: send INVITE with Authorization', user_name)
    context.sip_xport[user_name][1].sendto(context.invite_msg)

    # Wait 100 Trying
    raw_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    assert_that(sipmsg.Response.get_code(raw_msg)).described_as('response').is_equal_to('100')
    # Wait 180 Ringing
    raw_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    assert_that(sipmsg.Response.get_code(raw_msg)).described_as('response').is_equal_to('180')
    # Wait 200 OK
    raw_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    assert_that(sipmsg.Response.get_code(raw_msg)).described_as('response').is_equal_to('200')
    sipsdp_fields = hf.msg2fields(raw_msg)
    assert_that(sipsdp_fields['Content-Type'])\
        .described_as('SIP field Content-Type').is_equal_to('application/sdp')
    body = raw_msg[len(raw_msg) - int(sipsdp_fields['Content-Length']):]
    rtp_ip = hf.sdp_fields(body, 'c')[0].split()[-1]
    rtp_port = hf.sdp_fields(body, 'm')[0].split()[1]
    context.rtp_play[1].dest_addr = (rtp_ip, int(rtp_port))
    logging.debug('%s makes the call: remote RTP endpoint %s',
        user_name, str(context.rtp_play[1].dest_addr))

    # Begin the RTP playback
    context.rtp_play[1].begin()
    # Send ACK
    sdp_msg = context.sip_xport[user_name][1].get_prev_rcvd(method='200')
    prev_invite = context.sip_xport[user_name][1].get_prev_sent('INVITE')
    proxy_auth = copy.deepcopy(prev_invite.field('Proxy_Authorization'))
    ack_msg = sip_ack(sdp_msg, context.test_users[user_name], addr)
    ack_msg.hdr_fields.append(proxy_auth)
    ack_msg.sort()
    context.sip_xport[user_name][1].sendto(ack_msg)


# pylint: disable=W0613
@then('"{user_name}" answers the call')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name):
    # ## This sequence is actually in the autoresponse
    # wait for INVITE
    # send 100 Trying
    # send 180 Ringing
    # send 200 OK w/SDP body
    # wait for ACK request
    await context.sip_xport[user_name][1].call_future
    assert_that(context.sip_xport[user_name][1].in_a_call).is_true()

@then('"{user_name}" ends the call')
@async_run_until_complete(async_context='udp_datagram')
async def step(context, user_name):
    # Send BYE
    addr = context.sip_xport[user_name][0].get_extra_info('socket').getsockname()
    # The SDP message will have the appropriate tags for To and From
    sdp_msg = context.sip_xport[user_name][1].get_prev_rcvd(method='200')
    assert sdp_msg is not None
    # A received INVITE message will have Contact
    invite_msg = context.sip_xport[user_name][1].get_prev_rcvd(method='INVITE')
    contact = None
    if invite_msg is not None:
        contact = hf.msg2fields(invite_msg)['Contact'].trim('<>')
    logging.debug('ends the call: sdp_msg=%s', str(sdp_msg))
    bye_msg = sip_bye(sdp_msg, context.test_users[user_name], addr, contact=contact)
    logging.debug('ends the call: bye_msg=%s', str(bye_msg))
    context.sip_xport[user_name][1].sendto(bye_msg)

    # Expect 200 OK
    resp_msg = await context.sip_xport[user_name][1].rcv_queue.get()
    assert_that(sipmsg.Response.get_code(resp_msg)).described_as('response').is_equal_to('200')

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
