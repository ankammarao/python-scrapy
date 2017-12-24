# python-scrapy
Scraping of websites using python

Requirements
-------------
Windows 7 (should work on other platforms as well but not tested yet.)
Tested for both Python 3.5.2 and 2.7.12

Modules used
-------------
os, threading, lxml, json, fuzzywuzzy, selenium, sys, Queue(3.5.2)/queue(2.7.12), requests, ssl

Products details
----------------
default location: input/inputs.xml
Can modify this by changing input_file parameter in input/config.ini file

Site configurations
-------------------
default location: input/sites.json
Can modify this by changing sites_file parameter in input/config.ini file

Cookies
-------------------
default location: input/cookies.json
Can modify this by changing cookies_file parameter in input/config.ini file

Default configurations
----------------------
output_dir: results
timeout: 90
page_limit: 2
capture screenshots: Yes
No of webdrivers per site to capture screenshots: 4

Usage
-----
cd /path/to/main/folder/
python start.py

Limitation
----------
only walmart, bol, jumbo and kruidvat configurations are added.
