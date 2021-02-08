""" Provides partial implementation of RFC 3261, for UAC and UAS. """
# pylint: disable=too-few-public-methods,too-many-ancestors
# vim: set ai ts=4 sw=4 expandtab:

import headerfield as hf

class SipMessage(object):
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

    def __init__(self, msgtype=None, method=None):
        self.type = msgtype     # R, r, number >= 100
        self.method = method    # Name of method
        self.hdrfields = []
        self.body = None

    def init_valid(self, msgtype=None, method=None):
        """ Initialize with valid headers. """
        pass

    def init_mandatory(self, msgtype=None, method=None):
        """ Initialize with valid mandatory headers. """
        pass
        
    def sort(self):
        """ Sort header fields. """
        self.hdrfields = sorted(self.hdrfields, key=lambda o: o.order)

    def init_from_msg(self, prevmsg):
        """ Initialize values based on previous message. """
        pass

    def to_string(self):
        """ Get string value of headers and body. """
        pass

class Rfc3261(SipMessage):
    """ Messages based on RFC 3261 """
    def __init__(self):
        super(Rfc3261, self).__init__()

class Request(Rfc3261):
    """ SIP request message, RFC 3261, 7.1 """
    # Request-Line  =  Method SP Request-URI SP SIP-Version CRLF
    def __init__(self, msgtype=None, method=None):
        super(Request, self).__init__()
        self.type = "R"

    def initvalid(self):
        """ Initialize with all valid header fields. """
        self.hdrfields = hf.get_valid_fields(self)

    def initmandatory(self):
        """ Initialize with mandatory header fields. """
        pass

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

class Response(Rfc3261):
    """ RFC 3261, 7.2, Responses """
    # Status-Line  =  SIP-Version SP Status-Code SP Reason-Phrase CRLF
    def __init__(self, prevmsg=None):
        super(Register, self).__init__()
        self.type = "r"
        self.status_code = 0
        self.reason_phrase = ""
        self.prevmsg = prevmsg

#####################################################################

class Rfc3262(Rfc3261):
    """ RFC 3262, Provisional Response """
    def __init__(self):
        super(Rfc3262, self).__init__()

class Prack(Rfc3262):
    """ Provisional Response ACKnowledgement (PRACK) method """
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
    """ Event Subscription """
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

