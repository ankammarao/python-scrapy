# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 15:57:19 2016

@author: abattula
"""

import sys
import os
import requests
import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from pkg.config import timeout, cookies

#==============================================================================
#
#==============================================================================
class MyAdapter(HTTPAdapter):
    """"
    Possible ssl protocals:
        PROTOCOL_SSLv23
        PROTOCOL_SSLv3
        PROTOCOL_TLSv1
        PROTOCOL_TLSv1_1
        PROTOCOL_TLSv1_2
    """

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_SSLv23)


#==============================================================================
#
#==============================================================================
def get(session, url, cookies = {}, headers = {}):
    """Get a url using requests module with given session object"""
    return session.get(url, timeout=timeout, cookies=cookies, headers=headers)

#==============================================================================
#
#==============================================================================
def get_cookies(site=None):
    """
    Get cookies for given website. If website is not provided, returns all cookies for all websites.
    """
    if site:
        jar = requests.cookies.RequestsCookieJar()
        cookie_list = cookies[site]
        for cookie in cookie_list:
            jar.set(name=cookie['name'], value=cookie['value'], domain=cookie['domain'])
        return jar
    else:
        return cookies

#==============================================================================
#
#==============================================================================
def check_url(loaded_url, original_url):
    """Check if loaded url and original are same"""
    lu = loaded_url.replace('http://', '').replace('https://', '')
    ou = original_url.replace('http://', '').replace('https://', '')
    return lu == ou or lu == ou + '/' or lu + '/' == ou

#==============================================================================
#
#==============================================================================
def print_error(msg1, e=None, msg2=''):
    """Print to stderr"""
    sys.stderr.write('\nERROR: ' + msg1 + '..... ')
    if msg2:
        sys.stderr.write(msg2 + ' : ')
    if e:
        sys.stderr.write(repr(e.args))

    sys.stderr.write('\n')
    sys.stderr.flush()


#==============================================================================
#
#==============================================================================
def get_site(prod_url, sites = ['walmart', 'bol', 'kruidvat', 'jumbo']):
    """"Get the website from the product url"""
    for site in sites:
        if prod_url.find('www.' + site + '.') >= 0:
            return site
    return None

#==============================================================================
#
#==============================================================================
def change_session_user_agent(session, site):
    """"Change session header user agent"""
    new_session = get_session(site)
    if 'python' in session.headers['User-Agent']:
        new_session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    else:
        new_session.headers['User-Agent'] = 'python-requests/2.11.1'
    return new_session

#==============================================================================
#
#==============================================================================
def get_session(site):
    """Get session for respective website"""
    session = requests.Session()
    session.cookies = get_cookies(site)
    session.headers['User-Agent'] = 'python-requests/2.11.1'
    session.mount('https://', MyAdapter())
    return session

#==============================================================================
#
#==============================================================================
def create_dir(path) :
    """"Create a directory"""
    try:
        os.makedirs(path)
    except:
        pass
