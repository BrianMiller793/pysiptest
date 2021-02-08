# vim: set ai ts=4 sw=4 expandtab:

import sys
import unittest

sys.path.append('..')

import headerfield as hf

def exists(objects, name):
    for o in objects:
        if o.__class__.__name__ == name: return True
    return False

class TestSipMsg(object):
    def __init__(self):
        self.method = None
        self.msg_type = None

class TestHeaderField(unittest.TestCase):
    """ Unit tests for the HeaderField class. """

    def test_class_string(self):
        """ Test string value for class. """
        accept = hf.Accept()
        sv = "{}".format(accept)
        assert sv == "Accept: application/sdp"

    def test_CSeq(self):
        """ Test CSeq __str__ functionality. """
        o = hf.CSeq()
        o.value = 1234
        o.method = 'banana'
        sv = "{}".format(o)
        assert sv == "CSeq: 1234 banana"

    def test_From(self):
        """ Test From __str__ functionality. """
        o = hf.From()
        o.value = 'banana'
        o.tag = 1234
        sv = "{}".format(o)
        assert sv == "From: banana;tag=1234"
        o.use_compact = True
        sv = "{}".format(o)
        assert sv == "f: banana;tag=1234"

    def test_To(self):
        """ Test To __str__ functionality. """
        o = hf.To()
        o.value = 'banana'
        o.tag = 1234
        sv = "{}".format(o)
        assert sv == "To: banana;tag=1234"

        o.use_compact = True
        sv = "{}".format(o)
        assert sv == "t: banana;tag=1234"

        o.tag = None
        sv = "{}".format(o)
        assert sv == "t: banana"

    def test_Via(self):
        """ Test Via __str__ functionality. """
        o = hf.Via()
        o.branch = 'b1234'
        o.transport = 'UDP'
        o.address = "banana.apple"
        sv = "{}".format(o)
        assert sv == "Via: SIP/2.0/UDP banana.apple;branch=b1234"

        o.value = None
        o.maddr = 'm1234'
        sv = "{}".format(o)
        assert sv == "Via: SIP/2.0/UDP banana.apple;branch=b1234;maddr=m1234"

        o.value = None
        o.maddr = None
        o.ttl = 123
        sv = "{}".format(o)
        assert sv == "Via: SIP/2.0/UDP banana.apple;branch=b1234;ttl=123"

        o.value = None
        o.ttl = None
        o.received = 'rcvd123'
        sv = "{}".format(o)
        assert sv == "Via: SIP/2.0/UDP banana.apple;branch=b1234;received=rcvd123"

        o.value = None
        o.received = None
        o.use_compact = True
        sv = "{}".format(o)
        assert sv == "v: SIP/2.0/UDP banana.apple;branch=b1234"

    def test_where_isvalid(self):
        """ Verify isvalid() operation """
        # Also verifies HeaderField.value_for_type()
        assert hf.Accept.isvalid('R', 'REGISTER') == True
        assert hf.Accept.isvalid("R", "banana") == False
        assert hf.Accept.isvalid(200, 'REGISTER') == True
        assert hf.Accept.isvalid(415, 'REGISTER') == True
        assert hf.Accept.isvalid(199, 'REGISTER') == False
        assert hf.Accept.isvalid(300, 'REGISTER') == False

    def test_field_order(self):
        """ Check sort order for field processing priority """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.get_mandatory_fields(sipmsg)
        assert fields is not None

        fields = sorted(fields, key=lambda o: o.order)
        assert fields[0]._longname == "Via"
        assert fields[1]._longname == "Max-Forwards"
        assert fields[2]._longname == "From"
        assert fields[3]._longname == "To"
        assert fields[4]._longname == "CSeq"
        assert fields[5]._longname == "Call-ID"

    def test_instance_by_name(self):
        """ Test instantiating object by field name, normal and compact. """
        o = hf.instance_by_name("To")
        assert o._longname == "To"
        o = hf.instance_by_name("t")
        assert o._longname == "To"
        o = hf.instance_by_name("banana")
        assert o is None
        o = hf.instance_by_name("z")
        assert o is None

    def test_Register_allvalid(self):
        """ Check header field presence for SIP request """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.get_valid_fields(sipmsg)
        assert fields is not None

        # The following are allowed for REGISTER
        # Optional or mandatory according to Table 2
        assert exists(fields, "Accept")
        assert exists(fields, "Accept_Encoding")
        assert exists(fields, "Accept_Language")
        assert exists(fields, "Allow")
        assert exists(fields, "Authorization")
        assert exists(fields, "Call_ID")
        assert exists(fields, "Call_Info")
        assert exists(fields, "Contact")
        assert exists(fields, "Content_Disposition")
        assert exists(fields, "Content_Encoding")
        assert exists(fields, "Content_Language")
        assert exists(fields, "Content_Length")
        assert exists(fields, "Content_Type")
        assert exists(fields, "CSeq")
        assert exists(fields, "Date")
        assert exists(fields, "Expires")
        assert exists(fields, "From")
        assert exists(fields, "Max_Forwards")
        assert exists(fields, "MIME_Version")
        assert exists(fields, "Organization")
        assert exists(fields, "Proxy_Authorization")
        assert exists(fields, "Proxy_Require")
        assert exists(fields, "Require")
        assert exists(fields, "Route")
        assert exists(fields, "Supported")
        assert exists(fields, "Timestamp")
        assert exists(fields, "To")
        assert exists(fields, "User_Agent")
        assert exists(fields, "Via")

        # Absolutely mandatory fields
        for fn in hf.MANDATORY:
            assert exists(fields, fn)

    # Mandatory according to Table 2
    def test_Register_mandatory(self):
        """ Check mandatory header fields for SIP request """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.get_mandatory_fields(sipmsg)
        assert fields is not None

        assert exists(fields, "Call_ID")
        assert exists(fields, "Content_Length")
        assert exists(fields, "Content_Type")
        assert exists(fields, "CSeq")
        assert exists(fields, "From")
        assert exists(fields, "Max_Forwards")
        assert exists(fields, "To")
        assert exists(fields, "Via")

        # Absolutely mandatory fields
        for fn in hf.MANDATORY:
            assert exists(fields, fn)

    def test_INVITE_allvalid(self):
        """ """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "INVITE"

        fields = hf.get_valid_fields(sipmsg)
        assert fields is not None

        assert exists(fields, "Accept")
        assert exists(fields, "Accept_Encoding")
        assert exists(fields, "Accept_Language")
        assert exists(fields, "Alert_Info")
        assert exists(fields, "Allow")
        assert exists(fields, "Authorization")
        assert exists(fields, "Call_ID")
        assert exists(fields, "Call_Info")
        assert exists(fields, "Contact")
        assert exists(fields, "Content_Disposition")
        assert exists(fields, "Content_Encoding")
        assert exists(fields, "Content_Language")
        assert exists(fields, "Content_Length")
        assert exists(fields, "Content_Type")
        assert exists(fields, "CSeq")
        assert exists(fields, "Date")
        assert exists(fields, "Expires")
        assert exists(fields, "From")
        assert exists(fields, "In_Reply_To")
        assert exists(fields, "Max_Forwards")
        assert exists(fields, "MIME_Version")
        assert exists(fields, "Organization")
        assert exists(fields, "Priority")
        assert exists(fields, "Proxy_Authorization")
        assert exists(fields, "Proxy_Require")
        assert exists(fields, "Record_Route")
        assert exists(fields, "Reply_To")
        assert exists(fields, "Require")
        assert exists(fields, "Route")
        assert exists(fields, "Subject")
        assert exists(fields, "Supported")
        assert exists(fields, "Timestamp")
        assert exists(fields, "To")
        assert exists(fields, "User_Agent")
        assert exists(fields, "Via")

    def test_INVITE_mandatory(self):
        """ """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "INVITE"

        fields = hf.get_mandatory_fields(sipmsg)
        assert fields is not None

        assert exists(fields, "Call_ID")
        assert exists(fields, "Contact")
        assert exists(fields, "Content_Length")
        assert exists(fields, "Content_Type")
        assert exists(fields, "CSeq")
        assert exists(fields, "From")
        assert exists(fields, "Max_Forwards")
        assert exists(fields, "Supported")
        assert exists(fields, "To")
        assert exists(fields, "Via")

    def test_CANCEL(self):
        """ """
        # TODO Tests for INVITE just worked after REGISTER was debugged
        pass

    def test_BYE(self):
        """ """
        pass

    def test_ACK(self):
        """ """
        pass

    def test_OPTION(self):
        """ """
        pass

if __name__ == '__main__':
    unittest.main()

