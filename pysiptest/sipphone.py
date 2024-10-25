# vim: ai ts=4 sw=4 et
'''
Protocol factory supporting SIP phone.
'''

import asyncio
import copy
import logging

from pysiptest.digestauth import SipDigestAuth
from pysiptest import support
import pysiptest.headerfield as hf
from pysiptest import sipmsg

# pylint: disable=R0904

def rtp_sockname_from_sdp(sip_msg:str) -> tuple:
    '''Construct sockname from SDP message.'''
    fields = hf.HeaderFieldValues(sip_msg)
    assert 'sdp' in fields.getfield('Content-Type')[0]
    body = sip_msg[len(sip_msg) - int(fields.getfield('Content-Length')[0]):]
    sock_ip = hf.sdp_fields(body, 'c')[0][2:].split()[-1]
    sock_addr = int(hf.sdp_fields(body, 'm')[0][2:].split()[1])
    return (sock_ip, sock_addr)

class SipPhoneUdpClient:
    '''
    Factory transport class to support SIP protocol.
    '''
    # pylint: disable=R0902
    def __init__(self, **kwargs):
        '''Initialization

        :param on_con_lost: Optional
        '''
        self.on_con_lost = kwargs['on_con_lost'] \
            if 'on_con_lost' in kwargs else None
        self.user_info = kwargs['user_info'] \
            if 'user_info' in kwargs else {}
        self.header_fields = kwargs['header_fields'] \
            if 'header_fields' in kwargs else {
                'User-Agent': 'pysip/123456_DEADBEEFCAFE',
                'Expires': 120}
        self.wait = None                    # General wait point
        self.transport = None
        self.recvd_pkts = []                # all received packets (string)
        self.sent_msgs = []                 # all sent SIP messages
        self.rcv_queue = asyncio.Queue()    # received packets for Behave
        self.state_callback = {}            # Call-ID to method for state mach
        self._cseq_in_dialog = 0
        self._cseq_out_of_dialog = 0
        self.local_addr = None              # sockname of SIP client
        self.sip_digest_auth = SipDigestAuth() # Create digest authentication

    @property
    def cseq_in_dialog(self):
        '''CSeq for in-dialog messages, autoincrements.'''
        self._cseq_in_dialog += 1
        return self._cseq_in_dialog

    @property
    def cseq_out_of_dialog(self):
        '''CSeq for out-of-dialog messages, autoincrements.'''
        self._cseq_out_of_dialog += 1
        return self._cseq_out_of_dialog

    def get_digest_auth(self, challenge:str, request_method:str, userinfo:dict, uri:str=None):
        '''Create response to challenge WWW-Authenticate or Proxy-Authenticate.

        :param challenge: Challenge value from *-Authenticate
        :param request: Request method issuing challenge
        :param userinfo: User info from environment.py
        :param uri: Destination URI
        :return Authorization: Completed Authorization header
        '''
        assert isinstance(challenge, str)
        assert isinstance(request_method, str)
        assert isinstance(userinfo, dict)

        if uri is None:
            uri = f'sip:{userinfo["domain"]}'
        self.sip_digest_auth.parse_challenge(challenge)
        return self.sip_digest_auth.get_auth_digest(request_method, uri,
            userinfo['extension'], userinfo['password'])

    def get_prev_sent(self, method:str) -> sipmsg.SipMessage:
        '''Get a copy of a previously sent request.

        :param method: Method name to match, from last sent message.
        :retval sipmsg.SipMessage: Message matching method, or None.'''
        for i in range(len(self.sent_msgs)-1, -1, -1):
            if self.sent_msgs[i].method == method:
                return copy.deepcopy(self.sent_msgs[i])
        return None

    def get_prev_rcvd(self, method:str) -> str:
        '''Get a copy of first matching previously received message.

        :param method: Method name or code, starting from last received message.
        :retval str: Matching message, or None.'''
        for i in range(len(self.recvd_pkts)-1, -1, -1):
            msg_line = self.recvd_pkts[i].splitlines()[0].split()[0:2]
            logging.debug('get_prev_rcvd:msg_line=%s', msg_line)
            if method in msg_line:
                return copy.copy(self.recvd_pkts[i])
        return None

    def get_rcvd(self, method_code:str) -> list:
        '''Get a shallow copy of all previously received messages for method or code.

        :param method: Method name or code, starting from first received message.
        :retval list: Matching messages, or empty list.'''
        return [ m for m in self.recvd_pkts
            if method_code in m.splitlines()[0].split()[0:2] ]

    def connection_made(self, transport):
        '''Base protcol: Called when a connection is made.'''
        logging.debug('SipPhoneUdpClient:connection_made')
        self.transport = transport
        self.local_addr = transport.get_extra_info('socket').getsockname()

    def connection_lost(self, exc):             # pylint: disable=W0613
        '''Base protcol: Called when a connection is lost or closed.'''
        logging.debug('SipPhoneUdpClient:connection_lost')
        if self.on_con_lost is not None:
            self.on_con_lost.set_result(True)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.
        The is put on the rcv_queue if there is no Call-ID'''
        logging.debug('SipPhoneUdpClient:datagram_received')
        sip_msg = data.decode()
        logging.debug('SipPhoneUdpClient:datagram_received: sip_msg=%s', sip_msg)
        self.recvd_pkts.append(copy.copy(sip_msg))
        sip_fields = hf.HeaderFieldValues(sip_msg)
        if sip_fields.getfield('Call-ID')[0] in self.state_callback:
            callback = self.state_callback.pop(sip_fields.getfield('Call-ID')[0])
            assert hasattr(callback, '__call__')
            logging.debug(
                'SipPhoneUdpClient:datagram_received:callback=%s, Call-ID=%s',
                callback.__name__, sip_fields.getfield('Call-ID')[0])
            callback(sip_msg)
        else:
            self.rcv_queue.put_nowait(copy.copy(sip_msg))

    def sendto(self, sip_msg: sipmsg.SipMessage):
        '''Send SIP message to UAS.'''
        logging.debug('SipPhoneUdpClient:sendto')
        logging.debug('SipPhoneUdpClient:sendto: sipmsg=%s', str(sip_msg))
        self.sent_msgs.append(sip_msg)
        self.transport.sendto(str(sip_msg).encode())

    def error_received(self, exc):
        '''Datagram protcol: Called when an error is received.'''
        logging.debug('SipPhoneUdpClient:error_received: %s', str(exc))

class RegisterUnregister(SipPhoneUdpClient):
    '''Provide registration and unregistration for endpoint.'''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_registered = False
        self.expires = 0

    def start_registration(self):
        '''State machine: Start registration for client'''
        # Send REGISTER without authentication
        if len(self.user_info) == 0:
            raise AttributeError('user_info not set')
        register = support.sip_register(self.local_addr, self.user_info,
            header_fields=self.header_fields)
        register.field('CSeq').value = self.cseq_out_of_dialog
        self.state_callback[register.field('Call_ID').value] = \
            self.register_with_auth
        self.expires = int(register.field('Expires').value)
        self.sendto(register)
        self.is_registered = False

    def register_with_auth(self, sip_msg:str):
        '''State machine: Register with Authentication.'''
        logging.debug('SipPhoneUdpClient:register_with_auth')
        assert isinstance(sip_msg, str)
        assert self.user_info is not None
        # The message *should* be a 401 or 407
        sip_fields = hf.HeaderFieldValues(sip_msg)
        assert 'WWW-Authenticate' in sip_fields.field_names

        register = self.get_prev_sent('REGISTER')
        register.hdr_fields.append(
            hf.Authorization(value=self.get_digest_auth(
                sip_fields.getfield('WWW-Authenticate')[0], register.method,
                self.user_info)))
        register.field('CSeq').value = self.cseq_out_of_dialog
        register.sort()

        self.state_callback[register.field('Call_ID').value] = self.registered
        self.sendto(register)

    def registered(self, sip_msg:str):      # pylint: disable=W0613
        '''End state for registration, sets .wait'''
        logging.debug('SipPhoneUdpClient:registered')
        code = int(sipmsg.Response.get_code(sip_msg))
        self.is_registered = 200 <= code < 300 and self.expires != 0
        # The user *should* be waiting on this.
        logging.debug('registered: self.wait= %s', 'None' if self.wait is None else 'not None')
        if self.wait is not None:
            self.wait.set_result(True)

    def start_unregistration(self):
        '''State machine: Unregister from UAS'''
        logging.debug(
            'start_unregistration: userinfo.extension=%s is_registered=%s',
            self.user_info['extension'], str(self.is_registered))
        if not self.is_registered:
            logging.debug('start_unregistration: self.wait= %s',
                'None' if self.wait is None else 'not None')
            if self.wait is not None:
                self.wait.set_result(True)
            return
        if len(self.user_info) == 0:
            raise AttributeError('user_info not set')
        sock_addr = self.transport.get_extra_info('socket').getsockname()
        unregister = support.sip_register(sock_addr, self.user_info,
            header_fields=self.header_fields)
        unregister.field('Expires').value = 0
        self.expires = 0
        unregister.field('CSeq').value = self.cseq_out_of_dialog
        # This presumes Contact field has only one address
        contact_field = unregister.field('Contact')
        contact_addr = next(iter(contact_field.contact_params))
        contact_field.contact_params[contact_addr]['expires'] = '0'
        unregister.sort()

        self.state_callback[unregister.field('Call_ID').value] = self.register_with_auth
        self.sendto(unregister)

class KeepAlive(RegisterUnregister):
    '''Provide OPTIONS keep-alive for an auto-answer endpoint.'''
    def __init__(self, **kwargs):
        '''Initialization

        :param on_con_lost:
        :param user_info:
        :param loop: Async IO loop
        '''
        super().__init__(**kwargs)
        assert 'loop' in kwargs
        self.loop = kwargs['loop']
        assert 'user_info' in kwargs
        self.user_info = kwargs['user_info']
        self.options_msg = None
        self.fire_at = None
        self.ka_interval = 60 # seconds
        self.branch = None

    def connection_made(self, transport):
        super().connection_made(transport)
        addr = transport.get_extra_info('socket').getsockname()

        # Create OPTIONS message, and save branch
        self.options_msg = support.sip_options(self.user_info, addr,
            header_fields=self.header_fields)
        self.options_msg.field('CSeq').value = self.cseq_out_of_dialog
        self.branch = self.options_msg.field('Via').via_params['branch']
        self.fire_at = self.loop.time() + self.ka_interval
        self.loop.call_at(self.fire_at, self.callback_event)

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram Protocol: intercept OK from UAS.'''
        msg_dict = hf.HeaderFieldValues(data.decode())
        if self.branch is None or \
                self.branch not in msg_dict.getfield('Via')[0]:
            logging.debug('KeepAlive:datagram_received')
            super().datagram_received(data, addr)

    def callback_event(self):
        '''This is event is fired to send the OPTIONS packet.'''
        if self.is_registered:
            self.sendto(self.options_msg)
            self.options_msg.field('CSeq').value = self.cseq_out_of_dialog
        self.fire_at += self.ka_interval
        self.loop.call_at(self.fire_at, self.callback_event)

class AutoReply(KeepAlive):
    '''Automatically reply for INFO, NOTIFY, OPTIONS and UPDATE.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_reply = ['INFO', 'NOTIFY', 'OPTIONS', 'UPDATE']

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Datagram protcol: Called when a datagram is received.'''
        logging.debug('AutoReply:datagram_received')
        sip_msg = data.decode()
        sip_method = sip_msg.split(maxsplit=1)[0]
        if sip_method in self.auto_reply:
            logging.debug('AutoReply:datagram_received: auto reply to %s', sip_method)
            # Append packet for later reference, respond, exit processing
            self.recvd_pkts.append(copy.copy(sip_msg))
            response = sipmsg.Response(status_code=200, reason_phrase='OK')
            response.method = sip_method
            response.init_from_msg(sip_msg)
            support.insert_behave_fields(self.header_fields, response)
            response.sort()
            self.sendto(response)
            return

        super().datagram_received(data, addr)

class AutoAnswer(AutoReply):
    # State machine is currently implicit between steps and handler.
    '''Answer an incoming call.
       The RTP socket has been allocated, and the client is waiting for
       an INVITE.
    '''
    # wait for INVITE
    # send 100 Trying
    # send 180 Ringing
    # send 200 OK
    # wait for ACK
    def __init__(self, **kwargs):
        '''Initialization

        :param rtp_endpoint: RTP endpoint object, for echo or playback
        '''
        super().__init__(**kwargs)
        logging.debug('AutoAnswer:INITIALIZING')
        self.rtp_endpoint = kwargs['rtp_endpoint'] \
            if 'rtp_endpoint' in kwargs else None
        self.num_rings = kwargs['rings'] if 'rings' in kwargs else 1
        self.in_a_call = False
        self.dialog = {}
        self.answer_queue = asyncio.Queue() # Packets to be sent for answer

    def datagram_received(self, data, addr):    # pylint: disable=W0613
        '''Process datagram for INVITE or ACK.'''
        sip_msg = data.decode()
        method = sip_msg.split(maxsplit=1)[0]
        fields = hf.HeaderFieldValues(sip_msg)
        logging.debug('AutoAnswer:datagram_received:method=%s', method)
        if method == 'INVITE':
            if 'call_id' not in self.dialog:
                self.dialog['call_id'] = fields.getfield('Call-ID')[0]
            if 'contact' not in self.dialog:
                self.dialog['contact'] = fields.getfield('Contact')[0].strip('<>')
            self.state_callback[fields.getfield('Call-ID')[0]] = self.answer_invite
        if method == 'BYE':
            self.state_callback[fields.getfield('Call-ID')[0]] = self.bye_dialog
        if method == 'CANCEL':
            self.state_callback[fields.getfield('Call-ID')[0]] = self.cancel_dialog

        super().datagram_received(data, addr)

    #
    # STATE MACHINE
    #
    def answer_invite(self, sip_msg:str):
        '''Send the responses for a received INVITE message.
        The RTP client must already be started.'''
        logging.debug('AutoAnswer:answer_invite:Call-ID=%s', self.dialog['call_id'])
        assert self.rtp_endpoint is not None
        # TODO: get destination RTP port
        # State:
        #  From: UAS user <sip:ext@dom>;tag=jfjfjfjf
        #  To: UAC user <sip:ext@dom>
        self.dialog['req_uri'] = sip_msg.split(maxsplit=2)[1]
        logging.debug('AutoAnswer:answer_invite:INVITE, req_uri=%s',
            self.dialog['req_uri'])
        self.rtp_endpoint.dest_addr = rtp_sockname_from_sdp(sip_msg)

        logging.debug('AutoAnswer:answer_invite:sending:Trying')
        response = sipmsg.Response(
            prev_msg=sip_msg, status_code='100', reason_phrase='Trying')
        support.insert_behave_fields(self.header_fields, response)
        response.sort()
        self.answer_queue.put_nowait(response)

        self.dialog['uas_tag'] = response.field('From').tag
        self.dialog['uac_tag'] = hf.gen_tag()
        self.dialog['uas_user'] = response.field('From').value
        self.dialog['uac_user'] = response.field('To').value

        logging.debug('AutoAnswer:answer_invite:sending:Ringing')
        for _ in range(self.num_rings):
            response = sipmsg.Response(
                prev_msg=sip_msg, status_code='180', reason_phrase='Ringing')
            response.field('To').tag = self.dialog['uac_tag']
            support.insert_behave_fields(self.header_fields, response)
            response.sort()
            self.answer_queue.put_nowait(response)

        # pylint: disable=C0301
        logging.debug('AutoAnswer:answer_invite:sending:Ringing:rtp_endpoint.begin, local_addr=%s, dest_addr=%s',
            str(self.rtp_endpoint.local_addr), str(self.rtp_endpoint.dest_addr))
        self.rtp_endpoint.begin()

        logging.debug('AutoAnswer:answer_invite:sending:OK')
        response = sipmsg.Response(
            prev_msg=sip_msg, status_code='200', reason_phrase='OK')
        response.field('To').tag = self.dialog['uac_tag']
        response.body = support.sip_sdp(username=self.user_info['name'],
            sockname=self.rtp_endpoint.local_addr)
        response.hdr_fields.append(hf.Content_Type(value='application/sdp'))
        support.insert_behave_fields(self.header_fields, response)
        response.sort()
        self.answer_queue.put_nowait(response)

        # received ACK will trigger main state machine
        self.state_callback[response.field('Call_ID').value] = self.answer_ack
        self.answer_callback()

    def answer_callback(self):
        '''Loop timer callback to simulate phone ringing behavior.'''
        if not self.answer_queue.empty():
            self.sendto(self.answer_queue.get_nowait())
            fire_at = self.loop.time() + 1 # every second
            self.loop.call_at(fire_at, self.answer_callback)

    def answer_ack(self, sip_msg:str):  # pylint: disable=W0613
        '''ACK state for received call'''
        logging.debug('AutoAnswer:answer_ack:Call-ID=%s', self.dialog['call_id'])
        self.in_a_call = True
        logging.debug('answer_ack: self.wait= %s', 'None' if self.wait is None else 'not None')
        # The user *should* be waiting on this
        if self.wait is not None:
            try:
                self.wait.set_result(True)
            except asyncio.InvalidStateError:
                logging.warning(
                    'AutoAnswer:answer_ack:set_result InvalidStateError:Call-ID=%s',
                    self.dialog['call_id'])

    def cancel(self):
        '''CANCEL active, incomplete INVITE dialog. Expect to receive OK, 487'''
        # Expect OK, expect 487
        logging.debug('AutoAnswer:cancel():expecting 200')
        invite_msg = self.get_prev_sent('INVITE')
        assert invite_msg is not None

        self.dialog['req_uri'] = invite_msg.request_uri
        cancel = sipmsg.Cancel(request_uri=invite_msg.request_uri)
        cancel.init_mandatory()
        cancel.init_from_msg(str(invite_msg))
        cancel.field('CSeq').method = cancel.method
        support.insert_behave_fields(self.header_fields, cancel)
        cancel.sort()
        self.sendto(cancel)
        self.state_callback[self.dialog['call_id']] = self.cancel_callback

    def cancel_callback(self, sip_msg:str):
        '''State machine callback for CANCEL INVITE sequence. Expect 200 response.'''
        code = sipmsg.Response.get_code(sip_msg)
        if code == '200':
            logging.debug('AutoAnswer:cancel_callback():%s expected', code)
            self.state_callback[self.dialog['call_id']] = self.cancel_callback
        elif code == '487':
            cancel_ack = support.sip_ack(sip_msg, self.user_info,
                self.local_addr, req_uri=self.dialog['req_uri'], header_fields=self.header_fields)
            support.insert_behave_fields(self.header_fields, cancel_ack)
            self.sendto(cancel_ack)
        else:
            logging.error('AutoAnswer:cancel_callback():%s unexpected', code)
        if self.wait is not None:
            try:
                self.wait.set_result(code == '200')
            except asyncio.InvalidStateError:
                logging.warning(
                    'AutoAnswer:answer_ack:set_result InvalidStateError:Call-ID=%s',
                    self.dialog['call_id'])

    def dial(self, recipient):
        '''Initiate call to recipient (dialog). RTP must be ready.'''
        logging.debug('AutoAnswer:dial()')
        invite = support.sip_invite(self.local_addr,
            self.user_info, recipient,
            self.rtp_endpoint.local_addr, request_uri=None, header_fields=self.header_fields)
        #peername = self.transport.get_extra_info('peername')
        #invite.field('Route').value = f'<sip:{peername[0]}:{peername[1]};lr>'
        self.dialog['uac_user'] = invite.field('From').value
        self.dialog['uas_user'] = invite.field('To').value
        self.dialog['req_uri'] = invite.field('To').value.split('<')[-1].strip('<>')
        logging.debug('AutoAnswer:dial:dialog:req_uri=%s',
            self.dialog['req_uri'])
        self.dialog['uac_tag'] = invite.field('From').tag
        logging.debug('AutoAnswer:dial:dialog.uac_tag=%s',
            self.dialog['uac_tag'])

        invite.field('Contact').from_string(
            f'<sip:{self.user_info["extension"]}@{self.local_addr[0]}:{self.local_addr[1]}>')
        invite.field('CSeq').value = self.cseq_out_of_dialog
        self.state_callback[invite.field('Call_ID').value] = \
            self.dial_callback
        self.dialog['call_id'] = invite.field('Call_ID').value
        self.dialog['contact'] = f'sip:{self.user_info["extension"]}@{self.local_addr[0]}'
        self.sendto(invite)

    def dial_callback(self, sip_msg:str):
        '''State machine callback for INVITE sequence. Expect response.'''
        logging.debug('AutoAnswer:dial_callback')
        code = sip_msg.split(maxsplit=2)[1]
        if code == '100':
            self.dial_100trying(sip_msg)
        elif code == '180':
            self.dial_180ringing(sip_msg)
        elif code == '181':
            self.dial_181forwarded(sip_msg)
        elif code == '182':
            self.dial_182queued(sip_msg)
        elif code == '183':
            self.dial_183sessionprogress(sip_msg)
        elif code == '200':
            self.dial_200ok(sip_msg)
        elif code == '407':
            self.dial_407proxy_auth_req(sip_msg)
        elif code == '487':
            self.dial_487requestterminated()
        else:
            logging.error('AutoAnswer:dial_callback:received %s', code)

    def dial_100trying(self, sip_msg:str):
        '''State machine callback for 100 Trying.'''
        logging.debug('AutoAnswer:dial_100trying')
        fields = hf.HeaderFieldValues(sip_msg)
        self.state_callback[fields.getfield('Call-ID')[0]] = self.dial_callback

    def dial_180ringing(self, sip_msg:str):
        '''State machine callback for 180 Ringing.'''
        logging.debug('AutoAnswer:dial_180ringing')
        fields = hf.HeaderFieldValues(sip_msg)
        self.state_callback[fields.getfield('Call-ID')[0]] = self.dial_callback

    def dial_181forwarded(self, sip_msg:str):
        '''State machine callback for 181 Call Is Being Fowarded.'''
        logging.debug('AutoAnswer:dial_181forwarded')
        fields = hf.HeaderFieldValues(sip_msg)
        self.state_callback[fields.getfield('Call-ID')[0]] = self.dial_callback

    def dial_182queued(self, sip_msg:str):
        '''State machine callback for 182 Queued.'''
        logging.debug('AutoAnswer:dial_182queued')
        fields = hf.HeaderFieldValues(sip_msg)
        self.state_callback[fields.getfield('Call-ID')[0]] = self.dial_callback

    def dial_183sessionprogress(self, sip_msg:str):
        '''State machine callback for 183 Session Progress.'''
        logging.debug('AutoAnswer:dial_183sessionprogress')
        fields = hf.HeaderFieldValues(sip_msg)
        self.state_callback[fields.getfield('Call-ID')[0]] = self.dial_callback
        self.dialog['uas_tag'] = fields.getfield('To')[0].split('=')[-1]
        self.dialog['session_id'] = fields.getfield('Session-ID')[0]

    def dial_487requestterminated(self):
        '''State machine callback for 487 Request Terminated.'''
        logging.debug('AutoAnswer:dial_487requestterminated')
        # No further processing
        if self.wait is not None:
            logging.debug('dial_487requestterminated: wait.set_result(False)')
            self.wait.set_result(False)

    def dial_407proxy_auth_req(self, sip_msg:str):
        '''State machine callback for 407 Proxy Authentication Required.'''
        logging.debug('AutoAnswer:dial_407proxy_auth_req')
        sip_fields = hf.HeaderFieldValues(sip_msg)
        # RFC 8760 - there may be more than one authenticate
        assert 'Proxy-Authenticate' in sip_fields.field_names
        # send ACK for 407
        to_field = sip_fields.getfield('To')[0]
        req_uri = to_field[to_field.find('<')+1 : to_field.find('>')]
        auth_ack = support.sip_ack(sip_msg, self.user_info,
            self.local_addr, req_uri=req_uri, header_fields=self.header_fields)
        support.insert_behave_fields(self.header_fields, auth_ack)
        self.sendto(auth_ack)

        invite = self.get_prev_sent('INVITE')
        # If the previous INVITE failed with an Authorization, fail here too
        # TODO Need propagation mechanism
        assert invite.field('Authorization') is None

        invite.field('CSeq').value = self.cseq_out_of_dialog
        invite.hdr_fields.append(
            hf.Proxy_Authorization(value=self.get_digest_auth(
                sip_fields.getfield('Proxy-Authenticate')[0],
                invite.method, self.user_info, uri=self.user_info['sipuri'])))
        invite.sort()

        self.state_callback[invite.field('Call_ID').value] = self.dial_callback
        self.sendto(invite)

    def dial_200ok(self, sip_msg:str):
        '''State machine callback for 200 OK w/SDP, respond with ACK'''
        logging.debug('AutoAnswer:dial_200ok')
        # Get destination RTP endpoint
        self.rtp_endpoint.dest_addr = rtp_sockname_from_sdp(sip_msg)
        logging.debug('AutoAnswer:dial_200ok:rtp_endpoint.begin, local_addr=%s, dest_addr=%s',
            str(self.rtp_endpoint.local_addr), str(self.rtp_endpoint.dest_addr))
        self.rtp_endpoint.begin()

        fields = hf.HeaderFieldValues(sip_msg)
        self.dialog['req_uri'] = fields.getfield('Contact')[0].strip('<>')
        logging.debug('AutoAnswer:dial_200ok:dialog:req_uri=%s', self.dialog['req_uri'])
        self.dialog['uas_tag'] = fields.getfield('To')[0].split(';')[-1].split('=')[-1]
        logging.debug('AutoAnswer:dial_200ok:dialog_tag=%s', self.dialog['uas_tag'])

        # Send ACK
        ack = support.sip_ack(sip_msg, self.user_info, self.local_addr,
            req_uri=self.dialog['req_uri'], header_fields=self.header_fields)
        support.insert_behave_fields(self.header_fields, ack)
        self.sendto(ack)
        # The user *should* be waiting on this.
        logging.debug('dial_200ok: self.wait= %s', 'None' if self.wait is None else 'not None')
        if self.wait is not None:
            logging.debug('dial_200ok: wait.set_result(True)')
            self.wait.set_result(True)

    def hangup(self):
        '''Initiate end connection. Send BYE, wait for OK.'''
        logging.debug('AutoAnswer:hangup')
        assert 'call_id' in self.dialog
        assert 'req_uri' in self.dialog
        assert 'contact' in self.dialog
        assert 'uas_tag' in self.dialog
        assert 'uac_tag' in self.dialog
        assert 'uas_user' in self.dialog
        assert 'uac_user' in self.dialog
        bye = sipmsg.Bye(request_uri=self.dialog['req_uri'])
        bye.init_mandatory()
        bye.field('Via').via_params['transport'] = 'udp'
        bye.field('Via').via_params['address'] = \
            f'{self.local_addr[0]}:{self.local_addr[1]}'
        bye.field('From').value = \
            f'{self.user_info["name"]} <{self.user_info["sipuri"]}>'
        bye.field('To').value = self.dialog['uas_user']
        bye.field('To').tag = self.dialog['uas_tag']
        bye.field('From').value = self.dialog['uac_user']
        bye.field('From').tag = self.dialog['uac_tag']
        bye.field('CSeq').value = self.cseq_out_of_dialog
        bye.field('CSeq').method = bye.method
        bye.field('Call_ID').value = self.dialog['call_id']
        bye.hdr_fields.append(hf.Contact(value=\
            f'<sip:{self.user_info["extension"]}@{self.local_addr[0]}:{self.local_addr[1]}>'))
        support.insert_behave_fields(self.header_fields, bye)
        bye.sort()

        self.sendto(bye)
        self.state_callback[self.dialog['call_id']] = self.bye_200ok

    def bye_200ok(self, sip_msg:str):   # pylint: disable=W0613
        '''Response from UAS after sending BYE.'''
        logging.debug('AutoAnswer:bye_200ok')
        self.clear_endpoint()
        # The user *should* be waiting on this.
        logging.debug('bye_200ok: self.wait= %s', 'None' if self.wait is None else 'not None')
        if self.wait is not None:
            self.wait.set_result(True)

    def bye_dialog(self, sip_msg:str):
        '''Received request from UAS to end dialog.'''
        logging.debug('AutoAnswer:bye_dialog')
        bye_resp = sipmsg.Response(prev_msg=sip_msg, status_code=200, reason_phrase='OK')
        support.insert_behave_fields(self.header_fields, bye_resp)
        bye_resp.sort()
        self.sendto(bye_resp)

        self.clear_endpoint()
        # A user may, or may not, be waiting on the BYE.
        # This can happen in the background of a task, and the `wait` may
        # be None.
        logging.debug('bye_dialog: self.wait= %s', 'None' if self.wait is None else 'not None')
        if self.wait is not None:
            self.wait.set_result(True)

    def cancel_dialog(self, sip_msg:str):
        '''Received request from UAS to cancel INVITE. Send OK, then 487'''
        logging.debug('AutoAnswer:cancel_dialog')
        self.answer_queue = asyncio.Queue() # Dump queued answering packets

        # 200 for CANCEL
        response = sipmsg.Response(prev_msg=sip_msg, status_code=200, reason_phrase='OK')
        response.init_from_msg(sip_msg)
        response.method = 'CANCEL'
        support.insert_behave_fields(self.header_fields, response)
        response.sort()
        self.sendto(response)

        # 487 for INVITE
        invite_sip = self.get_prev_rcvd('INVITE')
        response = sipmsg.Response(
            prev_msg=invite_sip, status_code=487, reason_phrase='Request Terminated')
        response.init_from_msg(invite_sip)
        response.method = 'INVITE'
        support.insert_behave_fields(self.header_fields, response)
        response.sort()
        self.sendto(response)

        # expect ACK
        fields = hf.HeaderFieldValues(sip_msg)
        call_id = fields.getfield('Call-ID')[0]
        self.state_callback[call_id] = self.cancel_ack

    def cancel_ack(self, sip_msg:str):  # pylint: disable=W0613
        '''ACK state for canceled call'''
        logging.debug('AutoAnswer:cancel_ack:Call-ID=%s', self.dialog['call_id'])
        self.in_a_call = False
        logging.debug('answer_ack: self.wait= %s', 'None' if self.wait is None else 'not None')
        # The user *should* be waiting on this
        if self.wait is not None:
            try:
                self.wait.set_result(True)
            except asyncio.InvalidStateError:
                logging.warning(
                    'AutoAnswer:answer_ack:set_result InvalidStateError:Call-ID=%s',
                    self.dialog['call_id'])

    def clear_endpoint(self):
        '''End state, clear endpoint data.'''
        logging.debug('AutoAnswer:clear_endpoint')
        self.rtp_endpoint.end()
        self.in_a_call = False
        self.dialog = {}
