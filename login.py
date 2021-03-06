# -*- Encoding: utf-8 -*-
import os
import re

import socket
import urllib
from httplib2 import Http

from cfg import load_config
from authcode import get_authcode


T_TIMEOUT = 2
output_dir = 'rsp_temp'


def default_success(website, cookie, content):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    f_content = os.path.join(output_dir, '%s.html' % website)
    with open(f_content, 'w') as f:
        f.write(content)

    print '%s login success! html saved in %s, Cookie:' % (website, f_content)
    print cookie


def default_error(website, err_no, err_msg):
    print 'ERROR %s | website=%s | %s' % (err_no, website, err_msg)


class clean_cookie:
    def __init__(self):
        pass

    @classmethod
    def renren(self, rsp, content):
        _timeprog=re.compile(r'; expires=[^;]+?\st=')
        return _timeprog.sub(r'; t=', rsp['set-cookie'])

    @classmethod
    def yesinfo(self, rsp, content):
        import json
        res = json.loads(content)
        if res['result'] == 1:
            h = Http(timeout=T_TIMEOUT)
            rsp, content = h.request(res['redirectUrl'])
            return rsp.get('set-cookie', None)
        return None

    @classmethod
    def raw(self, rsp, content):
        return rsp.get('set-cookie', None)


def login(website, username, password):
    """auto login and return cookie if success

    return Error code if fails:
    '1': failed to load config
    '2': timeout
    '3': cookie not found in headers or response
    """
    cfg_data = load_config(website)
    if cfg_data is None:  # error
        return '1'

    method = 'POST'
    headers = cfg_data['headers']
    # body
    login_data = cfg_data.get('login_data', dict())
    login_data[cfg_data['field_user']] = username
    login_data[cfg_data['field_password']] = password
    authcode_name = cfg_data['field_authcode']
    if authcode_name:
        headers['Cookie'], login_data[authcode_name] = get_authcode(cfg_data['url_authcode'])
    body = urllib.urlencode(login_data)

    h = Http(timeout=T_TIMEOUT)
    try:
        rsp, content = h.request(cfg_data['url_login'], method, headers=headers, body=body)  # response 302
    except socket.timeout:
        return '2'

    # parse cookie
    clean_cookie_meth = getattr(clean_cookie, website, clean_cookie.raw)
    return clean_cookie_meth(rsp, content) or headers.get('Cookie', '3')


if __name__ == '__main__':

    # default
    site = 'renren'
    user = 'yyttrr3242342@163.com'
    password = 'bmeB500bmeB500'

    import sys
    if len(sys.argv) > 1:
        site = sys.argv[1]
        user = raw_input(u'user: ')
        password = raw_input(u'password: ')

    print login(site, user, password)
