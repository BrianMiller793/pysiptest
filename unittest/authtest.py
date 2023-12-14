# vim: set ai ts=4 sw=4 expandtab:

import logging
import sys
import unittest
import urllib.request, urllib.error, urllib.parse

from pysiptest.digestauth import SipDigestAuth

# Author: Brian C. Miller
# Copyright 2017-2022, all rights reserved

# https://tools.ietf.org/html/draft-smith-sipping-auth-examples-01#section-3
# Worked examples

class TestDigestAuth(unittest.TestCase):
    """ Unit tests covering worked examples in draft, section 3. """

    def test_NoAlgoNoQop(self):
        """ 3.1 Algorithm and QOP not specified """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertFalse('cnonce' in auth_dict)
        self.assertFalse('nc' in auth_dict)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['response'], 'bf57e4e0d0bffc0fbaedce64d59add5e')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

    def test_AuthNoAlgo(self):
        """ 3.2 auth and algorithm unspecified (MD5 assumed) """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        self.assertEqual(sda._force_nonce, sda.get_new_cnonce('banana'))
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['qop'], 'auth')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['response'], '89eb0059246c02b2f6ee02c7961d5ea3')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

    def test_AuthAndMD5(self):
        """ 3.3 auth and MD5 """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['qop'], 'auth')
        self.assertEqual(auth_dict['algorithm'], 'MD5')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['response'], '89eb0059246c02b2f6ee02c7961d5ea3')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

    def test_AuthAndMD5Sess(self):
        """ 3.4 auth and MD5-Sess """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5-sess, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['qop'], 'auth')
        self.assertEqual(auth_dict['algorithm'], 'MD5-sess')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['response'], 'e4e4ea61d186d07a92c9e1f6919902e9')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

    def test_AuthIntAndMD5(self):
        """ 3.5 auth-int and MD5 """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        body_md5sum = 'c1ed018b8ec4a3b170c0921f5b564e48'
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd, body_md5sum)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['qop'], 'auth-int')
        self.assertEqual(auth_dict['algorithm'], 'MD5')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['response'], 'bdbeebb2da6adb6bca02599c2239e192')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

    def test_AuthIntAndMD5Sess(self):
        """ 3.6 auth-int and MD5-Sess """
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5-sess, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        sda._force_nonce = '0a4f113b'
        body_md5sum = 'c1ed018b8ec4a3b170c0921f5b564e48'
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd, body_md5sum)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertFalse(hdr_auth is None)
        self.assertFalse(auth_dict is None)
        self.assertEqual(auth_dict['username'], 'bob')
        self.assertEqual(auth_dict['realm'], 'biloxi.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], 'sip:bob@biloxi.com')
        self.assertEqual(auth_dict['qop'], 'auth-int')
        self.assertEqual(auth_dict['algorithm'], 'MD5-sess')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['response'], '91984da2d8663716e91554859c22ca70')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')

class TestRepeatAuthBehavior(unittest.TestCase):
    def test_auth_seq(self):
        """ Sequential auth calls should increment 'nc' and produce a new cnonce. """
        nc_values = []
        cnonce_values = []
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        nc_values.append(int(auth_dict['nc'],16))
        cnonce_values.append(auth_dict['cnonce'])

        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        nc_values.append(int(auth_dict['nc'],16))
        cnonce_values.append(auth_dict['cnonce'])

        self.assertTrue(nc_values[0] + 1 == nc_values[1])
        self.assertNotEqual(cnonce_values[0], cnonce_values[1])

    def test_md5sess_seq(self):
        """ Sequential auth calls with MD5-sess should increment 'nc' but not produce a new cnonce. """
        nc_values = []
        cnonce_values = []
        bob_pwd = 'zanzibar'
        www_authenticate = 'Digest realm="biloxi.com", qop="auth,auth-int", algorithm=MD5-sess, nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        nc_values.append(int(auth_dict['nc'],16))
        cnonce_values.append(auth_dict['cnonce'])

        hdr_auth = sda.get_auth_digest('INVITE', 'sip:bob@biloxi.com', 'bob', bob_pwd)
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        nc_values.append(int(auth_dict['nc'],16))
        cnonce_values.append(auth_dict['cnonce'])

        self.assertTrue(nc_values[0] + 1 == nc_values[1])
        self.assertEqual(cnonce_values[0], cnonce_values[1])

    def test_RFC2617_sec3_5_example(self):
        nc_values = []
        cnonce_values = []
        # doc_uri = 'http://www.nowhere.org/dir/index.html'
        doc_uri = '/dir/index.html'
        username = 'Mufasa'
        password = 'Circle Of Life'
        www_authenticate = 'Digest realm="testrealm@host.com", qop="auth,auth-int", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
        sda = SipDigestAuth()
        sda._force_nonce = '0a4f113b'
        sda.parse_challenge(www_authenticate)
        hdr_auth = sda.get_auth_digest('GET', doc_uri, username, password)
        #logging.warning(hdr_auth)

        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(
            urllib.request.parse_http_list(kv))
        self.assertEqual(auth_dict['username'], 'Mufasa')
        self.assertEqual(auth_dict['realm'], 'testrealm@host.com')
        self.assertEqual(auth_dict['nonce'], 'dcd98b7102dd2f0e8b11d0f600bfb0c093')
        self.assertEqual(auth_dict['uri'], '/dir/index.html')
        self.assertEqual(auth_dict['qop'], 'auth')
        self.assertEqual(auth_dict['nc'], '00000001')
        self.assertEqual(auth_dict['cnonce'], '0a4f113b')
        self.assertEqual(auth_dict['opaque'], '5ccc069c403ebaf9f0171e9517f40e41')
        self.assertEqual(auth_dict['response'], '6629fae49393a05397450978507c4ef1')

    def test_sofia_parse(self):
        """Test parse of Sofia stack"""
        # Note: Sofia sends UUID for nonce
        nc_values = []
        cnonce_values = []
        user_uri = 'sip:Minion.Banana'
        user = 'Minion.Banana'
        password = "hownowbrowncow123"
        www_authenticate = 'Digest realm="teo", nonce="c6b46784-82b9-4a38-8c7c-c46b50b37a60", algorithm=MD5, qop="auth"'
        sda = SipDigestAuth()
        sda.parse_challenge(www_authenticate)
        hdr_auth = sda.get_auth_digest('REGISTER', user_uri, user, password)
        # The next part is strictly for test
        _, kv = hdr_auth.split(' ', 1)
        auth_dict = urllib.request.parse_keqv_list(urllib.request.parse_http_list(kv))
        self.assertEqual(auth_dict['realm'], 'teo')
        self.assertEqual(auth_dict['nonce'], 'c6b46784-82b9-4a38-8c7c-c46b50b37a60')
        self.assertEqual(auth_dict['algorithm'], 'MD5')
        self.assertEqual(auth_dict['qop'], 'auth')
        self.assertEqual(auth_dict['uri'], user_uri)
        #self.assertEqual(auth_dict['response'], '')
        self.assertEqual(auth_dict['qop'], 'auth')
        #self.assertEqual(auth_dict['cnonce'], '')
        self.assertEqual(auth_dict['nc'], '00000001')

if __name__ == '__main__':
    unittest.main()

