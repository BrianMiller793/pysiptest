'''Create body for presence messages.'''
# vim: ts=4 sw=4 et ai
# pylint: disable=C0301

import random
import string

PERSON_ID = 'p' + ''.join(random.choices(string.digits, k=5))
TUPLE_ID = 't' + ''.join(random.choices(string.digits, k=5))

def status(state:str, sip_entity:str=None, extension:str=None):
    '''Produce presence status message for setting client presence.

    :param state: Presence state, eg Away, No Not Disturb, Available
    :param sip_entity:
    :param extension:
    :return: '''

    if state == "Busy":
        state_msg = status_busy()
    elif state == "Away":
        state_msg = status_away()
    elif state == "Not Available":
        state_msg = status_not_available()
    elif state == "Do Not Disturb":
        state_msg = status_dnd()
    elif state == "On Holiday":
        state_msg = status_holiday()
    elif state == "On Vacation":
        state_msg = status_vacation()
    elif state == "After Hours":
        state_msg = status_after_hours()
    elif state == "Call Forward":
        state_msg = status_call_forward(extension)
    elif state == "Available":
        state_msg = status_available()
    else:
        raise ValueError()

    return f'<?xml version="1.0" encoding="UTF-8"?><presence xmlns="urn:ietf:params:xml:ns:pidf" xmlns:dm="urn:ietf:params:xml:ns:pidf:data-model" xmlns:rpid="urn:ietf:params:xml:ns:pidf:rpid" xmlns:c="urn:ietf:params:xml:ns:pidf:cipid" xmlns:lt="urn:ietf:params:xml:ns:location-type" entity="{sip_entity}"><tuple id="{TUPLE_ID}"><status><basic>open</basic></status></tuple><dm:person id="{PERSON_ID}">{state_msg}</dm:person></presence>'

def status_busy():
    '''Create Busy status message.'''
    return '<rpid:activities><rpid:busy/></rpid:activities><dm:note>Busy</dm:note>'

def status_away():
    '''Create Away status message.'''
    return '<rpid:activities><rpid:away/></rpid:activities><dm:note>Away</dm:note>'

def status_not_available():
    '''Create Not Available status message.'''
    return '<rpid:activities><rpid:busy/></rpid:activities><dm:note>Not Available</dm:note>'

def status_dnd():
    '''Create Do Not Disturb status message.'''
    return '<rpid:activities><rpid:busy/></rpid:activities><dm:note>Do Not Disturb</dm:note>'

def status_holiday():
    '''Create On Holiday status message.'''
    return '<rpid:activities><rpid:holiday/></rpid:activities><dm:note>On Holiday</dm:note>'

def status_vacation():
    '''Create On Vacation status message.'''
    return '<rpid:activities><rpid:vacation/></rpid:activities><dm:note>On Vacation</dm:note>'

def status_after_hours():
    '''Create After Hours status message.'''
    return '<rpid:activities><rpid:away/></rpid:activities><dm:note>After Hours</dm:note>'

def status_call_forward(fwd_extension:str=None):
    '''Create Call Forward status message.'''
    return f'<rpid:activities><rpid:away/></rpid:activities><dm:note>Call Forward {fwd_extension}</dm:note>'

def status_available():
    '''Create Available status message.'''
    return '<dm:note>Available</dm:note>'
