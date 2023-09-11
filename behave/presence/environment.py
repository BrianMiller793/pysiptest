# vim: set ai ts=4 sw=4 expandtab:

'''Test environment setup for Behave test steps.'''

import logging
from behave import fixture, use_fixture
from behave.api.async_step import use_or_create_async_context

import os
import sys
sys.path.append(os.getenv('PYSIP_LIB_PATH'))
from sipphone import AutoAnswer, AutoReply

TEST_HOST = '192.168.0.143'
PASSWORD_UCM = 'hownowbrowncow123'
PASSWORD_DOCKER = 'hownowbrowncow123'
TEST_USERS = {
    # Receiver
    'Alice': {
        'name': 'Alice',
        'extension': '2006',
        'domain': 'teo',
        'sipuri': 'sip:2006@teo',
        'password': PASSWORD_UCM,
        'server': 'Biloxi',
        'transport': AutoAnswer},
    # Caller
    'Bob': {
        'name': 'Bob',
        'extension': '2007',
        'domain': 'teo',
        'sipuri': 'sip:2007@teo',
        'password': PASSWORD_UCM,
        'server': 'Biloxi',
        'transport': AutoAnswer},
    'Charlie': {
        'name': 'Charlie',
        'extension': '2008',
        'domain': 'teo',
        'sipuri': 'sip:2008@teo',
        'password': PASSWORD_UCM,
        'server': 'Biloxi',
        'transport': AutoAnswer}}
TEST_SERVERS = {
    'Biloxi': ('192.168.0.203', 5060),
    'Docker': ('192.168.0.153', 5060)} # Docker running with --network=host

async def init_transport(
    context, async_context, user_name, user_info):
    '''Initiate network transport, sets context.sip_xport.

    :param context: Behave test context.
    :param async_context: Async context for asyncio operations.
    :param user_name:
    :param user_info:
    '''
    logging.debug('init_transport, user_name=%s, server_name=%s',
        user_name, user_info['server'])
    transport, protocol = \
        await async_context.loop.create_datagram_endpoint(
            lambda: user_info['transport'](
                user_info=user_info,
                loop=async_context.loop),
            remote_addr=TEST_SERVERS[user_info['server']])

    if not hasattr(context, 'sip_xport'):
        context.sip_xport = {}
    context.sip_xport[user_name] = (transport, protocol)

@fixture
def udp_transport(context):
    '''Fixture to provide network transport for tests.

    :param context: Behave test context.
    '''
    logging.info('fixture udp_transport')
    async_context = use_or_create_async_context(context, 'udp_transport')

    # Create the task for the client
    for user_name in TEST_USERS.keys():
        logging.debug('fixture udp_transport, user_name=%s', user_name)
        task = async_context.loop.create_task(
            init_transport(context, async_context,
                user_name, TEST_USERS[user_name]))
        async_context.loop.run_until_complete(task)
    assert hasattr(context, 'sip_xport')

    yield getattr(context, 'sip_xport')
    logging.debug('udp_transport sip_xport.keys=%s', context.sip_xport.keys())
    for key in context.sip_xport:
        context.sip_xport[key][0].close()

@fixture
def test_host(context):
    '''Provide test user data for tests.'''
    context.test_host = TEST_HOST
    yield context.test_host

@fixture
def test_users(context):
    '''Provide test user data for tests.'''
    context.test_users = TEST_USERS
    yield context.test_users

@fixture
def test_servers(context):
    '''Provide server data for tests.`'''
    context.test_servers = TEST_SERVERS
    yield context.test_servers

def before_scenario(context, scenario):
    '''Set up test context and skip marked scenarios.'''
    # Skip all scenarios tagged with @skip
    if "skip" in scenario.effective_tags:
        scenario.skip('Marked with @skip')
        return
    use_fixture(test_host, context)
    use_fixture(test_users, context)
    use_fixture(test_servers, context)

def before_feature(context, feature): # pylint: disable=W0613
    '''Set up test context.'''
    logging.debug('before_feature:udp_transport')
    use_fixture(udp_transport, context)
