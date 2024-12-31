# vim: set ai ts=4 sw=4 et:
# pylint: disable=C3001,C0114,C0115,C0116

import unittest
import sys
import inspect

from pysiptest import sipmsg
from pysiptest import headerfield as hf

def old_value_for_type(where_set, msg_type, method, new_value, old_value=None):
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

def new_value_for_type(where_set, msg_type, method, new_value, old_value=None):
    # msg_type: R, r, integer
    for hf_action in where_set:
        if method in hf_action[1].split(','):
            if isinstance(msg_type, int):
                if isinstance(hf_action[0], int):
                    if msg_type == hf_action[0]:
                        return hf_action[2](new_value, old_value)
                if isinstance(hf_action[0], tuple):
                    if hf_action[0][0] <= msg_type and \
                        msg_type <= hf_action[0][1]:
                        return hf_action[2](new_value, old_value)
            if isinstance(msg_type, str) and isinstance(hf_action[0], str):
                if msg_type in hf_action[0]:
                    return hf_action[2](new_value, old_value)

class TypeR(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [('R', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return TypeR.value_for_type(
            TypeR.where, msgtype, method, True) is not None

class Typer(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [('r', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return Typer.value_for_type(
            Typer.where, msgtype, method, True) is not None

class TypeRr(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [('Rr', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return TypeRr.value_for_type(
            TypeRr.where, msgtype, method, True) is not None

class TypeTuple(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [((100,199), 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return TypeTuple.value_for_type(
            TypeTuple.where, msgtype, method, True) is not None

class TypeInt(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [(100, 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return TypeInt.value_for_type(
            TypeInt.where, msgtype, method, True) is not None

class TypeMultiple(hf.HeaderField):
    _R = lambda nv, ov: nv
    where = [
        (200, 'OneFish,TwoFish', _R),
        ((100,199), 'OneFish,TwoFish', _R),
        ('R', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return TypeMultiple.value_for_type(
            TypeMultiple.where, msgtype, method, True) is not None

class NewTypeMultiple1():
    _R = lambda nv, ov: nv
    where = [
        (200, 'OneFish,TwoFish', _R),
        ((100,199), 'OneFish,TwoFish', _R),
        ('R', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return new_value_for_type(
            NewTypeMultiple1.where, msgtype, method, True) is not None

class NewTypeMultiple2():
    _R = lambda nv, ov: nv
    where = [
        ((100,199), 'OneFish,TwoFish', _R),
        (200, 'OneFish,TwoFish', _R),
        ('Rr', 'OneFish,TwoFish', _R)]

    @staticmethod
    def isvalid(msgtype, method):
        return new_value_for_type(
            NewTypeMultiple2.where, msgtype, method, True) is not None

class TestValueForType(unittest.TestCase):
    """ Unit tests for the header-field value_for_type method. """
    def test_R(self):
        assert TypeR.isvalid('R', 'OneFish')
        assert not TypeR.isvalid('R', 'ThreeFish')
        assert not TypeR.isvalid('r', 'OneFish')

    def test_r(self):
        assert Typer.isvalid('r', 'OneFish')

    def test_Rr(self):
        assert TypeRr.isvalid('R', 'OneFish')
        assert TypeRr.isvalid('r', 'OneFish')

    def test_tuple(self):
        assert TypeTuple.isvalid(100, 'OneFish')
        assert TypeTuple.isvalid(199, 'OneFish')
        assert not TypeTuple.isvalid(200, 'OneFish')

    def test_int(self):
        assert TypeInt.isvalid(100, 'OneFish')
        assert not TypeInt.isvalid(101, 'OneFish')

    def test_multiple(self):
        assert TypeMultiple.isvalid('R', 'OneFish')
        assert TypeMultiple.isvalid(100, 'OneFish')
        assert TypeMultiple.isvalid(200, 'OneFish')

    def test_newmultiple1(self):
        assert NewTypeMultiple1.isvalid('R', 'OneFish')
        assert not NewTypeMultiple1.isvalid('r', 'OneFish')
        assert NewTypeMultiple1.isvalid(100, 'OneFish')
        assert NewTypeMultiple1.isvalid(200, 'OneFish')
        assert not NewTypeMultiple1.isvalid('R', 'RedFish')
        assert not NewTypeMultiple1.isvalid(201, 'OneFish')

    def test_newmultiple2(self):
        assert NewTypeMultiple2.isvalid('R', 'OneFish')
        assert NewTypeMultiple2.isvalid('r', 'OneFish')
        assert NewTypeMultiple2.isvalid(100, 'OneFish')
        assert NewTypeMultiple2.isvalid(199, 'OneFish')
        assert NewTypeMultiple2.isvalid(200, 'OneFish')
        assert not NewTypeMultiple2.isvalid('R', 'RedFish')
        assert not NewTypeMultiple2.isvalid(201, 'OneFish')
        assert not NewTypeMultiple2.isvalid(99, 'OneFish')

    def test_overlappingname(self):
        assert not NewTypeMultiple2.isvalid('R', 'Fish')
        assert not NewTypeMultiple2.isvalid('R', 'One')

if __name__ == '__main__':
    unittest.main()
