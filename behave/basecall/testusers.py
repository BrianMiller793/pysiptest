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

#TEST_HOSTNAME = 'nuc2.localdomain'
TEST_HOSTNAME = 'raymes.duckdns.org'
TEST_HOSTIP = socket.gethostbyname(TEST_HOSTNAME)
TEST_SERVERS = {
    'UC': ('192.168.3.70', 5060),
    'Vanilla': ('50.106.21.108', 5080),
    'Docker': (TEST_HOSTIP, 5080)} # Docker running with --network=host
PASSWORD_DEFAULT = 'hownowbrowncow123'
server = TEST_SERVERS['Docker']
TEST_USERS = {
    'Alice': {
        'domain': server[0],
        'name': 'Alice',
        'extension': '1000',
        'sipuri': f'sip:1000@{server[0]}',
        'password': PASSWORD_DEFAULT,
        'server': 'Vanilla',
        'transport': AutoAnswer,
        'header_fields': {
            'Session-Expires': '1800',
            'Min-SE': '1800',
            'User-Agent': 'pysip/123456_DEADBEEFCAFE'}},
    'Bob': {
        'domain': server[0],
        'name': 'Bob',
        'extension': '1001',
        'sipuri': f'sip:1001@{server[0]}',
        'password': PASSWORD_DEFAULT,
        'server': 'Vanilla',
        'transport': AutoAnswer,
        'header_fields': {
            'Session-Expires': '1800',
            'Min-SE': '1800',
            'Supported': '199,timer',
            'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def'}},
    'Charlie': {
        'domain': server[0],
        'name': 'Charlie',
        'extension': '1002',
        'sipuri': f'sip:1002@{server[0]}',
        'password': PASSWORD_DEFAULT,
        'server': 'Vanilla',
        'transport': AutoAnswer,
        'header_fields': {
            'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def'}},
    'Dave': {
        'domain': server[0],
        'name': 'Dave',
        'extension': '1003',
        'sipuri': f'sip:1003@{server[0]}',
        'password': PASSWORD_DEFAULT,
        'server': 'Vanilla',
        'transport': AutoAnswer,
        'header_fields': {
            'User-Agent': 'Aastra 400',
            #'User-Agent': 'Teo Teo Fir V2 2.12.16.17.1 123abc456def',
            'Allow': 'ACK,BYE,CANCEL,INVITE,NOTIFY,OPTIONS,PUBLISH,UPDATE,REFER',
            'Supported': '199,timer',
            'P-Preferred-Identity': f'"Dave" <sip:1003@{server[0]}>',
            'P-Early-Media': 'supported',
            'Privacy': 'none',
            'Min-SE': '1800',
            'Session-Expires': '1800'}}}
