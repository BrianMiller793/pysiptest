# vim: set ai ts=4 sw=4 expandtab:

'''Test environment setup for Behave test steps.'''

import csv
import logging
import os
import socket

from pysiptest.sipphone import AutoAnswer
from behave import fixture, use_fixture
from behave.api.async_step import use_or_create_async_context
import testusers as td

# Aastra
# There is no device at the following local network address
# pylint: disable=W0603
ROUTE_BOGUS_ADDR = ('64.19.65.25', 2525)
SIPVIA_BOGUS_ADDR = ('192.168.4.214', 4242)

async def init_udp_transport(
    context, async_context, user_name, user_info):
    '''Initiate network transport, sets context.sip_xport.

    :param context: Behave test context.
    :param async_context: Async context for asyncio operations.
    :param user_name:
    :param user_info:
    '''
    global ROUTE_BOGUS_ADDR
    logging.debug('init_udp_transport, user_name=%s, server_name=%s, addr=%s',
        user_name, user_info['server'], td.TEST_SERVERS[user_info['server']])
    aastra_route_addr = ROUTE_BOGUS_ADDR if user_name == 'x_wunderbaum' \
        else td.TEST_SERVERS[user_info['server']]
    aastra_sip_addr = SIPVIA_BOGUS_ADDR if user_name == 'x_wunderbaum' \
        else None
    transport, protocol = \
        await async_context.loop.create_datagram_endpoint(
            lambda: user_info['transport'](
                user_info=user_info,
                loop=async_context.loop,
                header_fields=user_info['header_fields'],
                keepalive=True,
                ka_refresh=20,
                route_addr=aastra_route_addr,
                sip_local_addr=aastra_sip_addr),
            remote_addr=td.TEST_SERVERS[user_info['server']])
    ROUTE_BOGUS_ADDR = (ROUTE_BOGUS_ADDR[0], ROUTE_BOGUS_ADDR[1]+5)

    if not hasattr(context, 'sip_xport'):
        context.sip_xport = {}
    context.sip_xport[user_name] = (transport, protocol)
    # Testing Aastra and rules
    logging.debug('init_udp_transport:sip_xport..sip_local_addr=%s',
        context.sip_xport[user_name][1].sip_local_addr)
    await register_user(context, user_name)

async def init_tcp_transport(
    context, async_context, user_name, user_info):
    '''Initiate network transport, sets context.sip_xport.

    :param context: Behave test context.
    :param async_context: Async context for asyncio operations.
    :param user_name:
    :param user_info:
    '''
    global ROUTE_BOGUS_ADDR
    logging.debug('init_tcp_transport, user_name=%s, server_name=%s, addr=%s',
        user_name, user_info['server'], td.TEST_SERVERS[user_info['server']])
    aastra_route_addr = ROUTE_BOGUS_ADDR if user_name == 'x_wunderbaum' \
        else td.TEST_SERVERS[user_info['server']]
    aastra_sip_addr = SIPVIA_BOGUS_ADDR if user_name == 'x_wunderbaum' \
        else None
    transport, protocol = \
        await async_context.loop.create_connection(
            lambda: user_info['transport'](
                user_info=user_info,
                loop=async_context.loop,
                header_fields=user_info['header_fields'],
                keepalive=True,
                ka_refresh=20,
                route_addr=aastra_route_addr,
                sip_local_addr=aastra_sip_addr),
            host=td.TEST_SERVERS[user_info['server']][0],
            port=td.TEST_SERVERS[user_info['server']][1],
            flags=socket.TCP_NODELAY)
    ROUTE_BOGUS_ADDR = (ROUTE_BOGUS_ADDR[0], ROUTE_BOGUS_ADDR[1]+5)

    if not hasattr(context, 'sip_xport'):
        context.sip_xport = {}
    context.sip_xport[user_name] = (transport, protocol)
    # Testing Aastra and rules
    logging.debug('init_tcp_transport:sip_xport..sip_local_addr=%s',
        context.sip_xport[user_name][1].sip_local_addr)
    await register_user(context, user_name)

async def register_user(context, name):
    '''Register a user.

    :param context: Behave test context.
    :param name: User name to unregister.
    '''
    user_protocol = context.sip_xport[name][1]

    user_protocol.wait = context.net_transport.loop.create_future()
    user_protocol.start_registration(expires=600)
    await user_protocol.wait
    user_protocol.wait = None
    logging.debug('register_user:%s:is_registered=%s', name, user_protocol.is_registered)

async def unregister_user(context, name):
    '''Unregister a user after a scenario.

    :param context: Behave test context.
    :param name: User name to unregister.
    '''
    user_protocol = context.sip_xport[name][1]
    logging.debug('unregister_user:%s:is_registered=%s', name, user_protocol.is_registered)
    if user_protocol.is_registered:
        user_protocol.wait = context.net_transport.loop.create_future()
        user_protocol.start_unregistration()
        await user_protocol.wait
        user_protocol.wait = None

@fixture
def net_transport(context):
    '''Fixture to provide network transport for tests.

    :param context: Behave test context.
    '''
    logging.info('fixture net_transport')
    async_context = use_or_create_async_context(context, 'net_transport')

    # Create the task for the client
    for user_key, user in td.TEST_USERS.items():
        if user['password'] is not None:
            logging.debug('fixture net_transport, user=%s', user['name'])
            task = async_context.loop.create_task(
                init_udp_transport(context, async_context,
                    user_key, user))
            async_context.loop.run_until_complete(task)
    assert hasattr(context, 'sip_xport')

    yield getattr(context, 'sip_xport')
    logging.debug('net_transport sip_xport.keys=%s', context.sip_xport.keys())
    for xport in context.sip_xport.values():
        xport[0].close()

@fixture
def test_hostname(context):
    '''Provide test user data for tests.'''
    logging.debug('context.test_hostname=%s', td.TEST_HOSTNAME)
    context.test_hostname = td.TEST_HOSTNAME
    yield context.test_hostname

@fixture
def test_hostip(context):
    '''Provide test user data for tests.'''
    logging.debug('context.test_hostip=%s', td.TEST_HOSTIP)
    context.test_hostip = td.TEST_HOSTIP
    yield context.test_hostip

@fixture
def test_localhostip(context):
    '''Provide test user data for tests.'''
    logging.debug('context.test_localhostip=%s', td.TEST_LOCALHOSTIP)
    context.test_localhostip = td.TEST_LOCALHOSTIP
    yield context.test_localhostip

@fixture
def test_localhostname(context):
    '''Provide test user data for tests.'''
    logging.debug('context.test_localhostname=%s', td.TEST_LOCALHOSTNAME)
    context.test_localhostname = td.TEST_LOCALHOSTNAME
    yield context.test_localhostname

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
def import_init_udp_transport(context, import_file_name):
    '''Import user from Teo CSV and initialize user network transport.'''
    async_context = use_or_create_async_context(context, 'net_transport')
    with open(import_file_name, 'r', encoding='utf-8') as ucusers:
        reader = csv.DictReader(ucusers)
        for row in reader:
            user_name = row['username']
            td.TEST_USERS[user_name] = {
                'domain': 'teo',
                'name': row['username'],
                'extension': row['listedPhoneNumber'],
                'sipuri': f'sip:{row["listedPhoneNumber"]}@teo',
                'password': td.PASSWORD_DEFAULT,
                'server': 'Docker',
                'transport': AutoAnswer}

            task = async_context.loop.create_task(
                init_udp_transport(context, async_context,
                    user_name, td.TEST_USERS[user_name]))
            async_context.loop.run_until_complete(task)

###########################################
def before_tag(context, tag):
    '''Perform actions specific to tags.'''
    if tag.startswith('import.'):
        import_file_name = tag.replace('import.', '', 1)
        assert os.path.isfile(import_file_name)
        import_init_udp_transport(context, import_file_name)

def before_scenario(context, scenario):
    '''Set up test context and skip marked scenarios.'''
    # Skip all scenarios tagged with @skip
    if 'skip' in scenario.effective_tags:
        scenario.skip('Marked with @skip')
        return

    use_fixture(test_localhostip, context)
    use_fixture(test_localhostname, context)
    use_fixture(test_hostname, context)
    use_fixture(test_hostip, context)
    use_fixture(test_users, context)
    use_fixture(test_servers, context)

def before_feature(context, feature): # pylint: disable=W0613
    '''Set up test context.'''
    logging.debug('before_feature:net_transport')
    use_fixture(net_transport, context)

# pylint: disable=W0613
def after_feature(context, feature):
    '''Unregister users after feature completed.'''
    logging.debug('after_feature')
    async_context = use_or_create_async_context(context, 'net_transport')
    for user_key, user in td.TEST_USERS.items():
        logging.debug('after_feature, user=%s', user_key)
        if user['password'] is not None:
            if hasattr(context, 'sip_xport') and \
                hasattr(context.sip_xport[user_key][1], 'rtp_endpoint') and \
                context.sip_xport[user_key][1].rtp_endpoint:
                logging.debug('after_feature, context rtp_endpoint.end()')
                context.sip_xport[user_key][1].rtp_endpoint.end()
            logging.debug('after_feature, unregister user=%s', user_key)
            task = async_context.loop.create_task(
                unregister_user(context, user_key))
            async_context.loop.run_until_complete(task)
