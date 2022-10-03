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
        self.cseq = 1
        self.call_id = '31415926'
        self.transport = 'UDP'
        self.branch = 'branch12345'

class TestHeaderField(unittest.TestCase):
    """ Unit tests for the HeaderField class. """

    def test_class_string(self):
        """ Test string value for class. """
        accept = hf.Accept()
        self.assertEqual(str(accept), "Accept: application/sdp")

    def test_CSeq_without_sipmsg(self):
        """ Test CSeq __str__ functionality. """
        o = hf.CSeq()
        o.value = 1234
        o.method = 'banana'
        self.assertEqual(str(o), "CSeq: 1234 banana")

    def test_CSeq_with_sipmsg(self):
        """ Test CSeq __str__ functionality. """
        sipmsg = TestSipMsg()
        sipmsg.method = 'banana'
        sipmsg.cseq = 1
        o = hf.CSeq(sipmsg=sipmsg)
        self.assertEqual(str(o), "CSeq: 1 banana")
        sipmsg.cseq += 1
        self.assertEqual(str(o), "CSeq: 2 banana")

    def test_From(self):
        """ Test From __str__ functionality. """
        o = hf.From()
        o.value = 'banana'
        o.tag = 1234
        self.assertEqual(str(o), "From: banana;tag=1234")
        o.use_compact = True
        self.assertEqual(str(o), "f: banana;tag=1234")

    def test_To(self):
        """ Test To __str__ functionality. """
        o = hf.To()
        o.value = 'banana'
        o.tag = 1234
        self.assertEqual(str(o), "To: banana;tag=1234")

        o.use_compact = True
        self.assertEqual(str(o), "t: banana;tag=1234")

        o.tag = None
        self.assertEqual(str(o), "t: banana")

    def test_Via_required(self):
        """ Test Via required parameters."""
        o = hf.Via()
        o.value = None
        o.via_params['protocol-name'] = None
        o.via_params['protocol-version'] = 'abc'
        o.via_params['transport'] = 'abc'
        o.via_params['address'] = 'abc'
        self.assertRaises(AssertionError, lambda: o.__str__())

        o.value = None
        o.via_params['protocol-name'] = 'abc'
        o.via_params['protocol-version'] = None
        o.via_params['transport'] = 'abc'
        o.via_params['address'] = 'abc'
        self.assertRaises(AssertionError, lambda: o.__str__())

        o.value = None
        o.via_params['protocol-name'] = 'abc'
        o.via_params['protocol-version'] = 'abc'
        o.via_params['transport'] = None
        o.via_params['address'] = 'abc'
        self.assertRaises(AssertionError, lambda: o.__str__())

        o.value = None
        o.via_params['protocol-name'] = 'abc'
        o.via_params['protocol-version'] = 'abc'
        o.via_params['transport'] = 'abc'
        o.via_params['address'] = None
        self.assertRaises(AssertionError, lambda: o.__str__())

    def test_Via_str(self):
        """ Test Via __str__ functionality. """
        o = hf.Via(sipmsg=TestSipMsg())
        o.via_params['branch'] = 'b1234'
        o.via_params['transport'] = 'UDP'
        o.via_params['address'] = "banana.apple"
        self.assertEqual(o.__str__(),
            "Via: SIP/2.0/UDP banana.apple;branch=b1234")

        o.value = None
        o.via_params['maddr'] = 'm1234'
        self.assertEqual(o.__str__(),
            "Via: SIP/2.0/UDP banana.apple;maddr=m1234;branch=b1234")

        o.value = None
        o.via_params['maddr'] = None
        o.via_params['ttl'] = 123
        self.assertEqual(o.__str__(),
            "Via: SIP/2.0/UDP banana.apple;ttl=123;branch=b1234")

        o.value = None
        o.via_params['ttl'] = None
        o.via_params['received'] = 'rcvd123'
        self.assertEqual(o.__str__(),
            "Via: SIP/2.0/UDP banana.apple;received=rcvd123;branch=b1234")

        o.value = None
        o.via_params['received'] = None
        o.use_compact = True
        self.assertEqual(o.__str__(),
            "v: SIP/2.0/UDP banana.apple;branch=b1234")

    def test_Contact_from_str1(self):
        '''Test Contact from_str'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = '"Mr. Watson" <sip:watson@worcester.bell-telephone.com>;q=0.7;expires=3600'
        key = 'sip:watson@worcester.bell-telephone.com'
        o.from_string(ts1)
        self.assertEqual(1, len(o.contact_params))
        self.assertEqual(3, len(o.contact_params[key]))
        self.assertEqual('Mr. Watson', o.contact_params[key]['display-name'])
        self.assertEqual('0.7', o.contact_params[key]['q'])
        self.assertEqual('3600', o.contact_params[key]['expires'])

    def test_Contact_from_str2(self):
        '''Test Contact from_str'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = '"Mr. Watson" <sip:watson@worcester.bell-telephone.com>;q=0.7;expires=3600,"Mr. Watson" <mailto:watson@bell-telephone.com>;q=0.1'
        key1 = 'sip:watson@worcester.bell-telephone.com'
        key2 = 'mailto:watson@bell-telephone.com'
        o.from_string(ts1)
        self.assertEqual(2, len(o.contact_params))
        self.assertEqual(3, len(o.contact_params[key1]))
        self.assertEqual(2, len(o.contact_params[key2]))
        self.assertEqual('0.1', o.contact_params[key2]['q'])

    def test_Contact_from_str3(self):
        '''Test Contact from_str'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = 'sip:hownow@browncow.com'
        key = ts1
        o.from_string(ts1)
        self.assertEqual(1, len(o.contact_params))
        self.assertEqual(0, len(o.contact_params[key]))

    def test_Contact_to_str1(self):
        '''Test Contact __str__'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = 'sip:hownow@browncow.com'
        o.from_string(ts1)
        s_val = str(o)
        self.assertEqual('Contact: ' + ts1, s_val)

    def test_Contact_to_str2(self):
        '''Test Contact __str__'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = '"Mr. Watson" <sip:watson@worcester.bell-telephone.com>;q=0.7;expires=3600'
        o.from_string(ts1)
        s_val = str(o)
        self.assertEqual('Contact: ' + ts1, s_val)

    def test_Contact_to_str3(self):
        '''Test Contact __str__'''
        o = hf.Contact(sipmsg=TestSipMsg())
        ts1 = '"Mr. Watson" <sip:watson@worcester.bell-telephone.com>;q=0.7;expires=3600,"Mr. Watson" <mailto:watson@bell-telephone.com>;q=0.1'
        o.from_string(ts1)
        s_val = str(o)
        self.assertEqual('Contact: ' + ts1, s_val)

    def test_Content_Type(self):
        '''Test Content-Type'''
        expected = 'text/plain'
        o = hf.Content_Type(value=expected)
        self.assertEqual(o.value, expected)
        expected = 'Content-Type: ' + expected
        self.assertEqual(str(o), expected)

    def test_where_isvalid(self):
        """ Verify isvalid() operation """
        # Also verifies HeaderField.value_for_type()
        self.assertTrue(hf.Accept.isvalid('R', 'REGISTER'))
        self.assertFalse(hf.Accept.isvalid("R", "banana"))
        self.assertTrue(hf.Accept.isvalid(200, 'REGISTER'))
        self.assertTrue(hf.Accept.isvalid(415, 'REGISTER'))
        self.assertFalse(hf.Accept.isvalid(199, 'REGISTER'))
        self.assertFalse(hf.Accept.isvalid(300, 'REGISTER'))

    def test_field_order(self):
        """ Check sort order for field processing priority """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.factory_mandatory_fields(sipmsg)
        self.assertIsNotNone(fields)

        fields = sorted(fields, key=lambda o: o.order)
        self.assertEqual(fields[0]._longname, "Via")
        self.assertEqual(fields[1]._longname, "Max-Forwards")
        self.assertEqual(fields[2]._longname, "From")
        self.assertEqual(fields[3]._longname, "To")
        self.assertEqual(fields[4]._longname, "CSeq")
        self.assertEqual(fields[5]._longname, "Call-ID")

    def test_factory_field_by_name(self):
        """ Test instantiating object by field name, normal and compact. """
        o = hf.factory_field_by_name("To")
        self.assertEqual(o._longname, "To")
        o = hf.factory_field_by_name("t")
        self.assertEqual(o._longname, "To")
        o = hf.factory_field_by_name("banana")
        self.assertIsNone(o)
        o = hf.factory_field_by_name("z")
        self.assertIsNone(o)

    def test_Register_allvalid(self):
        """ Check header field presence for SIP request """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.factory_valid_fields(sipmsg)
        self.assertIsNotNone(fields)

        # The following are allowed for REGISTER
        # Optional or mandatory according to Table 2
        self.assertTrue(exists(fields, "Accept"))
        self.assertTrue(exists(fields, "Accept_Encoding"))
        self.assertTrue(exists(fields, "Accept_Language"))
        self.assertTrue(exists(fields, "Allow"))
        self.assertTrue(exists(fields, "Authorization"))
        self.assertTrue(exists(fields, "Call_ID"))
        self.assertTrue(exists(fields, "Call_Info"))
        self.assertTrue(exists(fields, "Contact"))
        self.assertTrue(exists(fields, "Content_Disposition"))
        self.assertTrue(exists(fields, "Content_Encoding"))
        self.assertTrue(exists(fields, "Content_Language"))
        self.assertTrue(exists(fields, "Content_Length"))
        self.assertTrue(exists(fields, "Content_Type"))
        self.assertTrue(exists(fields, "CSeq"))
        self.assertTrue(exists(fields, "Date"))
        self.assertTrue(exists(fields, "Expires"))
        self.assertTrue(exists(fields, "From"))
        self.assertTrue(exists(fields, "Max_Forwards"))
        self.assertTrue(exists(fields, "MIME_Version"))
        self.assertTrue(exists(fields, "Organization"))
        self.assertTrue(exists(fields, "Proxy_Authorization"))
        self.assertTrue(exists(fields, "Proxy_Require"))
        self.assertTrue(exists(fields, "Require"))
        self.assertTrue(exists(fields, "Route"))
        self.assertTrue(exists(fields, "Supported"))
        self.assertTrue(exists(fields, "Timestamp"))
        self.assertTrue(exists(fields, "To"))
        self.assertTrue(exists(fields, "User_Agent"))
        self.assertTrue(exists(fields, "Via"))

        # Absolutely mandatory fields
        for fn in hf.MANDATORY:
            self.assertTrue(exists(fields, fn))

    # Mandatory according to Table 2
    def test_Register_mandatory(self):
        """ Check mandatory header fields for SIP request """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "REGISTER"

        fields = hf.factory_mandatory_fields(sipmsg)
        self.assertIsNotNone(fields)

        self.assertTrue(exists(fields, "Call_ID"))
        self.assertTrue(exists(fields, "Content_Length"))
        self.assertTrue(exists(fields, "CSeq"))
        self.assertTrue(exists(fields, "From"))
        self.assertTrue(exists(fields, "Max_Forwards"))
        self.assertTrue(exists(fields, "To"))
        self.assertTrue(exists(fields, "Via"))

        # Absolutely mandatory fields
        for fn in hf.MANDATORY:
            self.assertTrue(exists(fields, fn))

    def test_INVITE_allvalid(self):
        """ """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "INVITE"

        fields = hf.factory_valid_fields(sipmsg)
        self.assertIsNotNone(fields)

        self.assertTrue(exists(fields, "Accept"))
        self.assertTrue(exists(fields, "Accept_Encoding"))
        self.assertTrue(exists(fields, "Accept_Language"))
        self.assertTrue(exists(fields, "Alert_Info"))
        self.assertTrue(exists(fields, "Allow"))
        self.assertTrue(exists(fields, "Authorization"))
        self.assertTrue(exists(fields, "Call_ID"))
        self.assertTrue(exists(fields, "Call_Info"))
        self.assertTrue(exists(fields, "Contact"))
        self.assertTrue(exists(fields, "Content_Disposition"))
        self.assertTrue(exists(fields, "Content_Encoding"))
        self.assertTrue(exists(fields, "Content_Language"))
        self.assertTrue(exists(fields, "Content_Length"))
        self.assertTrue(exists(fields, "Content_Type"))
        self.assertTrue(exists(fields, "CSeq"))
        self.assertTrue(exists(fields, "Date"))
        self.assertTrue(exists(fields, "Expires"))
        self.assertTrue(exists(fields, "From"))
        self.assertTrue(exists(fields, "In_Reply_To"))
        self.assertTrue(exists(fields, "Max_Forwards"))
        self.assertTrue(exists(fields, "MIME_Version"))
        self.assertTrue(exists(fields, "Organization"))
        self.assertTrue(exists(fields, "Priority"))
        self.assertTrue(exists(fields, "Proxy_Authorization"))
        self.assertTrue(exists(fields, "Proxy_Require"))
        self.assertTrue(exists(fields, "Record_Route"))
        self.assertTrue(exists(fields, "Reply_To"))
        self.assertTrue(exists(fields, "Require"))
        self.assertTrue(exists(fields, "Route"))
        self.assertTrue(exists(fields, "Subject"))
        self.assertTrue(exists(fields, "Supported"))
        self.assertTrue(exists(fields, "Timestamp"))
        self.assertTrue(exists(fields, "To"))
        self.assertTrue(exists(fields, "User_Agent"))
        self.assertTrue(exists(fields, "Via"))

    def test_INVITE_mandatory(self):
        """ """
        sipmsg = TestSipMsg()
        sipmsg.msg_type = "R"
        sipmsg.method = "INVITE"

        fields = hf.factory_mandatory_fields(sipmsg)
        self.assertIsNotNone(fields)

        self.assertTrue(exists(fields, "Call_ID"))
        self.assertTrue(exists(fields, "Contact"))
        self.assertTrue(exists(fields, "Content_Length"))
        self.assertTrue(exists(fields, "CSeq"))
        self.assertTrue(exists(fields, "From"))
        self.assertTrue(exists(fields, "Max_Forwards"))
        self.assertTrue(exists(fields, "Supported"))
        self.assertTrue(exists(fields, "To"))
        self.assertTrue(exists(fields, "Via"))

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

