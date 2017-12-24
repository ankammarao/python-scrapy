# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 15:21:25 2016

@author: abattula
"""
import json

config = {}
with open('input/config.ini', 'r') as f:
    for line in f.readlines():
        sp = line.strip().split('=')
        config[sp[0]] = sp[1]


input_file = config['input_file'] if 'input_file' in config else 'input/inputs.xml'
sites_file = config['sites_file'] if 'sites_file' in config else 'input/sites.json'
cookies_file = config['cookies_file'] if 'output_dir' in config else 'input/cookies.json'
output_dir = config['output_dir'] if 'output_dir' in config else 'results'
timeout = int(config['timeout']) if 'timeout' in config else 90
page_limit = int(config['page_limit']) if 'page_limit' in config else 2
screen_shot_capture = bool(config['screen_shot_capture']) if 'screen_shot_capture' in config else True
screenshot_threads = int(config['screenshot_threads']) if 'screenshot_threads' in config else 4

#Read the config files
with open(sites_file, 'r') as f:
    site_config = json.loads(f.read())

with open(cookies_file, 'r') as f:
    cookies = json.loads(f.read())

sites = site_config.keys()