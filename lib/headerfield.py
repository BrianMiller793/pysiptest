"""Message header fields for SIP messages. RFC 3261, see also RFC 2543."""

# vim: set ai ts=4 sw=4 expandtab:
# Author: Brian C. Miller
# Copyright 2017, all rights reserved
# Date: February 22, 2017
# pylint: disable=fixme,too-many-lines,invalid-name,super-with-arguments,unused-argument,too-many-instance-attributes

from binascii import hexlify
import inspect
import itertools
import os
import random
import re
import string
import sys
import uuid

# Absolutely mandatory fields, Section 8.1.1, ordered by recommendation.
MANDATORY = ('Via', 'Max_Forwards', 'From', 'To', 'CSeq', 'Call_ID')
VIA_COOKIE = "z9hG4bK"
SIP_VER = "SIP/2.0"

# Compact name to normal lookup
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
    'u': 'Allow_Events',
    'o': 'Event',
    'r': 'Refer_To',
}

def __get_subclasses():
    """Get all subclasses of HeaderField."""
    return inspect.getmembers(sys.modules[__name__],
        predicate=lambda o: inspect.isclass(o) \
            and issubclass(o, HeaderField) \
            and not o is HeaderField)

def gen_rand_str(length=10):
    """Generate a string, [A-Za-z0-9]*"""
    return ''.join(
        random.SystemRandom()
        .choice(string.ascii_letters + string.digits)
        for _ in range(length))

def gen_tag():
    """Generate a tag value, sec 19.3"""
    # "MUST be globally unique and cryptographically random
    # with at least 32 bits of randomness."
    return int.from_bytes(os.urandom(4), 'little', signed=False)

def gen_new_branch(length=10):
    """Generate a value for a new branch ID."""
    return VIA_COOKIE + gen_rand_str(length)

def msg2fields(sipmsg:str) -> dict:
    """Split SIP message into field-value dictionary. Additional
    data after header fields is in 'Body'."""
    # Use takewhile to split the message until an empty line
    # between fields and body
    line_iter = itertools.takewhile(lambda x : len(x), sipmsg.splitlines())
    lines = list(line_iter)

    # Convert list to dictionary, cleaning up keys and values
    fields = {
        hf.split(' ', 1)[0].rstrip(': '): hf.split(' ', 1)[1].strip()
        for hf in lines}

    content_length = int(fields['Content-Length'])
    if content_length != 0:
        fields['Body'] = sipmsg[len(sipmsg)-content_length:]

    return fields

def sdp_fields(sdp_body:str, field:str) -> list:
    '''Retrieve a list of SDP fields from a message.

    :param sdp_body: SIP SDP message.
    :param field: Field to match.
    :returns list: List of matching fields. May be empty.'''
    fields = [f for f in sdp_body.splitlines() if f.startswith(field)]
    return fields

def by_name(name):
    '''Return a field instance by its name from a list of fields.'''
    field = [f for f in __get_subclasses() if f.__class__.__name__ == name]
    return field[0]() if len(field) == 1 else None

def factory_valid_fields(sip_msg):
    """Factory to generate all valid header fields for a SIP message.

    :param sip_msg: Reference SIP message.
    :returns: list of fields.
    """
    assert sip_msg is not None
    assert sip_msg.method is not None
    assert sip_msg.msg_type is not None

    return [f[1]() for f in __get_subclasses()
        if f[1].isvalid(sip_msg.msg_type, sip_msg.method)]

def factory_mandatory_fields(sip_msg):
    """Factory to generate all mandatory header fields for a SIP message.

    :param sip_msg: Reference SIP message.
    :returns: list of fields.
    """
    assert sip_msg is not None
    assert sip_msg.method is not None
    assert sip_msg.msg_type is not None

    return [f[1]() for f in __get_subclasses()
        if f[1].ismandatory(sip_msg.msg_type, sip_msg.method)]

def factory_field_by_name(field_name):
    """Factory to instantiate object by field name."""

    if field_name is None:
        return None

    if len(field_name) == 1:
        try:
            field_name = COMPACT_NAMES[field_name]
        except KeyError:
            return None
    else:
        field_name = field_name.replace('-', '_')

    try:
        instance = getattr(sys.modules[__name__], field_name)()
    except AttributeError:
        return None
    return instance or None

class HeaderField():
    """Base class for a SIP message header field."""
    # pylint: disable=too-many-public-methods,invalid-name

    def __init__(self, value=None):
        """Initialize a new instance of HeaderField. """
        self.value = value
        self.use_compact = False
        self.order = 50
        self._shortname = ''
        self._longname = ''

    def __str__(self):
        # pylint: disable=C0209
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            self.value)

    def from_string(self, hdr_value):
        '''Header values parsed from given string value.'''
        # Should override in subclass
        self.value = hdr_value

    @staticmethod
    def value_for_type(where_set, msg_type, method, new_value, old_value=None):
        """Return valid value for msessage type.

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
            valid_methods = hf_action[1].split(',') if hf_action[1] else None
            if isinstance(hf_action[0], tuple) and \
                isinstance(msg_type, int) and \
                hf_action[0][0] <= msg_type and \
                hf_action[0][1] >= msg_type and \
                method in valid_methods:
                return hf_action[2](new_value, old_value)
            if isinstance(hf_action[0], int) and \
                isinstance(msg_type, int) and \
                hf_action[0] == msg_type and \
                method in valid_methods:
                return hf_action[2](new_value, old_value)
            if isinstance(hf_action[0], str) and \
                isinstance(msg_type, str) and \
                msg_type in hf_action[0] and \
                method in valid_methods:
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
    """Identify message body formats that are accepted. Sec 20.1"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Accept                  R            -   o   -   o   m*  o   o   o   o   o   o
    # Accept                 2xx           -   -   -   o   m*  o   -   -   -   -   -
    # Accept                 415           -   c   -   c   c   c   c   o   o   c   m*
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        ((200, 299), "INVITE,OPTIONS,REGISTER", _2xx),
        (415, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER", _415))
    mandatory = (
        ('R', "OPTIONS", _R),
        ((200, 299), "OPTIONS", _2xx),
        (415, "PUBLISH", _415))

    def __init__(self, value='application/sdp'):
        super().__init__(value)
        self._shortname = "Accept"
        self._longname = "Accept"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Accept.value_for_type(
            Accept.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Accept.value_for_type(
            Accept.mandatory, msgtype, method, True) is not None

class Accept_Encoding(HeaderField):
    """Identify encoding formats accepted in response. Sec 20.2"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Accept-Encoding         R            -   o   -   o   o   o   o   o   o       o
    # Accept-Encoding        2xx           -   -   -   o   m*  o   -   -   -       -
    # Accept-Encoding        415           -   c   -   c   c   c   c   o   o       m*
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,PUBLISH", _R),
        ((200, 299), "INVITE,OPTIONS,REGISTER", _2xx),
        (415, 'BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY', _415))
    mandatory = (
        ((200, 299), "OPTIONS", _2xx),
        (415, "PUBLISH", _415))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Accept-Encoding"
        self._longname = "Accept-Encoding"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Accept_Encoding.value_for_type(
            Accept_Encoding.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Accept_Encoding.value_for_type(
            Accept_Encoding.mandatory, msgtype, method, True) is not None

class Accept_Language(HeaderField):
    """Indicates preferred languages. Sec 20.3"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Accept-Language         R            -   o   -   o   o   o   o   o   o   o   o
    # Accept-Language        2xx           -   -   -   o   m*  o   -   -   -   -   -
    # Accept-Language        415           -   c   -   c   c   c   c   o   o   c   m*
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _415 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        ((200, 299), "INVITE,OPTIONS,REGISTER", _2xx),
        (415, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER", _415))
    mandatory = (
        ((200, 299), "OPTIONS", _2xx),
        (415, "PUBLISH", _415))

    def __init__(self, value='en-us'):
        super().__init__(value)
        self._shortname = "Accept-Language"
        self._longname = "Accept-Language"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Accept_Language.value_for_type(
            Accept_Language.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Accept_Language.value_for_type(
            Accept_Language.mandatory, msgtype, method, True) is not None

class Alert_Info(HeaderField):
    """Specifies an alternate ring tone. Sec 20.4"""
    # Also see section 20.9 for security risks and mitigation
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Alert-Info              R      ar    -   -   -   o   -   -   -   -   -   -   -
    # Alert-Info             180     ar    -   -   -   o   -   -   -   -   -   -
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _180 = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (180, "INVITE", _180))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Alert-Info"
        self._longname = "Alert-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Alert_Info.value_for_type(
            Alert_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Allow(HeaderField):
    """Lists the set of methods supported by the UA. Sec 20.5"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Allow                   R            -   o   -   o   o   o   o   o   o   o   o
    # Allow                  2xx           -   o   -   m*  m*  o   o   o   o   -
    # Allow                   r            -   o   -   o   o   o   o   o   o   o   o
    # Allow                  405           -   m   -   m   m   m   m   m   m   m   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _r = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _405 = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        ('r', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _r),
        ((200, 299), "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY", _2xx),
        (405, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY", _405))
    mandatory = (
        ((200, 299), "INVITE,OPTIONS", _2xx),
        (405, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _405))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Allow"
        self._longname = "Allow"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Allow.value_for_type(
            Allow.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Allow.value_for_type(
            Allow.mandatory, msgtype, method, True) is not None

class Authentication_Info(HeaderField):
    """Provides mutual authentication with HTTP Digest. Sec 20.6"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Authentication-Info    2xx           -   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _2xx = lambda nv, ov: nv
    where = (
        ((200, 299), "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _2xx),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Authentication-Info"
        self._longname = "Authentication-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Authentication_Info.value_for_type(
            Authentication_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Authorization(HeaderField):
    """Contains authentication credentials of a UA. Sec 20.7"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Authorization           R            o   o   o   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Authorization"
        self._longname = "Authorization"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Authorization.value_for_type(
            Authorization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Call_ID(HeaderField):
    """Contains unique identifier for INVITE or REGISTER. Sec 20.8"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Call-ID                 c       r    m   m   m   m   m   m   m   m   m   m   m
    # TODO Copied from request to response
    # pylint: disable=C3001
    _c = lambda nv, ov: ov or nv

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'i'
        self._longname = 'Call-ID'
        self.order = 6
        self.value = value if value is not None else str(uuid.uuid4())

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return True

class Call_Info(HeaderField):
    """Provides additional information about the caller or callee. Sec 20.9"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Call-Info                      ar    -   -   -   o   o   o   -   -   -   -   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,OPTIONS,REGISTER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Call-Info"
        self._longname = "Call-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Call_Info.value_for_type(
            Call_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Contact(HeaderField):
    """Context-dependent URI value. Sec 20.10"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Contact                 R            o   -   -   m   o   o   -   m   m   m   -
    # Contact                1xx           -   -   -   o   -   -   -   o   o   -   -
    # Contact                2xx           -   -   -   m   o   o   -   m   o   m   -
    # Contact                3xx      d    -   o   -   o   o   o   o   m   m   o   o
    # Contact                485           -   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _1xx = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _3xx = lambda nv, ov: nv
    _485 = lambda nv, ov: nv
    where = (
        ('R', "ACK,INVITE,OPTIONS,REGISTER,SUBSCRIBE,NOTIFY", _R),
        ((100, 199), "INVITE,SUBSCRIBE,NOTIFY,SUBSCRIBE,NOTIFY", _1xx),
        ((200, 299), "INVITE,OPTIONS,REGISTER,SUBSCRIBE,NOTIFY", _2xx),
        ((300, 399), "BYE,INVITE,OPTIONS,REGISTER,SUBSCRIBE,NOTIFY,PUBLISH", _3xx),
        (485, "BYE,INVITE,OPTIONS,REGISTER,SUBSCRIBE,NOTIFY,PUBLISH", _485))
    mandatory = (
        ('R', "INVITE,SUBSCRIBE,NOTIFY,SUBSCRIBE,NOTIFY,REFER", _R),
        ((200, 299), "INVITE,SUBSCRIBE,REFER", _2xx),
        ((300, 399), "SUBSCRIBE,NOTIFY", _3xx))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'm'
        self._longname = 'Contact'
        self.contact_params = {} # key is addr-spec, data is tuple
        if value is not None:
            self.from_string(value)

    def from_string(self, hdr_value):
        # Parse Contact, RFC 3261 p.228
        self.contact_params.clear()
        for contact_param in hdr_value.split(','):
            param_values = contact_param.split(';')
            # display-name and addr-spec
            dn_match = re.search('((?<=")[^"]+)', param_values[0])
            as_match = re.search('((?<=<)[^>]+)', param_values[0])
            display_name = dn_match[0] if dn_match is not None else None
            addr_spec = as_match[0] if as_match is not None else param_values[0]
            self.contact_params[addr_spec] = {}
            if display_name:
                self.contact_params[addr_spec]['display-name'] = display_name
            for c_param in param_values[1:]:
                p_key, p_value = c_param.split('=')
                self.contact_params[addr_spec][p_key] = p_value

    def __str__(self):
        # pylint: disable=C0209
        param_str = ''
        for cp_key in self.contact_params.keys():
            param = self.contact_params[cp_key]
            if param_str != '':
                param_str += ','
            if 'display-name' in self.contact_params[cp_key].keys():
                param_str += f'"{self.contact_params[cp_key]["display-name"]}" <{cp_key}>'
            else:
                param_str += cp_key
            for pk in param.keys():
                if pk == 'display-name':
                    continue
                param_str += ';{}={}'.format(pk, param[pk])

        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            param_str)

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Contact.value_for_type(
            Contact.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Contact.value_for_type(
            Contact.mandatory, msgtype, method, True) is not None

class Content_Disposition(HeaderField):
    """Describes how the message body should be interpreted. Sec 20.11"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Content-Disposition                  o   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Content-Disposition"
        self._longname = "Content-Disposition"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Content_Disposition.value_for_type(
            Content_Disposition.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Content_Encoding(HeaderField):
    """Modifier to 'media-type'. Sec 20.12"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Content-Encoding                     o   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'e'
        self._longname = 'Content-Encoding'

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Content_Encoding.value_for_type(
            Content_Encoding.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Content_Language(HeaderField):
    """See RFC 2616, Sec 14.12. Sec 20.13"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Content-Language                     o   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value='en-us'):
        super().__init__(value)
        self._shortname = "Content-Language"
        self._longname = "Content-Language"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Content_Language.value_for_type(
            Content_Language.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Content_Length(HeaderField):
    """Indicates the size of the message-body. Sec 20.14"""
    # TODO This field is mandatory only when there is a message body.
    # TODO If a stream-based protocol (such as TCP) is used as transport,
    #      the header field MUST be used.
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Content-Length                 ar    t   t   t   t   t   t   t   t   t   o   t

    def __init__(self, value=0):
        super().__init__(value)
        self._shortname = 'l'
        self._longname = "Content-Length"
        self.order = 99

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        # TODO mandatory when message has a message body or stream transport.
        # For now: mandatory
        return True

class Content_Type(HeaderField):
    """Indicates media type of the message-body. Sec 20.15"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Content-Type                         *   *   -   *   *   *   *   *   *   *   *
    # * = Required if message body is not empty
    # TODO message body
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))
    mandatory = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'c'
        self._longname = 'Content-Type'

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Content_Type.value_for_type(
            Content_Type.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class CSeq(HeaderField):
    """Contains a sequence number and the request method. Sec 20.16"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # CSeq                    c       r    m   m   m   m   m   m   m   m   m   m   m
    # TODO Copied from request to response
    # pylint: disable=C3001
    _c = lambda nv, ov: ov or nv

    def __init__(self, value=1, method=None):
        super().__init__(value)
        self._shortname = "CSeq"
        self._longname = "CSeq"
        self.order = 5
        self.method = method

    def __str__(self):
        # pylint: disable=C0209
        assert self.value is not None
        assert self.method is not None
        return "{}: {} {}".format(
            self._shortname if self.use_compact else self._longname,
            self.value,
            self.method)

    def from_string(self, hdr_value):
        values = hdr_value.split(' ')
        self.value = int(values[0])
        self.method = values[1]

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return True

class Date(HeaderField):
    """Contains time and date. Sec 20.17"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Date                            a    o   o   o   o   o   o   o   o   o   o   o

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Date"
        self._longname = "Date"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Error_Info(HeaderField):
    """Provides a pointer to addition error information. Sec 20.18"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Error-Info           300-699    a    -   o   o   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _300 = lambda nv, ov: nv
    where = (
        ((300, 699), "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _300),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Error-Info"
        self._longname = "Error-Info"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Error_Info.value_for_type(
            Error_Info.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Expires(HeaderField):
    """Gives relative time after which the message expires. Sec 20.19"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Expires                              -   -   -   o   -   o   -   o   -   o   o
    # Expires                2xx           -   -   -   o   -   o   -   m   -   -   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,REGISTER,REFER,PUBLISH", _R),
        ((200, 299), "INVITE,REGISTER,SUBSCRIBE", _2xx))
    mandatory = (
        ((200, 299), "INVITE,REGISTER,SUBSCRIBE,PUBLISH", _2xx),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Expires"
        self._longname = "Expires"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Expires.value_for_type(
            Expires.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Expires.value_for_type(
            Expires.mandatory, msgtype, method, True) is not None

class From(HeaderField):
    """Indicates the initiator of the request. Sec. 20.10"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # From                    c       r    m   m   m   m   m   m   m   m   m   m   m
    # TODO Copied from request to response
    # pylint: disable=C3001
    _c = lambda nv, ov: ov or nv

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'f'
        self._longname = 'From'
        self.order = 3
        self.tag = None
        # TODO: parse old value
        if self.tag is None:
            self.tag = gen_tag()

    def __str__(self):
        # pylint: disable=C0209
        assert self.tag is not None
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            "{};tag={}".format(self.value, self.tag))

    def from_string(self, hdr_value):
        '''Parse From: ___;tag=___ or From: ___'''
        # TODO: improve parsing
        values = hdr_value.split(';')
        self.value = values[0]
        if len(values) > 1:
            self.tag = values[1].split('=')[1]

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return True

class In_Reply_To(HeaderField):
    """Enumerates the Call-IDs referenced or returned. Sec 20.11"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # In-Reply-To             R            -   -   -   o   -   -   -   -   -   -   -
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "In-Reply-To"
        self._longname = "In-Reply-To"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return In_Reply_To.value_for_type(
            In_Reply_To.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Max_Forwards(HeaderField):
    """Maximum number of times message should be forwarded. Sec 20.22"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Max-Forwards            R      amr   m   m   m   m   m   m   m   m   m   m   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))
    mandatory = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=70):
        super().__init__(value)
        self._shortname = "Max-Forwards"
        self._longname = "Max-Forwards"
        self.order = 2

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Max_Forwards.value_for_type(
            Max_Forwards.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Max_Forwards.value_for_type(
            Max_Forwards.mandatory, msgtype, method, True) is not None

class MIME_Version(HeaderField):
    """See RFC 2616, Sec 19.4.1. Sec 20.24"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # MIME-Version                         o   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "ACK,BYE,INVITE,OPTIONS,REGISTER,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "MIME-Version"
        self._longname = "MIME-Version"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return MIME_Version.value_for_type(
            MIME_Version.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Min_Expires(HeaderField):
    """Minimum refresh interval for soft-state elements. Sec 20.23"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Min-Expires            423           -   -   -   -   -   m   -   -   -   -   m
    # pylint: disable=C3001
    _423 = lambda nv, ov: nv
    where = (
        (423, "REGISTER,PUBLISH", _423),
        (None, None, None))
    mandatory = (
        (423, "REGISTER,PUBLISH", _423),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Min-Expires"
        self._longname = "Min-Expires"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Min_Expires.value_for_type(
            Min_Expires.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Min_Expires.value_for_type(
            Min_Expires.mandatory, msgtype, method, True) is not None

class Organization(HeaderField):
    """Name of organization. Sec 20.25"""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Organization                   ar    -   -   -   o   o   o   -   o   -   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE,OPTIONS,REGISTER,SUBSCRIBE,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Organization"
        self._longname = "Organization"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Organization.value_for_type(
            Organization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Priority(HeaderField):
    """Indicates request urgency. Sec 20.26, also see RFC 6878"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Priority                    R          ar    -   -   -   o   -   -   -   o   -   -   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE,SUBSCRIBE,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Priority"
        self._longname = "Priority"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Priority.value_for_type(
            Priority.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Proxy_Authenticate(HeaderField):
    """Contains an authentication challenge. Sec 20.27"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Proxy-Authenticate         407         ar    -   m   -   m   m   m   m   m   m   m   m
    # Proxy-Authenticate         401         ar    -   o   o   o   o   o   o           o   o
    # pylint: disable=C3001
    _407 = lambda nv, ov: nv
    _401 = lambda nv, ov: nv
    where = (
        (407, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _407),
        (401, "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,PUBLISH", _401))
    mandatory = (
        (407, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,PUBLISH", _407),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Proxy-Authenticate"
        self._longname = "Proxy-Authenticate"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Proxy_Authenticate.value_for_type(
            Proxy_Authenticate.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Proxy_Authenticate.value_for_type(
            Proxy_Authenticate.mandatory, msgtype, method, True) is not None

class Proxy_Authorization(HeaderField):
    """Allows client to identify itself to proxy. Sec 20.28"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Proxy-Authorization         R          dr    o   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Proxy-Authorization"
        self._longname = "Proxy-Authorization"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Proxy_Authorization.value_for_type(
            Proxy_Authorization.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Proxy_Require(HeaderField):
    """Proxy-sensitive features that must be supported. Sec 20.29"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Proxy-Require               R          ar    -   o   -   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Proxy-Require"
        self._longname = "Proxy-Require"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Proxy_Require.value_for_type(
            Proxy_Require.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Record_Route(HeaderField):
    """Inserted by proxies to force requests through the proxy. Sec 20.30"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Record-Route                R          ar    o   o   o   o   o   -   o   o   o   o   -
    # Record-Route             2xx,18x       mr    -   o   o   o   o   -   o   o   o   o   -
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTIONS,PRACK,SUBSCRIBE,NOTIFY,REFER", _R),
        ((200, 299), "BYE,CANCEL,INVITE,OPTIONS,PRACK,SUBSCRIBE,NOTIFY,REFER", _2xx),
        ((180, 189), "BYE,CANCEL,INVITE,OPTIONS,PRACK,SUBSCRIBE,NOTIFY,REFER", _2xx))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Record-Route"
        self._longname = "Record-Route"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Record_Route.value_for_type(
            Record_Route.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Reply_To(HeaderField):
    """Logical return URI that may be different from From field. Sec 20.31"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Reply-To                                     -   -   -   o   -   -   -   -   -   -   -
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('Rr', "INVITE", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Reply-To"
        self._longname = "Reply-To"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Reply_To.value_for_type(
            Reply_To.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Require(HeaderField):
    """Used by UAC to specify options that must be supported. Sec 20.32"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Require                                ar    -   c   -   c   c   c   c   o   o   c   o
    # pylint: disable=C3001
    _R = lambda nv, ov: ov or nv
    where = (
        ('Rr', "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Require"
        self._longname = "Require"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Require.value_for_type(
            Require.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        # Although an optional header field, the Require MUST NOT be
        # ignored if it is present.
        return False

class Retry_After(HeaderField):
    """Indicate how long the service is expected to be unavailable. Sec 20.33"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Retry-After          404,413,480,486         -   o   o   o   o   o   o   o   o   o   o
    #                          500,503             -   o   o   o   o   o   o   o   o   o   o
    #                          600,603             -   o   o   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        (404, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (413, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (480, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (486, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (500, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (503, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (600, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (603, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Retry-After"
        self._longname = "Retry-After"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Retry_After.value_for_type(
            Retry_After.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Route(HeaderField):
    """Force routing through listed set of proxies. Sec 20.34"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Route                       R          adr   c   c   c   c   c   c   c   c   c   c   c
    # pylint: disable=C3001
    _R = lambda nv, ov: ov or nv
    where = (
        ('R', "ACK,BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Route"
        self._longname = "Route"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Route.value_for_type(
            Route.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Server(HeaderField):
    """Information about UAS software. Sec 20.35"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Server                      r                -   o   o   o   o   o   o   o   o   o   o
    # pylint: disable=C3001
    _r = lambda nv, ov: nv
    where = (
        ('r', "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _r),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Server"
        self._longname = "Server"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Server.value_for_type(
            Server.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Subject(HeaderField):
    """Summary or nature of the call. Sec 20.36"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Subject                     R                -   -   -   o   -   -   -   -   -   -   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "INVITE,PUBLISH", _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 's'
        self._longname = 'Subject'

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Subject.value_for_type(
            Subject.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Supported(HeaderField):
    """Enumerates all supported extensions. Sec 20.37"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Supported                   R                -   o   o   m*  o   o   o   o   o   o   o
    # Supported                  2xx               -   o   o   m*  m*  o   o   o   o   o   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    where = (
        ('R', "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _R),
        ((200, 299), "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _2xx))
    mandatory = (
        ('R', "INVITE", _R),
        ((200, 299), "INVITE,OPTIONS", _2xx))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 'k'
        self._longname = 'Supported'

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Supported.value_for_type(
            Supported.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Supported.value_for_type(
            Supported.mandatory, msgtype, method, True) is not None

class Timestamp(HeaderField):
    """Time when request is sent. Sec 20.38"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Timestamp                                    o   o   o   o   o   o   o   o   o   o   o

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Timestamp"
        self._longname = "Timestamp"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class To(HeaderField):
    """Specifies the logical recipient. Sec 20.39"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # To                        c(1)          r    m   m   m   m   m   m   m   m   m   m   m
    # TODO Copied from request to response
    # May require a tag value.
    # "A request outside of a dialog MUST NOT contain a To tag; the tag in
    # the To field of a request identifies the peer of the dialog.  Since
    # no dialog is established, no tag is present."
    # pylint: disable=C3001
    _c = lambda nv, ov: ov or nv

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = 't'
        self._longname = 'To'
        self.order = 4
        self.tag = None         # UAC Request outside of a dialog
                                # MUST NOT contain tag, 8.1.1.2

    def __str__(self):
        # pylint: disable=C0209
        value = \
            self.value if self.tag is None else "{};tag={}".format(self.value, self.tag)
            #";tag={}".format(self.tag) if self.tag is not None else ""
        return "{}: {}".format(
            self._shortname if self.use_compact else self._longname,
            value)

    def from_string(self, hdr_value):
        '''Parse To: ___;tag=___ or To: ___'''
        # TODO: improve parsing
        values = hdr_value.split(';')
        self.value = values[0]
        if len(values) > 1:
            self.tag = values[1].split('=')[1]

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return True

class Unsupported(HeaderField):
    """Lists the features not supported. Sec 20.40"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Unsupported                420               -   m   -   m   m   m   m   o   o   m   o
    # pylint: disable=C3001
    _420 = lambda nv, ov: nv
    where = (
        (420, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _420),
        (None, None, None))
    mandatory = (
        (420, "BYE,INVITE,OPTIONS,REGISTER,PRACK,REFER", _420),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Unsupported"
        self._longname = "Unsupported"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Unsupported.value_for_type(
            Unsupported.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Unsupported.value_for_type(
            Unsupported.mandatory, msgtype, method, True) is not None

class User_Agent(HeaderField):
    """Contains information about the user agent. Sec 20.40"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # User-Agent                                   o   o   o   o   o   o   o   o   o   o   o

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "User-Agent"
        self._longname = "User-Agent"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class Via(HeaderField):
    """Indicates path taken by the request so far. Sec 20.42"""
    # One or more Via headers will exist in a message.
    # Between UAC and UAS, there will only be one Via.
    # Between UAS and proxies, there may be more than one Via.
    # Header field     where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Via                R          amr   m   m   m   m   m   m   m   m   m   m   m
    # Via               rc          dr    m   m   m   m   m   m   m   m   m   m   m
    # TODO Copied from request to response
    # TODO Equality operator, 20.42

    def __init__(self, value=None, transport='UDP', branch=None):
        super().__init__(value)
        self._shortname = 'v'
        self._longname = 'Via'
        self.order = 1
        self.via_params = {}
        self.via_params['address'] = None   # Host name or network address
        self.via_params['ttl'] = None # time to live for UDP Multicast packet
        self.via_params['maddr'] = None # page 150, server to be contacted
        self.via_params['received'] = None # RFC 2543, 6.40.2, added for NAT
        self.via_params['rport'] = None # RFC 3581, Symmetric Response Routing
        self.via_params['request_rport'] = False
        self.via_params['rport_requested'] = False
        self.via_params['transport'] = None
        self.via_params['branch'] = None
        self.via_params['protocol-name'] = 'SIP'
        self.via_params['protocol-version'] = '2.0'
        self.via_params['transport'] = transport
        self.via_params['branch'] = branch

        if self.via_params['branch'] is None:
            self.via_params['branch'] = gen_new_branch()

    def __str__(self):
        # pylint: disable=C0209
        assert self.via_params['protocol-name'] is not None
        assert self.via_params['protocol-version'] is not None
        assert self.via_params['transport'] is not None
        assert self.via_params['address'] is not None
        if self.via_params['protocol-version'] == '2.0':
            assert self.via_params['branch'] is not None
        if self.value is None:
            self.value = '{}/{}/{} {}'.format(
                self.via_params['protocol-name'],
                self.via_params['protocol-version'],
                self.via_params['transport'],
                self.via_params['address']) \
                + ('' if self.via_params['ttl'] is None \
                    else ';ttl={}'.format(self.via_params['ttl'])) \
                + ('' if self.via_params['maddr'] is None \
                    else ';maddr={}'.format(self.via_params['maddr'])) \
                + ('' if self.via_params['received'] is None \
                    else ';received={}'.format(self.via_params['received'])) \
                + ('' if self.via_params['request_rport'] is False \
                    else ';rport') \
                + ('' if self.via_params['rport'] is None \
                    else ';rport={}'.format(self.via_params['rport'])) \
                + ('' if self.via_params['branch'] is None \
                    else ';branch={}'.format(self.via_params['branch']))
        return '{}: {}'.format(
            self._shortname if self.use_compact else self._longname,
            self.value)

    def from_string(self, hdr_value):
        '''Populate values from header field.'''
        hdr_values = hdr_value.split(';')
        # Split initial sent field
        sent = hdr_values[0].split()
        protocol = sent[0].split('/')
        self.via_params['protocol-name'] = protocol[0]
        self.via_params['protocol-version'] = protocol[1]
        self.via_params['transport'] = protocol[2]
        self.via_params['address'] = sent[1]
        for hv in hdr_values[1:]:
            vp = hv.split('=')
            if len(vp) == 2:
                self.via_params[vp[0]] = vp[1].strip()
            # if rport is requested, set flag
            elif vp[0] == 'rport':
                self.via_params['rport_requested'] = True

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return True

class Warning(HeaderField):
    """Additional information about the response status. Sec 20.43"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Warning                     r                -   o   o   o   o   o   o   o   o   o   o
    # Warning                     R                -   -   -   -   -   -   -   -   o   -
    # pylint: disable=C3001
    _r = lambda nv, ov: nv
    where = (
        ('r', "BYE,CANCEL,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _r),
        ('R', 'NOTIFY', _r))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Warning"
        self._longname = "Warning"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Warning.value_for_type(
            Warning.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

class WWW_Authenticate(HeaderField):
    """Contains authentication challenge. Sec 20.44"""
    # Header field              where       proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # WWW-Authenticate           401         ar    -   m   -   m   m   m   m   m   m   m   m
    # WWW-Authenticate           407         ar    -   o   -   o   o   o   -   -   -   o   o
    # pylint: disable=C3001
    _401 = lambda nv, ov: nv
    _407 = lambda nv, ov: nv
    where = (
        (401, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _401),
        (407, "BYE,INVITE,OPTIONS,REGISTER,REFER,PUBLISH", _407))
    mandatory = (
        (401, "BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY,REFER,PUBLISH", _401),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "WWW-Authenticate"
        self._longname = "WWW-Authenticate"

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return WWW_Authenticate.value_for_type(
            WWW_Authenticate.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return WWW_Authenticate.value_for_type(
            WWW_Authenticate.mandatory, msgtype, method, True) is not None

#####################################################################
# RFC 3262 Provisional Response

class RAck(HeaderField):
    '''The RAck header is sent in a PRACK request to support reliability of
    provisional responses. sec 7.2'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # RAck                    R            -   -   -   -   -   -   m   -   -
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', "PRACK", _R),
        (None, None, None))
    mandatory = (
        ('R', "PRACK", _R),
        (None, None, None))

    def __init__(self, value=None, method=None, rseq=0, cseq=0):
        super().__init__(value)
        self._shortname = "RAck"
        self._longname = "RAck"
        self.method = method
        self.rseq = rseq # from RSeq header in provisional response
        self.cseq = cseq # copied from CSeq in response

    def __str__(self):
        # It contains two numbers and a method tag.  The first number is
        # the value from the RSeq header in the provisional response that
        # is being acknowledged.  The next number, and the method, are
        # copied from the CSeq in the response that is being acknowledged.
        # The method name in the RAck header is case sensitive.
        # pylint: disable=C0209
        return "{}: {} {} {}".format(
            self._longname, self.rseq, self.cseq, self.method)

    def from_string(self, hdr_value):
        # RAck value comes from seperate values instead of one header.
        pass

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return RAck.value_for_type(
            RAck.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return RAck.value_for_type(
            RAck.mandatory, msgtype, method, True) is not None

class RSeq(HeaderField):
    '''The RSeq header is used in provisional responses in order to transmit
    them reliably.'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # RSeq                   1xx           -   -   -   o   -   -   -   -   -
    # pylint: disable=C3001
    _1xx = lambda nv, ov: nv
    where = (
        ((100, 199), "INVITE", _1xx),
        (None, None, None))

    def __init__(self, value=None, method=None):
        super().__init__(value)
        self._shortname = "RSeq"
        self._longname = "RSeq"
        self.method = method

    def __str__(self):
        # It contains a single numeric value from 1 to 2**32 - 1.
        # pylint: disable=C0209
        return "{}: {}".format(self._longname, self.value)

    def from_string(self, hdr_value):
        # Value is not set from previous header.
        pass

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return RSeq.value_for_type(
            RSeq.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

#####################################################################
# RFC 3265 -- SIP-Specific Event Notification (obsolete)
# RFC 6665 -- SIP-Specific Event Notification
# RFC 3863 -- Presence Information Data Format (PIDF)

class Allow_Events(HeaderField):
    """Allow-Events includes a list of tokens indicating the event packages supported."""
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Allow-Events            R            o   o   -   o   o   o   o   o   o
    # Allow-Events           2xx           -   o   -   o   o   o   o   o   o
    # Allow-Events           489           -   -   -   -   -   -   -   m   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    _2xx = lambda nv, ov: nv
    _489 = lambda nv, ov: nv
    where = (
        ('R', 'ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY', _R),
        ((200, 299), 'ACK,BYE,INVITE,OPTIONS,REGISTER,PRACK,SUBSCRIBE,NOTIFY', _2xx))
    mandatory = (
        (489, 'SUBSCRIBE,NOTIFY', _489),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "u"
        self._longname = "Allow-Events"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Allow_Events.value_for_type(
            Allow_Events.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Allow_Events.value_for_type(
            Allow_Events.mandatory, msgtype, method, True) is not None

class Subscription_State(HeaderField):
    '''Value contains state of subscription.'''
    # 6.4: Subscription-State registers response codes:
    #   Response Code Number:   202
    #   Default Reason Phrase:  Accepted
    # Response Code Number:   489
    #   Default Reason Phrase:  Bad Event
    # example: Subscription-State: active;expires=3597

    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Subscription-State      R            -   -   -   -   -   -   -   -   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', 'NOTIFY', _R),
        (None, None, None))
    mandatory = (
        ('R', 'NOTIFY', _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Subscription-State"
        self._longname = "Subscription-State"
        self.order = 50

    def from_string(self, hdr_value):
        # Value is not set from previous header.
        pass

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Subscription_State.value_for_type(
            Subscription_State.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Subscription_State.value_for_type(
            Subscription_State.mandatory, msgtype, method, True) is not None

class Event(HeaderField):
    '''Used to match NOTIFY and SUBSCRIBE messages, sec 7.2.1'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Event                   R            -   -   -   -   -   -   -   m   m   o   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', 'SUBSCRIBE,NOTIFY,REFER,PUBLISH', _R),
        (None, None, None))
    mandatory = (
        ('R', 'SUBSCRIBE,NOTIFY,PUBLISH', _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "o"
        self._longname = "Event"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Event.value_for_type(
            Event.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Event.value_for_type(
            Event.mandatory, msgtype, method, True) is not None

#####################################################################
# RFC 3515

class Refer_To(HeaderField):
    '''Provide URL to reference for REFER request.'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Refer_To                R            -   -   -   -   -   -   -   -   -   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', 'REFER', _R),
        (None, None, None))
    mandatory = (
        ('R', 'REFER', _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "r"
        self._longname = "Refer-To"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Refer_To.value_for_type(
            Refer_To.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Refer_To.value_for_type(
            Refer_To.mandatory, msgtype, method, True) is not None

#####################################################################
# RFC 3892

class Referred_By(HeaderField):
    '''Provide URL to reference for REFER request.'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Referred_By             R            -   o   -   o   o   o   -   -   -   m
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', 'BYE,INVITE,OPTIONS,REGISTER,REFER', _R),
        (None, None, None))
    mandatory = (
        ('R', 'REFER', _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Referred-By"
        self._longname = "Referred-By"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return Referred_By.value_for_type(
            Referred_By.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return Referred_By.value_for_type(
            Referred_By.mandatory, msgtype, method, True) is not None

#####################################################################
# RFC 7329: Session Identifier for SIP (Obsoleted by 7989)
# RFC 7989: End-to-End Session Identification
# The RFCs for Session-ID define a more rules than can be contained
# in the current header architecture at this time.

class Session_ID(HeaderField):
    '''Unique ID for duration of call session. Similar to Call-ID.'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # Session-ID              R            o   o   o   o   o   o   o   o   o   o

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "Session-ID"
        self._longname = "Session-ID"
        self.order = 50
        if value is None:
            self.value = hexlify(os.urandom(16)).decode()
        else:
            self.value = value

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return True

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False

    def from_string(self, hdr_value):
        '''Use remote= as new value, otherwise ignore value'''
        if 'remote' in hdr_value:
            rem_pos = hdr_value.strpos('remote=') + 7
            self.value = hdr_value[rem_pos:rem_pos + 32]

#####################################################################
# RFC 3903: SIP Event State Publication

class SIP_ETag(HeaderField):
    '''Entity tag to track PUBLISH event for updates.
    For each successful PUBLISH request, the ESC will generate and assign
    an entity-tag and return it in the SIP-ETag header field of the 2xx
    response.(4.1)'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # SIP-ETag               2xx           -   -   -   -   -   -   -   -   -   -   m
    # pylint: disable=C3001
    _2xx = lambda nv, ov: nv
    where = (
        ((200, 299), 'PUBLISH', _2xx),
        (None, None, None))
    mandatory = (
        ((200, 299), 'PUBLISH', _2xx),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "SIP-ETag"
        self._longname = "SIP-ETag"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return SIP_ETag.value_for_type(
            SIP_ETag.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return SIP_ETag.value_for_type(
            SIP_ETag.mandatory, msgtype, method, True) is not None

class SIP_If_Match(HeaderField):
    '''Used to identify specific event state.
    The first PUBLISH request will not have this header field.
    Subsequent event updates MUST have this field, containing the SIP-ETag
    value from the previous response.(4.1)'''
    # Header field          where   proxy ACK BYE CAN INV OPT REG PRA SUB NOT REF PUB
    # SIP-If-Match            R            -   -   -   -   -   -   -   -   -   -   o
    # pylint: disable=C3001
    _R = lambda nv, ov: nv
    where = (
        ('R', 'PUBLISH', _R),
        (None, None, None))

    def __init__(self, value=None):
        super().__init__(value)
        self._shortname = "SIP-If-Match"
        self._longname = "SIP-If-Match"
        self.order = 50

    @staticmethod
    def isvalid(msgtype, method):
        """Determine whether field is valid for the SIP message type."""
        return SIP_If_Match.value_for_type(
            SIP_If_Match.where, msgtype, method, True) is not None

    @staticmethod
    def ismandatory(msgtype, method):
        """Determine whether field is mandatory for the SIP message type."""
        return False
