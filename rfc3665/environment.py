# vim: set ai ts=4 sw=4 expandtab:
# pylint: disable=W0613

'''Test environment setup for Behave test steps.'''

import logging
from behave import fixture, use_fixture
from behave.api.async_step import use_or_create_async_context
from steps.sipphone import SipPhoneUdpClient

TEST_USERS = {
    'Bob': ('Bob.Newhart', '1234', '@dr3amWithin@drEAm'),
    'NoSuchUser': ('NoSuch.User', '9999', 'NoAccount')}
TEST_SERVERS = {
    'Biloxi': ('192.168.0.156', 5060)}

async def init_transport(context, async_context, on_con_lost):
    '''Initiate network transport, sets context.sip_xport.

    :param context: Behave test context.
    :param async_context: Async context for asyncio operations.
    :param on_con_lost: Future for signaling loss of connection.
    '''
    logging.info('init_transport')
    transport, protocol = \
        await async_context.loop.create_datagram_endpoint(
            lambda: SipPhoneUdpClient(on_con_lost),
            remote_addr=TEST_SERVERS['Biloxi'])
    context.sip_xport = (transport, protocol)

@fixture
def udp_transport(context):
    '''Fixture to provide network transport for tests.

    :param context: Behave test context.
    '''
    logging.info('fixture udp_transport')
    async_context = use_or_create_async_context(context, 'udp_transport')
    on_con_lost = async_context.loop.create_future()

    # Create the task for the client
    task = async_context.loop.create_task(
        init_transport(context, async_context, on_con_lost))
    async_context.loop.run_until_complete(task)
    assert hasattr(context, 'sip_xport')

    yield getattr(context, 'sip_xport')
    context.sip_xport[0].close()

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
    use_fixture(test_users, context)
    use_fixture(test_servers, context)

def before_feature(context, feature):
    '''Set up test context.'''
    use_fixture(udp_transport, context)
