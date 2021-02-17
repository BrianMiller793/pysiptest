"""
digestauth.py

This class provides digest authentication per RFC 2617 for SIP RFC 3261.
"""
# pylint: disable=invalid-name,too-many-arguments,too-many-branches,fixme
# TODO: RFC 7616

import hashlib
import os
import time
import urllib.request
import urllib.error
import urllib.parse

class SipDigestAuth():
    """ Provide digest authentication for SIP authentication challenge. """
    def __init__(self):
        self.__A1 = None
        self.__H = None
        self._force_nonce = None
        self.nonce_count = 0
        self.cnonce = None
        self.challenge = {}

    def reset_nonce_count(self):
        """ Reset Nonce Count for digest. """
        self.nonce_count = 0

    def need_body_hash(self):
        """ Does digest need an MD5 hash of the request body for auth-int. """
        return 'qop' in self.challenge and 'auth-int' in self.challenge['qop']

    def has_qop(self):
        """ Is the quality of protection set. """
        return 'qop' in self.challenge

    def is_algorithm_supported(self):
        """ Is the hash algorithm requested by the server supported. """
        return self.__H is not None

    def get_qop_type(self):
        """ Get the quality of protection value. """
        return self.challenge['qop'] if 'qop' in self.challenge else None

    def get_new_cnonce(self, nonce):
        """ Get the client-supplied cnonce value. """
        dig = hashlib.sha256(
            ("%u:%s:%s:%s" % (self.nonce_count, nonce, time.ctime(), \
	    os.urandom(64).hex())).encode('ascii')).hexdigest()
        return dig[:32] if self._force_nonce is None else self._force_nonce

    def parse_challenge(self, challenge):
        """ Parse WWW-Authenticate response header (3.2.1). """
        # challenge        =  "Digest" digest-challenge
        # digest-challenge  = 1#( realm | [ domain ] | nonce |
        #                   [ opaque ] |[ stale ] | [ algorithm ] |
        #                   [ qop-options ] | [auth-param] )
        # domain            = "domain" "=" <"> URI ( 1*SP URI ) <">
        # URI               = absoluteURI | abs_path
        # nonce             = "nonce" "=" nonce-value
        # nonce-value       = quoted-string
        # opaque            = "opaque" "=" quoted-string
        # stale             = "stale" "=" ( "true" | "false" )
        # algorithm         = "algorithm" "=" ( "MD5" | "MD5-sess" | token )
        # qop-options       = "qop" "=" <"> 1#qop-value <">
        # qop-value         = "auth" | "auth-int" | token
        _, challenge = challenge.split(' ', 1)
        self.challenge = urllib.request.parse_keqv_list(urllib.request.parse_http_list(challenge))
        if 'algorithm' not in list(self.challenge.keys()):
            self.challenge['algorithm'] = 'MD5'

        # RFC 7616
        if 'MD5' in self.challenge['algorithm']:
            self.__H = lambda d: hashlib.md5(d.encode('ascii')).hexdigest()
        elif 'SHA-256' in self.challenge['algorithm']:
            self.__H = lambda d: hashlib.sha256(d.encode('ascii')).hexdigest()
        elif 'SHA-512-256' in self.challenge['algorithm']:
            self.__H = lambda d: hashlib.sha512(d.encode('ascii')).hexdigest()

    def get_auth_digest(self, sip_method, digest_uri, username, password, request_body_hash=None):
        """
        Create an MD5 authentication digest, per RFC 2617.

        :param sip_method: The SIP method, such as REGISTER or INVITE
        :param digest_uri: The SIP URI from the request, e.g., sip:bob@biloxi.com
        :param username: The user name to authenticate, e.g., bob
        :param password: The password for the user.
        :param request_body_hash: Optional MD5 sum of request body, required for qop="auth-int".
        """
        # credentials      = "Digest" digest-response
        # digest-response  = 1#( username | realm | nonce | digest-uri
        #                    | response | [ algorithm ] | [cnonce] |
        #                    [opaque] | [message-qop] |
        #                    [nonce-count]  | [auth-param] )
        # username         = "username" "=" username-value
        # username-value   = quoted-string
        # digest-uri       = "uri" "=" digest-uri-value
        # digest-uri-value = request-uri   ; As specified by HTTP/1.1
        # message-qop      = "qop" "=" qop-value
        # cnonce           = "cnonce" "=" cnonce-value
        # cnonce-value     = nonce-value
        # nonce-count      = "nc" "=" nc-value
        # nc-value         = 8LHEX
        # response         = "response" "=" request-digest
        # request-digest   = <"> 32LHEX <">
        # LHEX             =  "0" | "1" | "2" | "3" |
        #                     "4" | "5" | "6" | "7" |
        #                     "8" | "9" | "a" | "b" |
        #                     "c" | "d" | "e" | "f"
        if sip_method is None or digest_uri is None or username is None or password is None:
            return None
        if not self.is_algorithm_supported():
            return None

        KD = lambda s, d: self.__H("%s:%s" % (s, d))
        A1_Value = lambda: '%s:%s:%s' % (username, self.challenge['realm'], password)
        self.nonce_count = self.nonce_count + 1
        nc_value = '%08x' % self.nonce_count

        # For session digest, the A1 value is set just once
        if '-sess' in self.challenge['algorithm'] and self.__A1 is None:
            self.cnonce = self.get_new_cnonce(self.challenge['nonce'])
            self.__A1 = self.__H(A1_Value()) + ':' + self.challenge['nonce'] + ':' + self.cnonce
        else:
            self.__A1 = A1_Value()

        A2 = '%s:%s' % (sip_method, digest_uri)
        # RFC 3261, 22.4, #8, must set QOP if cnonce is required by algorithm
        if self.cnonce is not None and 'qop' not in self.challenge:
            self.challenge['qop'] = "auth"

        if 'qop' in self.challenge:
            if 'auth-int' in self.challenge['qop'] and request_body_hash is not None:
                self.challenge['qop'] = 'auth-int'
                A2 = '%s:%s:%s' % (sip_method, digest_uri, request_body_hash)
            else:
                self.challenge['qop'] = 'auth'

            # Get new cnonce value for non-session authentication
            if '-sess' not in self.challenge['algorithm']:
                self.cnonce = self.get_new_cnonce(self.challenge['nonce'])
            request_digest = KD(self.__H(self.__A1), "%s:%s:%s:%s:%s" % \
                (self.challenge['nonce'], nc_value, self.cnonce,
                 self.challenge['qop'], self.__H(A2)))
        else:
            request_digest = KD(self.__H(self.__A1), \
                "%s:%s" % (self.challenge['nonce'], self.__H(A2)))

        digest = 'Digest username="%s", realm="%s", nonce="%s", uri="%s", response="%s"' % \
            (username, self.challenge['realm'], self.challenge['nonce'],
             digest_uri, request_digest)

        if 'qop' in self.challenge:
            digest = '%s, qop=%s, cnonce="%s", nc=%s' % \
            (digest, self.challenge['qop'], self.cnonce, nc_value)
        if 'opaque' in self.challenge:
            digest = '%s, opaque="%s"' % (digest, self.challenge['opaque'])
        if 'algorithm' in self.challenge:
            digest = '%s, algorithm=%s' % (digest, self.challenge['algorithm'])

        return digest

# pylint: enable=invalid-name,too-many-arguments,too-many-branches,fixme
