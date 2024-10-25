'''Provide FreeSWITCH event socket steps for Behave test'''
# vim: ts=4 sw=4 et ai
# pylint: disable=E0401,E0102,C0413,W0108,C0116,W0603

import datetime
import logging
import socket

from pysiptest.eventsocket import EventSocket
from pysiptest import headerfield as hf
from behave import then    # pylint: disable=E0611
from behave.api.async_step import async_run_until_complete

#pylint: disable=W0613

BACKGROUND_LOOP = None
EVENT_SOCKET = None
LOOP_TIMER = 0
LOOP_ITER = 0
SIP_CALLID = None
def background_task():
    '''Background task example'''
    global LOOP_TIMER, LOOP_ITER
    EVENT_SOCKET.write(f'bgapi uuid_send_info {SIP_CALLID} {datetime.datetime.now().isoformat()}')
    logging.debug('events:background_task, messages.empty=%s',
        EVENT_SOCKET.messages.empty())
    while not EVENT_SOCKET.messages.empty():
        EVENT_SOCKET.messages.get_nowait()
        #logging.debug('events:background_task, messages=%s',
        #    EVENT_SOCKET.messages.get_nowait())
    LOOP_ITER -= 1
    if LOOP_ITER > 0:
        LOOP_TIMER += 1.0
        BACKGROUND_LOOP.call_at(LOOP_TIMER, background_task)

def csv2list(csv_data):
    '''Convert CSV data to lists.'''
    csv_list = []
    for csv_line in csv_data.splitlines():
        csv_list.append(csv_line.split(sep=','))
    return csv_list

def parse_registrations(reg_raw):
    '''Parse registration data, returns array of dict.'''
    registrations = []
    registration = {}
    for line in reg_raw.splitlines():
        if 'Registrations' in line:
            continue
        if 'Total items returned' in line:
            continue
        if 'Content-' in line:
            continue
        if '=====' in line:
            continue
        if len(line) == 0:
            if len(registration) != 0:
                registrations.append(registration)
            registration = {}
            continue
        reg_data = line.split(sep=':')
        registration[reg_data[0]] = reg_data[1].lstrip()
    return registrations

@then('connect to server {uas_name} event socket')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, uas_name):
    global EVENT_SOCKET
    assert uas_name in context.test_servers
    logging.debug('events:connect event socket: server %s', uas_name)
    _, context.event_socket = \
        await context.udp_transport.loop.create_connection(
        lambda: EventSocket(),
        host=context.test_servers[uas_name][0], port=8021, flags=socket.TCP_NODELAY)
    context.event_socket.begin()
    EVENT_SOCKET = context.event_socket

    # Login to event socket
    msg = await EVENT_SOCKET.messages.get()
    assert 'auth/request' in msg
    EVENT_SOCKET.write('auth ' + EVENT_SOCKET.password)
    msg = await EVENT_SOCKET.messages.get()
    assert 'OK accepted' in msg
    #EVENT_SOCKET.write('event plain CHANNEL_CALLSTATE')

@then('do something in the background for a bit')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context):
    global BACKGROUND_LOOP, LOOP_TIMER
    BACKGROUND_LOOP = context.udp_transport.loop
    LOOP_TIMER = BACKGROUND_LOOP.time() + 1.0
    BACKGROUND_LOOP.call_at(LOOP_TIMER, background_task)

@then('get channel info for current calls')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context):
    global SIP_CALLID
    while not EVENT_SOCKET.messages.empty():
        EVENT_SOCKET.messages.get_nowait()
    #EVENT_SOCKET.write('api show detailed_calls')

    EVENT_SOCKET.write('api show channels')

    # read content
    msg = await EVENT_SOCKET.messages.get()

    # Separate Content-Len from existing content
    header_len = len(''.join(msg.splitlines(keepends=True)[:3]))
    content_len = int(msg.splitlines()[1].split()[1])
    remaining_total_len = len(msg) - header_len - content_len
    while remaining_total_len > 0:
        new_data = await EVENT_SOCKET.messages.get()
        msg += new_data
        remaining_total_len -= len(new_data)

    content = msg[header_len:header_len+content_len]
    content = content[:content.find('\n\n')]
    calls = csv2list(content)
    SIP_CALLID = calls[1][calls[0].index('uuid')]
    assert SIP_CALLID

    EVENT_SOCKET.write(f'api uuid_setvar {SIP_CALLID} fs_send_unsupported_info 1')
    logging.debug(
        'events:get channel info: api uuid_setvar %s fs_send_unsupported_info 1',
        SIP_CALLID)
    msg = await EVENT_SOCKET.messages.get()

@then('get SIP call info for {user_name}')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, user_name):
    global SIP_CALLID
    user_protocol = context.sip_xport[user_name][1]
    invite = user_protocol.get_prev_rcvd('INVITE')
    if invite:
        headers = hf.msg2fields(invite)
        invite_call_id = headers['CALL-ID']
    else:
        invite = user_protocol.get_prev_sent('INVITE')
        invite_call_id = invite.field('Call_ID')
    SIP_CALLID = invite_call_id

    logging.debug('events:get call info for: SIP_CALLID=%s', SIP_CALLID)
    assert SIP_CALLID is not None
    assert SIP_CALLID
    #EVENT_SOCKET.write('api sofia status profile internal reg')
    #msg = await EVENT_SOCKET.messages.get()
    #while not 'Total items returned' in msg and msg.endswith('\n\n'):
    #    msg += await EVENT_SOCKET.messages.get()
    #registrations = parse_registrations(msg)
    #extension = context.test_users[user_name]["sipuri"][4:]
    #user_reg = [r for r in registrations if extension in r['User']][0]
    #SIP_CALLID = user_reg['Call-ID']

@then('send {num_messages} INFO to caller')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, num_messages):
    global BACKGROUND_LOOP, LOOP_TIMER, LOOP_ITER
    LOOP_ITER = int(num_messages)
    BACKGROUND_LOOP = context.udp_transport.loop
    LOOP_TIMER = BACKGROUND_LOOP.time() + 1.0
    BACKGROUND_LOOP.call_at(LOOP_TIMER, background_task)

@then('stop event background task')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context):
    global LOOP_ITER
    LOOP_ITER = 0

#sofia status profile internal reg
#sofia profile internal flush_inbound_reg
#fsctl hupall
