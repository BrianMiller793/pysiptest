# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
from pysiptest.sipphone import AutoAnswer

TEST_HOST = '192.168.1.115'
TEST_SERVERS = {
    'UC': ('192.168.3.70', 5060),
    'Docker': ('192.168.1.115', 5060)} # Docker running with --network=host
PASSWORD_DEFAULT = 'hownowbrowncow123'
TEST_USERS = {
    'Alice': {
        'domain': 'teo',
        'name': 'Alice',
        'extension': '2006',
        'sipuri': 'sip:2006@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer,
        'header_fields': {
            'Session-Expires': '1800',
            'Min-SE': '1800',
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}},
    'Bob': {
        'domain': 'teo',
        'name': 'Bob',
        'extension': '2007',
        'sipuri': 'sip:2007@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer,
        'header_fields': {
            'Session-Expires': '1800',
            'Min-SE': '1800',
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}},
    'Charlie': {
        'domain': 'teo',
        'name': 'Charlie',
        'extension': '2008',
        'sipuri': 'sip:2008@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer,
        'header_fields': {
            'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def'}},
    'Dave': {
        'domain': 'teo',
        'name': 'Dave',
        'extension': '2009',
        'sipuri': 'sip:2009@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer,
        'header_fields': {
            'User-Agent': 'Aastra 400',
            'Supported': '199,timer',
            'Min-SE': '1800',
            'P-Preferred-Identity': '"Dave" <sip:2009@teo>',
            'P-Early-Media': 'supported',
            'Privacy': 'none',
            'Session-Expires': '1800'}},
    'H100': { # Hunt
        'domain': 'teo',
        'name': 'H100',
        'extension': '100',
        'sipuri': 'sip:100@teo',
        'password': None,
        'server': None,
        'transport': None,
        'header_fields': {
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}},
    'A200': { # Auto Attendant
        'domain': 'teo',
        'name': 'A200',
        'extension': '200',
        'sipuri': 'sip:200@teo',
        'password': None,
        'server': None,
        'transport': None,
        'header_fields': {
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}}}
