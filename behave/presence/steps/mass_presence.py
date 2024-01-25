'''Provide steps supporting many users performing SUBSCRIBE and PUBLISH requests.'''
# vim: ts=4 sw=4 et ai
# pylint: disable=E0102
# pylint: disable=E0611

import logging
from behave import given, then

def ext2name(context, extension):
    '''Find name for given extension'''
    extension = str(extension)
    found = [k
            for k in context.test_users
            if context.test_users[k]['extension'] == extension]
    return found[0] if found else None

@given('extensions {first_ext} to {last_ext} register')
def step_impl(context, first_ext, last_ext):
    '''Implement step for registration'''
    first_ext = int(first_ext)
    last_ext = int(last_ext)
    assert len(context.test_users) > last_ext - first_ext
    context.mass_first = first_ext
    context.mass_last = last_ext
    for ext in range(first_ext, last_ext+1):
        ext_name = ext2name(context, ext)
        assert ext_name is not None
        logging.debug('%s registers', ext_name)
        context.execute_steps(f'Given "{ext_name}" registers')

@then('many users subscribe to each other')
def step_impl(context):
    '''Implement step for subscription'''
    assert 'mass_first' in context
    assert 'mass_last' in context
    first_ext = context.mass_first
    last_ext = context.mass_last
    for ext in range(first_ext, last_ext+1):
        for other_ext in range(first_ext, last_ext+1):
            if ext != other_ext:
                subscriber = ext2name(context, ext)
                subscribe_to = ext2name(context, other_ext)
                context.execute_steps(
                    f'Then "{subscriber}" subscribes to "{subscribe_to}"')

@then('many users unsubscribe from each other')
def step_impl(context):
    '''Implement step for unsubscription'''
    assert 'mass_first' in context
    assert 'mass_last' in context
    first_ext = context.mass_first
    last_ext = context.mass_last
    for ext in range(first_ext, last_ext+1):
        for other_ext in range(first_ext, last_ext+1):
            if ext != other_ext:
                subscriber = ext2name(context, ext)
                subscribe_to = ext2name(context, other_ext)
                context.execute_steps(
                    f'Then "{subscriber}" unsubscribes from "{subscribe_to}"')

@then('in sequence users set presence to "{new_state}"')
def step_impl(context, new_state):
    '''Implement step for presence state change'''
    assert 'mass_first' in context
    assert 'mass_last' in context
    first_ext = context.mass_first
    last_ext = context.mass_last
    for ext in range(first_ext, last_ext+1):
        subscriber = ext2name(context, ext)
        context.execute_steps(f'Then "{subscriber}" sets presence to "{new_state}"')
