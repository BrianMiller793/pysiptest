# vi: ai ts=4 =4 et

import logging
from behave import *

@given('{user} uses {phone} phone')
def step_impl(context, user, phone):
    logging.info('hello world')
    assert len(context.phones.keys()) == 0

@when('{caller} calls {receiver}')
def step_impl(context, caller, receiver):
    # (?) look up receiver-ext
    pass

@then('{user} answers the phone')
def step_impl(context, user):
    # option for behavior override?
    pass

@then('{user} talks for {duration} {timediv}')
def step_impl(context, user, duration, timediv):
    # wait
    pass

@then('{user} hangs up the phone')
def step_impl(context, user):
    pass

@then('{user} phone receives {state_request}')
def step_impl(context, user, state_request):
    pass

@given('{phone_state} is set to {state}')
def step_impl(context, phone_state, state):
    # Something goes here to put phone in 'state'
    pass

@then('{user} has voicemail')
def step_impl(context, user):
    # Something goes here for VM check
    pass

