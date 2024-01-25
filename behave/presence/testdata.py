# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
from pysiptest.sipphone import AutoAnswer

PASSWORD_UCM = 'hownowbrowncow123'
PASSWORD_DOCKER = 'hownowbrowncow123'
TEST_USERS = {
    # Receiver
    'Alice': {
        'domain': 'teo',
        'name': 'Alice',
        'extension': '2000',
        'sipuri': 'sip:2000@teo',
        'password': PASSWORD_UCM,
        'server': 'Docker',
        'transport': AutoAnswer},
    # Caller
    'Bob': {
        'domain': 'teo',
        'name': 'Bob',
        'extension': '2001',
        'sipuri': 'sip:2001@teo',
        'password': PASSWORD_UCM,
        'server': 'Docker',
        'transport': AutoAnswer},
    'Charlie': {
        'domain': 'teo',
        'name': 'Charlie',
        'extension': '2002',
        'sipuri': 'sip:2002@teo',
        'password': PASSWORD_UCM,
        'server': 'Docker',
        'transport': AutoAnswer}}
TEST_HOST = '192.168.0.143'
TEST_SERVERS = {
    'Biloxi': ('192.168.0.203', 5060),
    'Docker': ('192.168.0.143', 5060)} # Docker running with --network=host
