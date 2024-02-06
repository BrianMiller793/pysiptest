# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
from pysiptest.sipphone import AutoAnswer

TEST_HOST = '192.168.0.143'
TEST_SERVERS = {
    'UC': ('192.168.0.203', 5060),
    'Docker': ('192.168.0.143', 5060)} # Docker running with --network=host
PASSWORD_DEFAULT = 'hownowbrowncow123'
TEST_USERS = {
    'Alice': {
        'domain': 'teo',
        'name': 'Alice',
        'extension': '2000',
        'sipuri': 'sip:2000@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer},
    'Bob': {
        'domain': 'teo',
        'name': 'Bob',
        'extension': '2001',
        'sipuri': 'sip:2001@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer},
    'Charlie': {
        'domain': 'teo',
        'name': 'Charlie',
        'extension': '2002',
        'sipuri': 'sip:2002@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer}}
