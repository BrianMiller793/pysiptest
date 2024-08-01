# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
from pysiptest.sipphone import AutoAnswer

TEST_HOST = '192.168.1.115'
TEST_SERVERS = {
    'UC': ('192.168.3.70', 5060),
    'Docker': ('192.168.1.115', 5060)} # Docker running with --network=host
PASSWORD_DEFAULT = 'hownowbrowncow123'
TEST_USERS = {
    'Alice1': {
        'domain': 'teo',
        'name': 'Alice',
        'extension': '2006',
        'sipuri': 'sip:2006@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'UC',
        'transport': AutoAnswer},
    'Bob1': {
        'domain': 'teo',
        'name': 'Bob',
        'extension': '2007',
        'sipuri': 'sip:2007@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'UC',
        'transport': AutoAnswer},
    'Charlie1': {
        'domain': 'teo',
        'name': 'Charlie',
        'extension': '2002',
        'sipuri': 'sip:2002@teo',
        'password': None,
        'server': None,
        'transport': None},
    'H100': {
        'domain': 'teo',
        'name': 'H100',
        'extension': '100',
        'sipuri': 'sip:100@teo',
        'password': None,
        'server': None,
        'transport': None},
    'A200': {
        'domain': 'teo',
        'name': 'A200',
        'extension': '200',
        'sipuri': 'sip:200@teo',
        'password': None,
        'server': None,
        'transport': None}}
