# vim: set ai ts=4 sw=4 expandtab:

import logging
import unittest
import sys

import pysiptest.headerfield as hf
from pysiptest import sipmsg
from pysiptest import support

USERDATA = {
    'domain': 'teo',
    'name': 'auser',
    'extension': '1234',
    'sipuri': 'sip:1234@domain',
    'password': 'badpassword',
    'server': 'serverName',
    'transport': None,
    'header_fields': {
        'Session-Expires': '1800',
        'Min-SE': '1800',
        'User-Agent': 'pysip/123456_DEADBEEFCAFE'}}

class TestHeaderField(unittest.TestCase):
    def test_behave_fields_sipmsgRegister(self):
        message = sipmsg.Register()
        message.init_mandatory()
        first_value = 'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE'
        second_value = 'ACK,BYE,CANCEL,INVITE,NOTIFY,OPTIONS,PUBLISH,UPDATE,REFER'
        behave_headers = {'Allow': second_value}

        num_headers = len(message.hdr_fields)
        assert message.field('Allow') is None

        message.hdr_fields.append(hf.Allow(value=first_value))
        assert len(message.hdr_fields) > num_headers

        num_headers = len(message.hdr_fields)
        assert message.field('Allow') is not None
        assert message.field('Allow').value == first_value

        support.insert_behave_fields(behave_headers, message)
        assert len(message.hdr_fields) == num_headers
        assert message.field('Allow').value == second_value
        assert num_headers == 8

    def test_behave_fields_supportSipInvite(self):
        msg_dflt = support.sip_invite(('1.2.3.4', 1234), USERDATA, USERDATA, ('5.6.7.8', 5678))
        allow_headers = [h for h in msg_dflt.hdr_fields if str(h).startswith('Allow:')]
        assert len(allow_headers) == 1

        second_value = 'ACK,BYE,CANCEL,INVITE,NOTIFY,OPTIONS,PUBLISH,UPDATE,REFER'
        behave_headers = {'Allow': second_value}
        message = support.sip_invite(('1.2.3.4', 1234), USERDATA, USERDATA, ('5.6.7.8', 5678), header_fields=behave_headers)
        allow_headers = [h for h in message.hdr_fields if str(h).startswith('Allow:')]
        assert len(allow_headers) == 1
        assert message.field('Allow').value == second_value

    def test_behave_fields_sipmsgInvite(self):
        first_value = 'ACK, BYE, CANCEL, INFO, INVITE, MESSAGE, NOTIFY, OPTIONS, REFER, SUBSCRIBE, UPDATE'
        second_value = 'ACK,BYE,CANCEL,INVITE,NOTIFY,OPTIONS,PUBLISH,UPDATE,REFER'
        behave_headers = {'Allow': second_value, 'Allow-Events': 'presence,dialog,message-summary,refer'}

        message = sipmsg.Invite()
        message.init_mandatory()
        initial_num_hdrs = len(message.hdr_fields)
        assert message.field('Allow') is None
        assert message.field('Allow-Events') is None

        message.hdr_fields.append(hf.Allow(value=first_value))
        assert len(message.hdr_fields) == initial_num_hdrs + 1
        assert message.field('Allow') is not None
        assert message.field('Allow').value == first_value

        support.insert_behave_fields(behave_headers, message)
        assert message.field('Allow') is not None
        assert message.field('Allow').value == second_value
        assert len(message.hdr_fields) == initial_num_hdrs + len(behave_headers)

if __name__ == '__main__':
    unittest.main()
