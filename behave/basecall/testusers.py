# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
import socket
import subprocess

from pysiptest.sipphone import AutoAnswer
from pysiptest.support import available_ips

hostname_a = subprocess\
    .run('hostname -A', shell=True, capture_output=True, check=False)\
    .stdout.decode('ASCII')\
    .split()
TEST_LOCALHOSTNAME = '' if not hostname_a else hostname_a[0]
try:
    TEST_LOCALHOSTIP = socket.gethostbyname(TEST_LOCALHOSTNAME)
except socket.gaierror:
    TEST_LOCALHOSTIP = available_ips()[0]

TEST_HOSTNAME = 'nuc2.localdomain'
TEST_HOSTIP = socket.gethostbyname(TEST_HOSTNAME)
TEST_SERVERS = {
    'UC': ('192.168.3.70', 5060),
    'Docker': (TEST_HOSTIP, 5080)} # Docker running with --network=host
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
            'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def'}},
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
            'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def',
            'Allow': 'ACK,BYE,CANCEL,INVITE,NOTIFY,OPTIONS,PUBLISH,UPDATE,REFER',
            'Supported': '199,timer',
            'P-Preferred-Identity': '"Dave" <sip:2009@teo>',
            'P-Early-Media': 'supported',
            'Privacy': 'none',
            'Min-SE': '1800',
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
