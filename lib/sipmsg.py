""" Provides partial implementation of RFC 3261, for UAC and UAS. """
# pylint: disable=too-few-public-methods,too-many-ancestors,super-with-arguments,unused-argument,useless-super-delegation
# vim: set ai ts=4 sw=4 expandtab:

import logging
import uuid
#import string
import headerfield as hf

class SipMessage():
    """ Minimum SIP Request header """

    # Branch: Value shall be unique per request in space and time,
    #         except for CANCEL (same branch as request it cancels) and
    #         ACK for non-2xx response as the INVITE it acknowleges.
    # RFC 5626: Managing Client-Initiated Connections in SIP
    # RFC 6026: Correct Transaction Handling for 2xx Responses to SIP INVITE
    # RFC 6141: Re-INVITE and Target-Refresh Request Handling in SIP
    # RFC 7621: SIP-Specific Event Notification
    # RFC 6878: "Priority" Header Field

    # ('', None),                 # p.26, 7 SIP Messages, start-line

    def __init__(self):
        """
        Initialize a SIP message, p.26, section 7

        Parameters:
        method: Name of request method
        request_uri: Request URI value
        status_code: Response code
        reason_phrase: Common phrase describing code.
        """
        self.sip_version = 'SIP/2.0' # p.28
        self.transport = None
        self.hdr_fields = []    # List of fields, may be ordered
        self.body = None
        self.cseq = 1           # 8.1.1.5 CSeq
        self.call_id = str(uuid.uuid4())

    def field(self, field_name):
        """Return the field object by name, or None."""
        hdr_field = [f
            for f in self.hdr_fields if f.__class__.__name__ == field_name]
        return hdr_field[0] if len(hdr_field) == 1 else None

    def init_valid(self):
        """ Initialize with all valid header fields. """
        self.hdr_fields = hf.factory_valid_fields(self)

    def init_mandatory(self):
        """ Initialize with mandatory header fields. """
        self.hdr_fields = hf.factory_mandatory_fields(self)

    def sort(self):
        """ Sort header fields. """
        self.hdr_fields = sorted(self.hdr_fields, key=lambda o: o.order)

    def init_from_msg(self, prevmsg):
        """ Initialize values based on previous message. """
        assert isinstance(prevmsg, str)
        msg_dict = hf.msg2fields(prevmsg)
        if len(self.hdr_fields) == 0:
            self.init_mandatory()
        for hfield in self.hdr_fields:
            msg_field_name = hfield.__class__.__name__.replace('_', '-')
            print(msg_field_name)
            if msg_field_name in msg_dict.keys():
                hfield.from_string(msg_dict[msg_field_name])

        self.field('Content_Length').value = 0

class Rfc3261(SipMessage):
    """ Messages based on RFC 3261 """
    def __init__(self):
        super(Rfc3261, self).__init__()

class Request(Rfc3261):
    """SIP request message, RFC 3261, 7.1

    Parameters:
    method: Name of request method
    request_uri: Request URI value
    status_code: Response code
    reason_phrase: Common phrase describing code.
    """
    # Request-Line  =  Method SP Request-URI SP SIP-Version CRLF
    def __init__(self, method=None, request_uri=None, transport=None):
        super(Request, self).__init__()
        self.method = method    # Name of request method, p.27, 7.1 Requests
        self.request_uri = request_uri
        self.transport = transport
        self.msg_type = "R"

        #letters = string.ascii_letters + string.digits
        self.branch = hf.gen_new_branch()

    def __str__(self):
        """Get string value of SIP request."""
        return self.request_line + \
            "\r\n" + "\r\n".join([h.__str__() for h in self.hdr_fields]) + \
            '\r\n\r\n'

    @property
    def request_line(self):
        """Request line, p.27, 7.1"""
        return f"{self.method} {self.request_uri} {self.sip_version}"

class Response(Rfc3261):
    """RFC 3261, 7.2, SIP Responses

    Parameters:
    method: Name of request method
    request_uri: Request URI value
    status_code: Response code
    reason_phrase: Common phrase describing code.
    """
    # Status-Line  =  SIP-Version SP Status-Code SP Reason-Phrase CRLF
    def __init__(self, prevmsg=None, status_code=None, reason_phrase=None):
        super(Response, self).__init__()
        self.msg_type = "r"
        self.status_code = status_code # Status code, p. 28, 7.2 Responses
        self.reason_phrase = reason_phrase
        self.prevmsg = prevmsg
        self.method = None  # method value from prevmsg
        self.branch = None  # branch value from prevmsg

    def __str__(self):
        """Get string value of SIP response."""
        return self.status_line + \
            "\r\n" + "\r\n".join([h.__str__() for h in self.hdr_fields]) + \
            '\r\n\r\n'

    @property
    def status_line(self):
        """Response status line, p.28, 7.2"""
        return f"{self.sip_version} {self.status_code} {self.reason_phrase}"

#
# SIP Methods are sorted by name
#
class Ack(Request):
    """ RFC 3261, 13, and 17.1.1.3 Construction of the ACK Request """
    def __init__(self):
        super(Ack, self).__init__()
        self.method = "ACK"

class Bye(Request):
    """ RFC 3261, 15, Terminating a Session """
    def __init__(self):
        super(Bye, self).__init__()
        self.method = "BYE"

class Cancel(Request):
    """ RFC 3261, 9, Canceling a Request """
    def __init__(self):
        super(Cancel, self).__init__()
        self.method = "CANCEL"

class Invite(Request):
    """ RFC 3261, 13, Initiating a Session """
    def __init__(self):
        super(Invite, self).__init__()
        self.method = "INVITE"

class Options(Request):
    """ RFC 3261, 11, Querying for Capabilities """
    def __init__(self):
        super(Options, self).__init__()
        self.method = "OPTIONS"

class Register(Request):
    """ RFC 3261, 10, Registrations """
    def __init__(self):
        super(Register, self).__init__()
        self.method = "REGISTER"

#####################################################################

class Rfc3262(Rfc3261):
    """ RFC 3262, Provisional Response """
    def __init__(self):
        super(Rfc3262, self).__init__()

class Prack(Rfc3262):
    """Provisional Response ACKnowledgement (PRACK) method"""
    def __init__(self):
        super(Prack, self).__init__()
        self.method = "PRACK"

#####################################################################

class Rfc3265(Rfc3262):
    """ RFC 3265, Event Notification """
    def __init__(self):
        super(Rfc3265, self).__init__()

class Notify(Rfc3265):
    """ Event Notification """
    def __init__(self):
        super(Notify, self).__init__()
        self.method = "NOTIFY"

class Subscribe(Rfc3265):
    """Event Subscription"""
    def __init__(self):
        super(Subscribe, self).__init__()
        self.method = "SUBSCRIBE"

#####################################################################

class Rfc3311(Rfc3265):
    """ RFC 3311, UPDATE Method """
    def __init__(self):
        super(Rfc3311, self).__init__()

class Update(Rfc3311):
    """ Update session info before final response to INVITE. """
    def __init__(self):
        super(Update, self).__init__()
        self.method = "UPDATE"

#####################################################################

class Rfc3428(Rfc3311):
    """ RFC 3428, Instant Messaging """
    def __init__(self):
        super(Rfc3428, self).__init__()

class Message(Rfc3428):
    """ Allows the transfer of Instant Messages. """
    def __init__(self):
        super(Message, self).__init__()
        self.method = "MESSAGE"

#####################################################################

class Rfc3515(Rfc3428):
    """ RFC 3515, Contact a third party, RFC 4488, RFC 4508, RFC 7614 """
    def __init__(self):
        super(Rfc3515, self).__init__()

class Refer(Rfc3515):
    """ Recipient REFER to a resource provided in the request. """
    def __init__(self):
        super(Refer, self).__init__()
        self.method = "REFER"

#####################################################################

class Rfc3903(Rfc3515):
    """ RFC 3903, Publish an event state. """
    # Also see RFC 5839
    def __init__(self):
        super(Rfc3903, self).__init__()

class Publish(Rfc3903):
    """ Method to publish event state within SIP Events framework. """
    def __init__(self):
        super(Publish, self).__init__()
        self.method = "PUBLISH"

#####################################################################

class Rfc6086(Rfc3261):
    """ RFC 6086, INFO Method and Package Framework """
    # Obsoletes 2976
    def __init__(self):
        super(Rfc6086, self).__init__()

class Info(Rfc6086):
    """ Info message, carries application level information. """
    def __init__(self):
        super(Info, self).__init__()
        self.method = "INFO"

##############################################################
