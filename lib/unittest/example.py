# vim: set ai ts=4 sw=4 expandtab:

import inspect
import sys

class RootClass(object):
    def __init__(self, value=None):
        self.banana = 'orange'
        self.value = value

    def hello(self, msg):
        return msg

    @staticmethod
    def staticmsg():
        return "static message"

def get_subclasses():
    return inspect.getmembers(sys.modules[__name__],
        predicate=lambda o: inspect.isclass(o) \
            and issubclass(o, RootClass) \
            and not o is RootClass)

class SubClass1(RootClass):
    aardvark = 'yoiks'

    def __init__(self):
        super(SubClass1, self).__init__()
        pass

    @staticmethod
    def isvalid(msgtype):
        """ Is valid, mandatory or optional """
        return msgtype == "yes"

    @staticmethod
    def staticname():
        return __name__

    def instancename(self):
        return __name__

class SubClass2(RootClass):
    def __init__(self):
        super(SubClass2, self).__init__()
        pass

class SubClass3(RootClass):
    def __init__(self):
        super(SubClass3, self).__init__()
        pass

