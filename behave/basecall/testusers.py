# vim: set ai ts=4 sw=4 expandtab:

'''Test data for Behave test steps.'''
import socket
import subprocess

from pysiptest.sipphone import AutoAnswer
from pysiptest.support import available_ips, get_stun_address

hostname_a = subprocess\
    .run('hostname -A', shell=True, capture_output=True, check=False)\
    .stdout.decode('ASCII')\
    .split()
TEST_LOCALHOSTNAME = '' if not hostname_a else hostname_a[0]
TEST_LOCALHOSTIP = None
if TEST_LOCALHOSTNAME:
    try:
        TEST_LOCALHOSTIP = socket.gethostbyname(TEST_LOCALHOSTNAME)
    except socket.gaierror:
        pass

if not TEST_LOCALHOSTIP:
    TEST_LOCALHOSTIP = available_ips()[0]

if '0.0.0.0' in TEST_LOCALHOSTIP:
    TEST_LOCALHOSTIP = get_stun_address()

TEST_HOSTNAME = 'nuc2.localdomain'
#TEST_HOSTNAME = 'raymes.duckdns.org'
TEST_HOSTIP = socket.gethostbyname(TEST_HOSTNAME)
TEST_SERVERS = {
    'UC': ('192.168.3.70', 5060),
    'Vanilla': ('50.106.21.108', 5080),
    'Docker': (TEST_HOSTIP, 5080)} # Docker running with --network=host
PASSWORD_DEFAULT = 'hownowbrowncow123'
server = TEST_SERVERS['Vanilla']
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
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}},
    'Dave': {
        'domain': 'teo',
        'name': 'Dave',
        'extension': '2009',
        'sipuri': 'sip:2009@teo',
        'password': PASSWORD_DEFAULT,
        'server': 'Docker',
        'transport': AutoAnswer,
        'header_fields': {
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}}}
