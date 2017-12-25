# python-scrapy
Scraping of websites using python

*For each website, generate a search URL and the traversal URL - for traversing to next page in search results 
*For each search page results, get the product URL
*For each product URL, extract the details 
*Validate the product in comparison with the searched key word 
*Storing all the results in XML format - one XML per site - linking which result id for which input.
*With this information, I can get all available products on each website that are similar to each input. 


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
python start.py

Limitation
----------
only walmart, bol, jumbo and kruidvat configurations are added.
