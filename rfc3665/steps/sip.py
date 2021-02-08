from behave import *
sip_sessions = {}

# vim: set ai ts=4 sw=4 expandtab:

@given('new connection with user "{sip_user}" and server "{sip_server}"')
def step_impl(context, sip_user, sip_server):
    assert sip_user not in sip_sessions
    sip_sessions[sip_user] = sip_server

@given('existing connection with user "{sip_user}" and server "{sip_server}"')
def step_impl(context, sip_user, sip_server):
    assert sip_user in sip_sessions

@when('"{sip_user}" sends request "{sip_method}"')
def step_impl(context, sip_user, sip_method):
    pass

@then('"{sip_user}" receives response "{resp_codes}"')
def step_impl(context, sip_user, resp_codes):
    pass

@step('with header field "{hdr_text}"')
def step_impl(context, hdr_text):
    pass

@step('without header field "{hdr_name}"')
def step_impl(context, hdr_name):
    pass

@then('"{sip_user}" response contains field "{hdr_field}"')
def step_impl(context, sip_user, hdr_field):
    pass

@then('"{sip_user}" response does not contain field "{hdr_field}"')
def step_impl(context, sip_user, hdr_field):
    pass

@step('with password "{user_password}"')
def step_impl(context, user_password):
    pass

@then('"{sip_user}" is registered at the server')
def step_impl(context, sip_user):
    pass

@then('"{sip_user}" is unregistered')
def step_impl(context, sip_user):
    del sip_sessions[sip_user]
    assert sip_user not in sip_sessions
