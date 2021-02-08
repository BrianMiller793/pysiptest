""" Message header fields for SIP messages. RFC 3261, see also RFC 2543. """

# vim: set ai ts=4 sw=4 expandtab:
# Author: Brian C. Miller
# Copyright 2017, all rights reserved
# Date: February 22, 2017

import inspect
import random
import string
import sys

# Absolutely mandatory fields, Section 8.1.1, ordered by recommendation.
MANDATORY = ('Via', 'Max_Forwards', 'From', 'To', 'CSeq', 'Call_ID')
VIA_COOKIE = "z9hG4bK"
SIP_VER = "SIP/2.0"

# Compact name to normal
COMPACT_NAMES = {
    'i': 'Call_ID',
    'm': 'Contact',
    'e': 'Content_Encoding',
    'l': 'Content_Length',
    'c': 'Content_Type',
    'f': 'From',
    's': 'Subject',
    'k': 'Supported',
    't': 'To',
    'v': 'Via',
}

def __get_subclasses():
    """ Get all subclasses of HeaderField. """
    return inspect.getmembers(sys.modules[__name__],
        predicate=lambda o: inspect.isclass(o) \
            and issubclass(o, HeaderField) \
            and not o is HeaderField)

def gen_rand_str(length=10):
    """ Generate a string, [A-Za-z0-9]* """
    return ''.join(
        random.SystemRandom()
        .choice(string.ascii_letters + string.digits)
        for _ in range(length))

def gen_new_branch(length=10):
    """ Generate a value for a new branch ID. """
    return VIA_COOKIE + gen_rand_str(length)

def get_valid_fields(sip_msg):
    """ Factory to generate all valid header fields for a SIP message. """
    assert sip_msg is not None
    assert sip_msg.method is not None
    assert sip_msg.msg_type is not None
    allfields = __get_subclasses()

    # allfields is collection of tuples: (name, class)
    validfields = []
    for field in allfields:
        if field[1].isvalid(sip_msg.msg_type, sip_msg.method) == True:
            validfields.append(field[1]())
    return validfields

def get_mandatory_fields(sip_msg):
    """ Factory to generate all mandatory header fields for a SIP message. """
    assert sip_msg is not None
    assert sip_msg.method is not None
    assert sip_msg.msg_type is not None

    # allfields is collection of tuples: (name, class)
    allfields = __get_subclasses()

    mandatoryfields = []
    for field in allfields:
        if field[1].ismandatory(sip_msg.msg_type, sip_msg.method) == True:
            mandatoryfields.append(field[1]())
    return mandatoryfields

def instance_by_name(field_name):
    """ Factory to instantiate object by field name. """

    if field_name is None:
        return None

    if len(field_name) == 1:
        try:
            field_name = COMPACT_NAMES[field_name]
        except KeyError:
            return None
    else:
        field_name = string.replace(field_name, '-', '_')

    try:
        instance = getattr(sys.modules[__name__], field_name)()
    except AttributeError:
        return None
    return instance or None

class HeaderField(object):
    """ Base class for a SIP message header field. """
    # pylint: disable=too-many-public-methods,invalid-name

    def __init__(self, oldvalue=None):
        """ Initialize a new instance of HeaderField.  """
        self.use_compact = False
        self.name = None
        self.value = None
        self.order = 99

    def __str__(self):
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            self.value)

    @staticmethod
    def value_for_type(where_set, msg_type, method, new_value, old_value=None):
        """ Return valid value for msessage type.

        This method is used to set appropriate values for the field.
        :param where_set: A set based on RFC 3261, Table 2 and 3.
            Position 0: 'Where' column, is letter, number, or tuple as range.
            Position 1: String containing SIP method names.
            Position 2: Lambda function, taking (new value, old value) as arguments.
        :param msg_type: Type of message, 'R', 'r', 'Rr' (both), number, range
        :param method: SIP method, e.g., ACK, BYE, CANCEL, etc.
        :param new_value: A new value for the field.
        :param old_value: A value from the previous set of headers, optional.
        :returns: None if field is not valid.
        """
        for hf_action in where_set:
            if isinstance(hf_action[0], tuple) and \
                isinstance(msg_type, int) and \
                hf_action[0][0] <= msg_type and \
                hf_action[0][1] >= msg_type and \
                method in hf_action[1]:
                return hf_action[2](new_value, old_value)
            elif isinstance(hf_action[0], int) and \
                isinstance(msg_type, int) and \
                hf_action[0] == msg_type and \
                method in hf_action[1]:
                return hf_action[2](new_value, old_value)
            elif isinstance(hf_action[0], str) and \
                isinstance(msg_type, str) and \
                msg_type in hf_action[0] and \
                method in hf_action[1]:
                return hf_action[2](new_value, old_value)
        return None

# The "where" column describes the request and response types in which
# the header field can be used.  Values in this column are:
#   R: header field may only appear in requests;
#   r: header field may only appear in responses;
#   Rr: An empty entry in the "where" column indicates that the header
#     field may be present in all requests and responses.
#   2xx, 4xx, etc.: A numerical value or range (tuple) indicates response
#     codes with which the header field can be used;
#   c: header field is copied from the request to the response.

# The next six columns relate to the presence of a header field in a
# method:
#   c: Conditional; requirements on the header field depend on the
#      context of the message.
#   m: The header field is mandatory.
#   m*: The header field SHOULD be sent, but clients/servers need to
#       be prepared to receive messages without that header field.
#   o: The header field is optional.
#   t: The header field SHOULD be sent, but clients/servers need to be
#      prepared to receive messages without that header field.
#      If a stream-based protocol (such as TCP) is used as a
#      transport, then the header field MUST be sent.
#   *: The header field is required if the message body is not empty.
#      See Sections 20.14, 20.15 and 7.4 for details.
#   -: The header field is not applicable.

class Accept(HeaderField):
    """ Identify message body formats that are accepted. Sec 20.1 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Accept                  R            -   o   -   o   m*  o
    # Accept                 2xx           -   -   -   o   m*  o
    # Accept                 415           -   c   -   c   c   c
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTION,REGISTER", _R),
        ((200, 299), "INVITE,OPTION,REGISTER", _2xx),
        (415, "BYE,INVITE,OPTION,REGISTER", _415))
    mandatory = (
        ('R', "OPTION", _R),
        ((200, 299), "OPTION", _2xx))

    def __init__(self, oldvalue=None):
        super(Accept, self).__init__(oldvalue)
        self._shortname = "Accept"
        self._longname = "Accept"
        self.value = 'application/sdp'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Accept.value_for_type(
            Accept.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Accept.value_for_type(
            Accept.mandatory, msgtype, method, True) is not None

class Accept_Encoding(HeaderField):
    """ Identify encoding formats accepted in response. Sec 20.2 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Accept-Encoding         R            -   o   -   o   o   o
    # Accept-Encoding        2xx           -   -   -   o   m*  o
    # Accept-Encoding        415           -   c   -   c   c   c
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTION,REGISTER", _R),
        ((200, 299), "INVITE,OPTION,REGISTER", _2xx),
        (415, 'BYE,INVITE,OPTION,REGISTER', _415))
    mandatory = (
        ((200, 299), "OPTION", _2xx),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Accept_Encoding, self).__init__(oldvalue)
        self._shortname = "Accept-Encoding"
        self._longname = "Accept-Encoding"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Accept_Encoding.value_for_type(
            Accept_Encoding.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Accept_Encoding.value_for_type(
            Accept_Encoding.mandatory, msgtype, method, True) is not None

class Accept_Language(HeaderField):
    """ Indicates preferred languages. Sec 20.3 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Accept-Language         R            -   o   -   o   o   o
    # Accept-Language        2xx           -   -   -   o   m*  o
    # Accept-Language        415           -   c   -   c   c   c
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTION,REGISTER", _R),
        ((200, 299), "INVITE,OPTION,REGISTER", _2xx),
        (415, "BYE,INVITE,OPTION,REGISTER", _415))
    mandatory = (
        ((200, 299), "OPTION", _2xx),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Accept_Language, self).__init__(oldvalue)
        self._shortname = "Accept-Language"
        self._longname = "Accept-Language"
        self.value = 'en-us'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Accept_Language.value_for_type(
            Accept_Language.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Accept_Language.value_for_type(
            Accept_Language.mandatory, msgtype, method, True) is not None

class Alert_Info(HeaderField):
    """ Specifies an alternate ring tone. Sec 20.4 """
    # Also see section 20.9 for security risks and mitigation
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Alert-Info              R      ar    -   -   -   o   -   -
    # Alert-Info             180     ar    -   -   -   o   -   -
    _R = lambda nv, ov: nv
    _180 = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (180, "INVITE", _180))

    def __init__(self, oldvalue=None):
        super(Alert_Info, self).__init__(oldvalue)
        self._shortname = "Alert-Info"
        self._longname = "Alert-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Alert_Info.value_for_type(
            Alert_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Allow(HeaderField):
    """ Lists the set of methods supported by the UA. Sec 20.5 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Allow                   R            -   o   -   o   o   o
    # Allow                  2xx           -   o   -   m*  m*  o
    # Allow                   r            -   o   -   o   o   o
    # Allow                  405           -   m   -   m   m   m
    _R = lambda nv, ov: nv
    _r = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _405 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTION,REGISTER", _R),
        ('r', "BYE,INVITE,OPTION,REGISTER", _r),
        ((200, 299), "BYE,INVITE,OPTION,REGISTER", _2xx),
        (405, "BYE,INVITE,OPTION,REGISTER", _405))
    mandatory = (
        ((200, 299), "INVITE,OPTION", _2xx),
        (405, "BYE,INVITE,OPTION,REGISTER", _405))

    def __init__(self, oldvalue=None):
        super(Allow, self).__init__(oldvalue)
        self._shortname = "Allow"
        self._longname = "Allow"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Allow.value_for_type(
            Allow.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Allow.value_for_type(
            Allow.mandatory, msgtype, method, True) is not None

class Authentication_Info(HeaderField):
    """ Provides mutual authentication with HTTP Digest. Sec 20.6 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Authentication-Info    2xx           -   o   -   o   o   o
    _2xx = lambda nv, ov: nv
    where = (
        ((200, 299), "BYE,INVITE,OPTION,REGISTER", _2xx),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Authentication_Info, self).__init__(oldvalue)
        self._shortname = "Authentication-Info"
        self._longname = "Authentication-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Authentication_Info.value_for_type(
            Authentication_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Authorization(HeaderField):
    """ Contains authentication credentials of a UA. Sec 20.7 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Authorization           R            o   o   o   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Authorization, self).__init__(oldvalue)
        self._shortname = "Authorization"
        self._longname = "Authorization"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Authorization.value_for_type(
            Authorization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Call_ID(HeaderField):
    """ Contains unique identifier for INVITE or REGISTER. Sec 20.8 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Call-ID                 c       r    m   m   m   m   m   m
    # TODO Copied from request to response
    _c = lambda nv, ov: ov or nv

    def __init__(self, oldvalue=None):
        super(Call_ID, self).__init__(oldvalue)
        self._shortname = 'i'
        self._longname = 'Call-ID'
        self.order = 6

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return True

class Call_Info(HeaderField):
    """ Provides additional information about the caller or callee. Sec 20.9 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Call-Info                      ar    -   -   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Call_Info, self).__init__(oldvalue)
        self._shortname = "Call-Info"
        self._longname = "Call-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Call_Info.value_for_type(
            Call_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Contact(HeaderField):
    """ Context-dependent URI value. Sec 20.10 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Contact                 R            o   -   -   m   o   o
    # Contact                1xx           -   -   -   o   -   -
    # Contact                2xx           -   -   -   m   o   o
    # Contact                3xx      d    -   o   -   o   o   o
    # Contact                485           -   o   -   o   o   o
    _R = lambda nv, ov: nv
    _1xx = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _3xx = lambda nv, ov: nv
    _485 = lambda nv, ov: nv
    where = (
        ('R', "ACK,INVITE,OPTION,REGISTER", _R),
        ((100, 199), "INVITE", _1xx),
        ((200, 299), "INVITE,OPTION,REGISTER", _2xx),
        ((300, 399), "BYE,INVITE,OPTION,REGISTER", _3xx),
        (485, "BYE,INVITE,OPTION,REGISTER", _485))
    mandatory = (
        ('R', "INVITE", _R),
        ((200, 299), "INVITE", _2xx))

    def __init__(self, oldvalue=None):
        super(Contact, self).__init__(oldvalue)
        self._shortname = 'm'
        self._longname = 'Contact'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Contact.value_for_type(
            Contact.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Contact.value_for_type(
            Contact.mandatory, msgtype, method, True) is not None

class Content_Disposition(HeaderField):
    """ Describes how the message body should be interpreted. Sec 20.11 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Content-Disposition                  o   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Content_Disposition, self).__init__(oldvalue)
        self._shortname = "Content-Disposition"
        self._longname = "Content-Disposition"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Content_Disposition.value_for_type(
            Content_Disposition.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Content_Encoding(HeaderField):
    """ Modifier to 'media-type'. Sec 20.12 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Content-Encoding                     o   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Content_Encoding, self).__init__(oldvalue)
        self._shortname = 'e'
        self._longname = 'Content-Encoding'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Content_Encoding.value_for_type(
            Content_Encoding.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Content_Language(HeaderField):
    """ See RFC 2616, Sec 14.12. Sec 20.13 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Content-Language                     o   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Content_Language, self).__init__(oldvalue)
        self._shortname = "Content-Language"
        self._longname = "Content-Language"
        self.value = 'en-us'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Content_Language.value_for_type(
            Content_Language.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Content_Length(HeaderField):
    """ Indicates the size of the message-body. Sec 20.14 """
    # TODO This field is mandatory only when there is a message body.
    # TODO If a stream-based protocol (such as TCP) is used as transport,
    #      the header field MUST be used.
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Content-Length                 ar    t   t   t   t   t   t

    def __init__(self, oldvalue=None):
        super(Content_Length, self).__init__(oldvalue)
        self._shortname = 'l'
        self._longname = "Content-Length"
        self.value = 0

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        # TODO mandatory when message has a message body or stream transport.
        # For now: mandatory
        return True

class Content_Type(HeaderField):
    """ Indicates media type of the message-body. Sec 20.15 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Content-Type                         *   *   -   *   *   *
    # * = Required if message body is not empty
    # TODO message body
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))
    mandatory = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Content_Type, self).__init__(oldvalue)
        self._shortname = 'c'
        self._longname = 'Content-Type'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Content_Type.value_for_type(
            Content_Type.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Content_Type.value_for_type(
            Content_Type.mandatory, msgtype, method, True) is not None

class CSeq(HeaderField):
    """ Contains a sequence number and the request method. Sec 20.16 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # CSeq                    c       r    m   m   m   m   m   m
    # TODO Copied from request to response
    # TODO requires method name
    _c = lambda nv, ov: ov or nv

    def __init__(self, oldvalue=None):
        super(CSeq, self).__init__(oldvalue)
        self._shortname = "CSeq"
        self._longname = "CSeq"
        self.order = 5
        self.method = None

    # TODO
    def __str__(self):
        assert self.method is not None
        return "{}: {} {}".format(
            self._shortname if self.use_compact else self._longname,
            self.value, self.method)

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return True

class Date(HeaderField):
    """ Contains time and date. Sec 20.17 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Date                            a    o   o   o   o   o   o

    def __init__(self, oldvalue=None):
        super(Date, self).__init__(oldvalue)
        self._shortname = "Date"
        self._longname = "Date"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Error_Info(HeaderField):
    """ Provides a pointer to addition error information. Sec 20.18 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Error-Info           300-699    a    -   o   o   o   o   o
    _300 = lambda nv, ov: nv
    where = (
        ((300, 699), "BYE,CANCEL,INVITE,OPTION,REGISTER", _300),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Error_Info, self).__init__(oldvalue)
        self._shortname = "Error-Info"
        self._longname = "Error-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Error_Info.value_for_type(
            Error_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Expires(HeaderField):
    """ Gives relative time after which the message expires. Sec 20.19 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Expires                              -   -   -   o   -   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Expires, self).__init__(oldvalue)
        self._shortname = "Expires"
        self._longname = "Expires"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Expires.value_for_type(
            Expires.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class From(HeaderField):
    """ Indicates the initiator of the request. Sec. 20.10 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # From                    c       r    m   m   m   m   m   m
    # TODO Copied from request to response
    _c = lambda nv, ov: ov or nv

    def __init__(self, oldvalue=None):
        super(From, self).__init__(oldvalue)
        self._shortname = 'f'
        self._longname = 'From'
        self.order = 3
        self.tag = None
        # TODO: parse old value
        if self.tag is None:
            self.tag = gen_rand_str()

    def __str__(self):
        assert self.tag is not None
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            "{};tag={}".format(self.value, self.tag))

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return True

class In_Reply_To(HeaderField):
    """ Enumerates the Call-IDs referenced or returned. Sec 20.11 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # In-Reply-To             R            -   -   -   o   -   -
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(In_Reply_To, self).__init__(oldvalue)
        self._shortname = "In-Reply-To"
        self._longname = "In-Reply-To"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return In_Reply_To.value_for_type(
            In_Reply_To.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Max_Forwards(HeaderField):
    """ Maximum number of times message should be forwarded. Sec 20.22 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Max-Forwards            R      amr   m   m   m   m   m   m
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        (None, None, None))
    mandatory = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Max_Forwards, self).__init__(oldvalue)
        self._shortname = "Max-Forwards"
        self._longname = "Max-Forwards"
        self.value = 70
        self.order = 2

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Max_Forwards.value_for_type(
            Max_Forwards.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Max_Forwards.value_for_type(
            Max_Forwards.mandatory, msgtype, method, True) is not None

class MIME_Version(HeaderField):
    """ See RFC 2616, Sec 19.4.1. Sec 20.24 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # MIME-Version                         o   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(MIME_Version, self).__init__(oldvalue)
        self._shortname = "MIME-Version"
        self._longname = "MIME-Version"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return MIME_Version.value_for_type(
            MIME_Version.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Min_Expires(HeaderField):
    """ Minimum refresh interval for soft-state elements. Sec 20.23 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Min-Expires            423           -   -   -   -   -   m
    _423 = lambda nv, ov: nv
    where = (
        (423, "REGISTER", _423),
        (None, None, None))
    mandatory = (
        (423, "REGISTER", _423),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Min_Expires, self).__init__(oldvalue)
        self._shortname = "Min-Expires"
        self._longname = "Min-Expires"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Min_Expires.value_for_type(
            Min_Expires.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Min_Expires.value_for_type(
            Min_Expires.mandatory, msgtype, method, True) is not None

class Organization(HeaderField):
    """ Name of organization. Sec 20.25 """
    # Header field          where   proxy ACK BYE CAN INV OPT REG
    # Organization                   ar    -   -   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Organization, self).__init__(oldvalue)
        self._shortname = "Organization"
        self._longname = "Organization"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Organization.value_for_type(
            Organization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Priority(HeaderField):
    """ Indicates request urgency. Sec 20.26, also see RFC 6878 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Priority                    R          ar    -   -   -   o   -   -
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Priority, self).__init__(oldvalue)
        self._shortname = "Priority"
        self._longname = "Priority"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Priority.value_for_type(
            Priority.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Proxy_Authenticate(HeaderField):
    """ Contains an authentication challenge. Sec 20.27 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Proxy-Authenticate         407         ar    -   m   -   m   m   m
    # Proxy-Authenticate         401         ar    -   o   o   o   o   o
    _407 = lambda nv, ov: nv
    _401 = lambda nv, ov: nv
    where = (
        (407, "BYE,INVITE,OPTION,REGISTER", _407),
        (401, "BYE,CANCEL,INVITE,OPTION,REGISTER", _401))
    mandatory = (
        (407, "BYE,INVITE,OPTION,REGISTER", _407),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Proxy_Authenticate, self).__init__(oldvalue)
        self._shortname = "Proxy-Authenticate"
        self._longname = "Proxy-Authenticate"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Proxy_Authenticate.value_for_type(
            Proxy_Authenticate.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Proxy_Authenticate.value_for_type(
            Proxy_Authenticate.mandatory, msgtype, method, True) is not None

class Proxy_Authorization(HeaderField):
    """ Allows client to identify itself to proxy. Sec 20.28 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Proxy-Authorization         R          dr    o   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Proxy_Authorization, self).__init__(oldvalue)
        self._shortname = "Proxy-Authorization"
        self._longname = "Proxy-Authorization"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Proxy_Authorization.value_for_type(
            Proxy_Authorization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Proxy_Require(HeaderField):
    """ Proxy-sensitive features that must be supported. Sec 20.29 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Proxy-Require               R          ar    -   o   -   o   o   o
    _R = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Proxy_Require, self).__init__(oldvalue)
        self._shortname = "Proxy-Require"
        self._longname = "Proxy-Require"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Proxy_Require.value_for_type(
            Proxy_Require.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Record_Route(HeaderField):
    """ Inserted by proxies to force requests through the proxy. Sec 20.30 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Record-Route                R          ar    o   o   o   o   o   -
    # Record-Route             2xx,18x       mr    -   o   o   o   o   -
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION", _R),
        ((200, 299), "BYE,CANCEL,INVITE,OPTION", _2xx),
        ((180, 189), "BYE,CANCEL,INVITE,OPTION", _2xx))

    def __init__(self, oldvalue=None):
        super(Record_Route, self).__init__(oldvalue)
        self._shortname = "Record-Route"
        self._longname = "Record-Route"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Record_Route.value_for_type(
            Record_Route.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Reply_To(HeaderField):
    """ Logical return URI that may be different from From field. Sec 20.31 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Reply-To                                     -   -   -   o   -   -
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Reply_To, self).__init__(oldvalue)
        self._shortname = "Reply-To"
        self._longname = "Reply-To"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Reply_To.value_for_type(
            Reply_To.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Require(HeaderField):
    """ Used by UAC to specify options that must be supported. Sec 20.32 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Require                                ar    -   c   -   c   c   c
    _R = lambda nv, ov: ov or nv
    where = (
        ('Rr', "BYE,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Require, self).__init__(oldvalue)
        self._shortname = "Require"
        self._longname = "Require"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Require.value_for_type(
            Require.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        # Although an optional header field, the Require MUST NOT be
        # ignored if it is present.
        return False

class Retry_After(HeaderField):
    """ Indicate how long the service is expected to be unavailable. Sec 20.33 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Retry-After          404,413,480,486         -   o   o   o   o   o
    #                          500,503             -   o   o   o   o   o
    #                          600,603             -   o   o   o   o   o
    _R = lambda nv, ov: nv
    where = (
        (404, "BYE,INVITE,OPTION,REGISTER", _R),
        (413, "BYE,INVITE,OPTION,REGISTER", _R),
        (480, "BYE,INVITE,OPTION,REGISTER", _R),
        (486, "BYE,INVITE,OPTION,REGISTER", _R),
        (500, "BYE,INVITE,OPTION,REGISTER", _R),
        (503, "BYE,INVITE,OPTION,REGISTER", _R),
        (600, "BYE,INVITE,OPTION,REGISTER", _R),
        (603, "BYE,INVITE,OPTION,REGISTER", _R))

    def __init__(self, oldvalue=None):
        super(Retry_After, self).__init__(oldvalue)
        self._shortname = "Retry-After"
        self._longname = "Retry-After"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Retry_After.value_for_type(
            Retry_After.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Route(HeaderField):
    """ Force routing through listed set of proxies. Sec 20.34 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Route                       R          adr   c   c   c   c   c   c
    _R = lambda nv, ov: ov or nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Route, self).__init__(oldvalue)
        self._shortname = "Route"
        self._longname = "Route"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Route.value_for_type(
            Route.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Server(HeaderField):
    """ Information about UAS software. Sec 20.35 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Server                      r                -   o   o   o   o   o
    _r = lambda nv, ov: nv
    where = (
        ('r', "BYE,CANCEL,INVITE,OPTION,REGISTER", _r),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Server, self).__init__(oldvalue)
        self._shortname = "Server"
        self._longname = "Server"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Server.value_for_type(
            Server.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Subject(HeaderField):
    """ Summary or nature of the call. Sec 20.36 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Subject                     R                -   -   -   o   -   -
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Subject, self).__init__(oldvalue)
        self._shortname = 's'
        self._longname = 'Subject'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Subject.value_for_type(
            Subject.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Supported(HeaderField):
    """ Enumerates all supported extensions. Sec 20.37 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Supported                   R                -   o   o   m*  o   o
    # Supported                  2xx               -   o   o   m*  m*  o
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    where = (
        ('R', "BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        ((200, 299), "BYE,CANCEL,INVITE,OPTION,REGISTER", _2xx))
    mandatory = (
        ('R', "INVITE", _R),
        ((200, 299), "INVITE,OPTION", _2xx))

    def __init__(self, oldvalue=None):
        super(Supported, self).__init__(oldvalue)
        self._shortname = 'k'
        self._longname = 'Supported'

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Supported.value_for_type(
            Supported.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Supported.value_for_type(
            Supported.mandatory, msgtype, method, True) is not None

class Timestamp(HeaderField):
    """ Time when request is sent. Sec 20.38 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Timestamp                                    o   o   o   o   o   o

    def __init__(self, oldvalue=None):
        super(Timestamp, self).__init__(oldvalue)
        self._shortname = "Timestamp"
        self._longname = "Timestamp"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class To(HeaderField):
    """ Specifies the logical recipient. Sec 20.39 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # To                        c(1)          r    m   m   m   m   m   m
    # TODO Copied from request to response
    # TODO requires tag value
    _c = lambda nv, ov: ov or nv

    def __init__(self, oldvalue=None):
        super(To, self).__init__(oldvalue)
        self._shortname = 't'
        self._longname = 'To'
        self.order = 4
        self.tag = None         # UAC Request outside of a dialog
                                # MUST NOT contain tag, 8.1.1.2

    def __str__(self):
        value = self.value + \
            (";tag={}".format(self.tag) if self.tag is not None else "")
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            value)

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return True

class Unsupported(HeaderField):
    """ Lists the features not supported. Sec 20.40 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Unsupported                420               -   m   -   m   m   m
    _420 = lambda nv, ov: nv
    where = (
        (420, "BYE,INVITE,OPTION,REGISTER", _420),
        (None, None, None))
    mandatory = (
        (420, "BYE,INVITE,OPTION,REGISTER", _420),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Unsupported, self).__init__(oldvalue)
        self._shortname = "Unsupported"
        self._longname = "Unsupported"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Unsupported.value_for_type(
            Unsupported.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Unsupported.value_for_type(
            Unsupported.mandatory, msgtype, method, True) is not None

class User_Agent(HeaderField):
    """ Contains information about the user agent. Sec 20.40 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # User-Agent                                   o   o   o   o   o   o

    def __init__(self, oldvalue=None):
        super(User_Agent, self).__init__(oldvalue)
        self._shortname = "User-Agent"
        self._longname = "User-Agent"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class Via(HeaderField):
    """ Indicates path taken by the request so far. Sec 20.42 """
    # One or more Via headers will exist in a message.
    # Between UAC and UAS, there will only be one Via.
    # Between UAS and proxies, there may be more than one Via.
    # Header field     where       proxy ACK BYE CAN INV OPT REG
    # Via                R          amr   m   m   m   m   m   m
    # Via               rc          dr    m   m   m   m   m   m
    # TODO Copied from request to response
    # TODO Equality operator, 20.42
    _c = lambda nv, ov: ov or nv
    _R = lambda nv, ov: nv
    _r = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        ('r', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _r))
    mandatory = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _R),
        ('r', "ACK,BYE,CANCEL,INVITE,OPTION,REGISTER", _r))

    def __init__(self, oldvalue=None):
        super(Via, self).__init__(oldvalue)
        self._shortname = 'v'
        self._longname = 'Via'
        self.order = 1
        self.transport = None       # 'UDP', 'TCP', 'TLS', 'SCTP'
        self.address = None         # Host name or network address, port opt.
        self.branch = None          # Required SIP/2.0, optional RFC 2543
        self.maddr = None           # page 150, server to be contacted for user
        self.ttl = None             # time to live for UDP Multicast packet
        self.received = None        # RFC 2543, 6.40.2, added by proxy for NAT
        self.value = oldvalue
        # TODO parse old value
        if self.branch is None:
            self.branch = gen_new_branch()

    def __str__(self):
        assert self.transport is not None
        assert self.address is not None
        assert self.branch is not None
        if self.value is None:
            self.value = 'SIP/2.0/{} {};branch={}'.format(
                self.transport, self.address, self.branch) \
                + ('' if self.maddr is None else ';maddr={}'.format(self.maddr)) \
                + ('' if self.ttl is None else ';ttl={}'.format(self.ttl)) \
                + ('' if self.received is None else ';received={}'.format(self.received))
        return '{}: {}'.format(
            self._shortname if self.use_compact else self._longname,
            self.value)

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Via.value_for_type(
            Via.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return Via.value_for_type(
            Via.mandatory, msgtype, method, True) is not None

class Warning(HeaderField):
    """ Additional information about the response status. Sec 20.43 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # Warning                     r                -   o   o   o   o   o
    _r = lambda nv, ov: nv
    where = (
        ('r', "BYE,CANCEL,INVITE,OPTION,REGISTER", _r),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(Warning, self).__init__(oldvalue)
        self._shortname = "Warning"
        self._longname = "Warning"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return Warning.value_for_type(
            Warning.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return False

class WWW_Authenticate(HeaderField):
    """ Contains authentication challenge. Sec 20.44 """
    # Header field              where       proxy ACK BYE CAN INV OPT REG
    # WWW-Authenticate           401         ar    -   m   -   m   m   m
    # WWW-Authenticate           407         ar    -   o   -   o   o   o
    _401 = lambda nv, ov: nv
    _407 = lambda nv, ov: nv
    where = (
        (401, "BYE,INVITE,OPTION,REGISTER", _401),
        (407, "BYE,INVITE,OPTION,REGISTER", _407))
    mandatory = (
        (401, "BYE,INVITE,OPTION,REGISTER", _401),
        (None, None, None))

    def __init__(self, oldvalue=None):
        super(WWW_Authenticate, self).__init__(oldvalue)
        self._shortname = "WWW-Authenticate"
        self._longname = "WWW-Authenticate"

    @staticmethod
    def isvalid(msgtype, method):
        """ Determine whether field is valid for the SIP message type. """
        return WWW_Authenticate.value_for_type(
            WWW_Authenticate.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """ Determine whether field is mandatory for the SIP message type. """
        return WWW_Authenticate.value_for_type(
            WWW_Authenticate.mandatory, msgtype, method, True) is not None

