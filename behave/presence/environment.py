# vim: set ai ts=4 sw=4 expandtab:

'''Test environment setup for Behave test steps.'''

import csv
import logging
import os
from behave import fixture, use_fixture
from behave.api.async_step import use_or_create_async_context

from pysiptest.sipphone import AutoAnswer, AutoReply
import testdata as td

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
            remote_addr=td.TEST_SERVERS[user_info['server']])

    if not hasattr(context, 'sip_xport'):
        context.sip_xport = {}
    context.sip_xport[user_name] = (transport, protocol)

async def register_user(context, name):
    '''Register a user.

    :param context: Behave test context.
    :param name: User name to unregister.
    '''
    user_protocol = context.sip_xport[name][1]

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_registration()
    await user_protocol.wait
    is_registered = user_protocol.wait.result()
    user_protocol.wait = None
    return is_registered

async def unregister_user(context, name):
    '''Unregister a user after a scenario.

    :param context: Behave test context.
    :param name: User name to unregister.
    '''
    user_protocol = context.sip_xport[name][1]

    user_protocol.wait = context.udp_transport.loop.create_future()
    user_protocol.start_unregistration()
    await user_protocol.wait
    user_protocol.wait = None

@fixture
def udp_transport(context):
    '''Fixture to provide network transport for tests.

    :param context: Behave test context.
    '''
    logging.info('fixture udp_transport')
    async_context = use_or_create_async_context(context, 'udp_transport')

    # Create the task for the client
    for user_name in td.TEST_USERS:
        logging.debug('fixture udp_transport, user_name=%s', user_name)
        task = async_context.loop.create_task(
            init_transport(context, async_context,
                user_name, td.TEST_USERS[user_name]))
        async_context.loop.run_until_complete(task)
    assert hasattr(context, 'sip_xport')

    yield getattr(context, 'sip_xport')
    logging.debug('udp_transport sip_xport.keys=%s', context.sip_xport.keys())
    for key in context.sip_xport:
        context.sip_xport[key][0].close()

@fixture
def test_host(context):
    '''Provide test user data for tests.'''
    context.test_host = td.TEST_HOST
    yield context.test_host

@fixture
def test_users(context):
    '''Provide test user data for tests.'''
    context.test_users = td.TEST_USERS
    yield context.test_users

@fixture
def test_servers(context):
    '''Provide server data for tests.`'''
    context.test_servers = td.TEST_SERVERS
    yield context.test_servers

###########################################
def import_init_transport(context, import_file_name):
    '''Import user from Teo CSV and initialize user network transport.'''
    async_context = use_or_create_async_context(context, 'udp_transport')
    with open(import_file_name, 'r', encoding='utf-8') as ucusers:
        reader = csv.DictReader(ucusers)
        for row in reader:
            user_name = row['username']
            td.TEST_USERS[user_name] = {
                'domain': 'teo',
                'name': row['username'],
                'extension': row['listedPhoneNumber'],
                'sipuri': f'sip:{row["listedPhoneNumber"]}@teo',
                'password': td.PASSWORD_UCM,
                'server': 'Docker',
                'transport': AutoAnswer}

            task = async_context.loop.create_task(
                init_transport(context, async_context,
                    user_name, td.TEST_USERS[user_name]))
            async_context.loop.run_until_complete(task)

###########################################
def before_tag(context, tag):
    '''Perform actions specific to tags.'''
    if tag.startswith('import.'):
        import_file_name = tag.replace('import.', '', 1)
        assert os.path.isfile(import_file_name)
        import_init_transport(context, import_file_name)

def before_scenario(context, scenario):
    '''Set up test context and skip marked scenarios.'''
    # Skip all scenarios tagged with @skip
    if 'skip' in scenario.effective_tags:
        scenario.skip('Marked with @skip')
        return

    use_fixture(test_host, context)
    use_fixture(test_users, context)
    use_fixture(test_servers, context)

def before_feature(context, feature): # pylint: disable=W0613
    '''Set up test context.'''
    logging.debug('before_feature:udp_transport')
    use_fixture(udp_transport, context)

# pylint: disable=W0613
def after_feature(context, feature):
    '''Unregister users after feature completed.'''
    async_context = use_or_create_async_context(context, 'udp_transport')
    for user_name in td.TEST_USERS:
        logging.debug('fixture udp_transport, user_name=%s', user_name)
        task = async_context.loop.create_task(
            unregister_user(context, user_name))
        async_context.loop.run_until_complete(task)
