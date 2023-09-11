# vim: ts=4 sw=4 et ai

import support

TEST_USERS = {
    # Receiver
    'Alice': {
        'name': 'Alice',
        'extension': '2006',
        'domain': 'teo',
        'sipuri': 'sip:2006@teo',
        'password': 'strongpasswordhere',
        'server': 'Biloxi',
        'transport': None}}
addr = ('192.168.0.1', 12345)
contact = 'sip:banana@192.168.0.1:12345'

opt = support.sip_options(TEST_USERS['Alice'], addr)
print(str(opt))
print(opt.field('Via').value)
