# vim: set ai ts=4 sw=4 expandtab:

import sys
import unittest

import pysiptest.headerfield as hf
import pysiptest.sipmsg as sipmsg

class TestSipMessage(unittest.TestCase):
    '''Unit tests for sipmsg classes.'''

    def test_field(self):
        pass

    def test_init_valid(self):
        pass

    def test_init_mandatory(self):
        pass

    def sort(self):
        pass

    def init_from_msg(self):
        pass

# Nothing really to test for this class.
class TestRfc3261(unittest.TestCase):
    def test_init(self):
        pass

class Test_Request(unittest.TestCase):
    def test_init(self):
        pass

    def test_request_line(self):
        pass

class Test_Response(unittest.TestCase):
    def test_init(self):
        pass

    def test_status_line(self):
        response = sipmsg.Response(status_code=200, reason_phrase="OK")
        v = str(response).split()
        assert len(v) > 2
        assert v[0] == 'SIP/2.0'
        assert v[1] == '200'
        assert v[2] == 'OK'

    def test_from_string(self):
        pass
#        t_req = sipmsg.Notify()
#        t_req.init_mandatory()
#        via_fld = t_req.field('Via')
#        via_fld.via_params[''] =
#        via_fld.via_params[''] =
#        via_fld.via_params[''] =
#        via_fld.via_params[''] =
#        via_fld.via_params[''] =
#        t_rsp = sipmsg.Response(status_code=200, reason_phrase="OK")

class Test_Ack(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Ack()
        assert msg.method == "ACK"

class Test_Bye(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Bye()
        assert msg.method == "BYE"

class Test_Cancel(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Cancel()
        assert msg.method == "CANCEL"

class Test_Invite(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Invite()
        assert msg.method == "INVITE"

class Test_Options(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Options()
        assert msg.method == "OPTIONS"

class Test_Register(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Register()
        assert msg.method == "REGISTER"

# Nothing really to test for this class.
class Test_Rfc3262(unittest.TestCase):
    def test_init(self):
        pass

class Test_Prack(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Prack()
        assert msg.method == "PRACK"

# Nothing really to test for this class.
class Test_Rfc3265(unittest.TestCase):
    def test_init(self):
        pass

class Test_Notify(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Notify()
        assert msg.method == "NOTIFY"

class Test_Subscribe(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Subscribe()
        assert msg.method == "SUBSCRIBE"

# Nothing really to test for this class.
class Test_Rfc3311(unittest.TestCase):
    def test_init(self):
        pass

class Test_Update(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Update()
        assert msg.method == "UPDATE"

# Nothing really to test for this class.
class Test_Rfc3428(unittest.TestCase):
    def test_init(self):
        pass

class Test_Message(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Message()
        assert msg.method == "MESSAGE"

# Nothing really to test for this class.
class Test_Rfc3515(unittest.TestCase):
    def test_init(self):
        pass

class Test_Refer(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Refer()
        assert msg.method == "REFER"

# Nothing really to test for this class.
class Test_Rfc3903(unittest.TestCase):
    def test_init(self):
        pass

class Test_Publish(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Publish()
        assert msg.method == "PUBLISH"

# Nothing really to test for this class.
class Test_Rfc6086(unittest.TestCase):
    def test_init(self):
        pass

class Test_Info(unittest.TestCase):
    def test_init(self):
        msg = sipmsg.Info()
        assert msg.method == "INFO"

if __name__ == '__main__':
    unittest.main()

