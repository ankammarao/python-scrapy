# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 11:59:21 2016

@author: abattula
"""
import os
from threading import Thread

from pkg.dom import get_inputs
from pkg.reports import generate_report_xml
from pkg.product import process_products, save_screenshots
from pkg.search import process_search, get_unique_search_terms
from pkg.util import get_session, change_session_user_agent
from pkg.config import page_limit, timeout, input_file, sites, output_dir, screen_shot_capture


#==============================================================================
#
#==============================================================================
#import json
#url = 'https://www.ah.nl/service/rest/zoeken?rq=nivea&offset=0'
#
#with open('res.json', 'r') as f:
#    res = json.loads(f.read())
#
#for lane in res['_embedded']['lanes']:
#    if lane['type'] == 'SearchLane':
#        for item in lane['_embedded']['items']:
#            print(item['navItem']['link']['href'])


#==============================================================================
#
#==============================================================================
def process_site(session, site, search_terms, inputs_map, rep_path, page_limit, timeout):
    """
    Search the keywords on the website then process the search results. Generate report and capture screen shots of the matching search results for given inputs.
    """
    product_links = process_search(session, site, search_terms, inputs_map, page_limit, timeout)

    session = change_session_user_agent(session, site)
    site_results = process_products(session, site, product_links, inputs_map, rep_path)

    screenshot_urls = generate_report_xml(site_results, site, inputs_map, rep_path)

    if screen_shot_capture:
#        screenshot_urls = dict([(r[0][0]['prod_url'], [r[0][0]['screenshot_loc']]) for r in site_results.values()])
        if screenshot_urls:
            save_screenshots(screenshot_urls, site)

#==============================================================================
#
#==============================================================================
if __name__ == '__main__':
    #os.chdir('C://Users//abattula//workspace/syndy_close_loop/')
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # get all inputs
    inputs_map = get_inputs(input_file)

    # Getting unique search terms for all inputs
    search_terms = get_unique_search_terms(inputs_map)

    results_path = os.path.join(os.getcwd(), output_dir)
    dirs = os.listdir(results_path)
    run_id = str(max([int(d) for d in dirs]) + 1) if dirs else '1'

    site_threads = []
    for site in sites:
        # create a session for each website
        session = get_session(site)
        rep_path = os.path.join(os.getcwd(), output_dir, run_id, site)

        # Create a thread for the site
        arguments = (session, site, search_terms, inputs_map, rep_path, page_limit, timeout)
        t = Thread(name=site, target=process_site, args=arguments)
        t.start()

        site_threads.append(t)

    for t in site_threads:
        t.join()

