'''Define steps for presence routing tests.'''

from asyncio import sleep
import logging
import os
import subprocess
from assertpy import assert_that
from behave import given, then      # pylint: disable=E0611
from behave.api.async_step import async_run_until_complete

# pylint: disable=E0102,W0613,C0116,C0301

def update_routing_config(domain, extension, routing):
    path = f'/opt/freeswitch/conf/directory/{domain}/{extension}.xml'
    sed_expression = f'sed -i -e /routes_available/s/value="[^"]*"/value="{routing}"/'
    docker_host = os.environ['FS_CONTAINER']
    command = f'docker exec {docker_host} {sed_expression} {path}'
    subprocess.run(command.split(), check=False)
    subprocess.run(f'docker exec {docker_host} fs_cli -x reloadxml'.split(), check=False)

@given('{extension} rings to {receiver1} and {receiver2} then {receiver3}')
def step_impl(context, extension, receiver1, receiver2, receiver3):
    assert 'FS_CONTAINER' in os.environ
    assert receiver1 in context.test_users
    assert receiver2 in context.test_users
    assert receiver3 in context.test_users
    routing = f'{context.test_users[receiver1]["extension"]}:0,{context.test_users[receiver2]["extension"]}:6,{context.test_users[receiver3]["extension"]}:6,'
    update_routing_config(context.test_users[receiver1]["domain"],
        context.test_users[receiver1]["extension"], routing)

@given('{extension} rings to {receiver1} and {receiver2}')
def step_impl(context, extension, receiver1, receiver2):
    #context.test_users[receiver1]["extension"]}
    assert 'FS_CONTAINER' in os.environ
    assert receiver1 in context.test_users
    assert receiver2 in context.test_users
    routing = f'{context.test_users[receiver1]["extension"]}:0,{context.test_users[receiver1]["extension"]}:6,,'
    update_routing_config(context.test_users[receiver1]["domain"],
        context.test_users[receiver1]["extension"], routing)

@given('{extension} rings to {receiver1} then {receiver2}')
def step_impl(context, extension, receiver1, receiver2):
    assert 'FS_CONTAINER' in os.environ
    assert receiver1 in context.test_users
    assert receiver2 in context.test_users
    routing = f'{context.test_users[receiver1]["extension"]}:6,{context.test_users[receiver1]["extension"]}:6,,'
    update_routing_config(context.test_users[receiver1]["domain"],
        context.test_users[receiver1]["extension"], routing)

@given('{extension} rings to {receiver}')
def step_impl(context, extension, receiver):
    assert 'FS_CONTAINER' in os.environ
    assert receiver in context.test_users
    routing = f'{context.test_users[receiver]["extension"]}:6,,,'
    update_routing_config(context.test_users[receiver]["domain"],
        context.test_users[receiver]["extension"], routing)

@given('{name} is registered and waiting')
@async_run_until_complete(async_context='udp_transport')
async def step_impl(context, name):
    assert 'udp_transport' in context
    assert 'sip_xport' in context
    assert name in context.sip_xport
    user_protocol = context.sip_xport[name][1]
#    if not user_protocol.is_registered:
#        logging.debug('step presroute: %s is registered and waiting: wait=loop.create_future()', name)
#        user_protocol.wait = context.udp_transport.loop.create_future()
#        user_protocol.start_registration()
#        if not user_protocol.wait.done():
#            await user_protocol.wait
#        assert user_protocol.wait.result() is True
#        user_protocol.wait = None
    assert user_protocol.is_registered

    # Tried this, failed
    # context.execute_steps(f'then {name} registers')
    assert name in context.test_users
    user_protocol = context.sip_xport[name][1]
    assert user_protocol.is_registered
    user_protocol.wait = context.udp_transport.loop.create_future()

#@given('{name} is not registered')
#def step_impl(context, name):
#    context.execute_steps(f'{name} unregisters')

@then('{name} has missed a call')
async def step_impl(context, name):
    await sleep(0.5)
    user_protocol = context.sip_xport[name][1]
    assert_that(user_protocol.get_prev_rcvd('INVITE'))\
        .described_as(f'{name} checks for a missed call, INVITE').is_not_none()
    assert_that(user_protocol.get_prev_rcvd('CANCEL'))\
        .described_as(f'{name} checks for a missed call, CANCEL').is_not_none()

@then('{name}\'s phone has not rung')
async def step_impl(context, name):
    await sleep(0.5)
    user_protocol = context.sip_xport[name][1]
    assert_that(user_protocol.get_prev_rcvd('INVITE'))\
        .described_as(f'{name} checks for a missed call, INVITE').is_none()

# vi: ts=4 sw=4 et ai
