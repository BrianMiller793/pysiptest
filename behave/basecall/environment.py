# vi: ai ts=4 sw=4 et

import asyncio
from behave import *

@fixture
def test_phones(context):
    context.phones = {}
    yield context.phones

def before_step(context, step):
    #use_fixture(test_phones, context)
    pass

def after_step(context, step):
    pass

def before_scenario(context, scenario):
    use_fixture(test_phones, context)
    pass

def after_scenario(context, scenario):
    pass

def before_feature(context, feature):
    pass

def after_feature(context, feature):
    pass

def before_tag(context, tag):
    pass

def after_tag(context, tag):
    pass

def before_all(context):
    pass

def after_all(context):
    pass
