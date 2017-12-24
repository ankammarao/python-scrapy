# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 15:41:25 2016

@author: abattula
"""
import sys
if sys.version[0] == '2':
    from Queue import Queue
else:
    from queue import Queue
from threading import Thread

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from pkg.config import timeout, site_config
from pkg.dom import get_child_elements, get_value, get_child_element, parse_html
from pkg.util import check_url, get_site

#==============================================================================
"""
search_url = 'https://www.walmart.com/search/?query=nivea&page=1'
search_url = 'https://www.bol.com/nl/s/index.html?page=1&searchtext=nivea'
search_url = 'https://www.kruidvat.nl/search?size=20&sort=score&page=0&q=nivea'
search_url = 'http://www.jumbo.com/producten?PageNumber=0&SearchTerm=nivea'
"""
#==============================================================================
def build_search_url(base, search_key, st, page_key, page_num, order):
    """Build search url"""
    if order:
        url = base + search_key + st + page_key + str(page_num)
    else:
        url = base + page_key + str(page_num) + search_key + st

    return url

#==============================================================================
#
#==============================================================================
def check_if_product(search_url, resp_url, site, rec=True):
    """"
    Check if the response is redirected to the product page. If redirected to product page, return the response link, otherwise None.
    """
    if 'prod_end_flag' in site_config[site]:
        end = resp_url.find(site_config[site]['prod_end_flag'])
        if end >= 0:
            resp_url = resp_url[:end]

    if site == 'jumbo':
        if 'jumbo.com:' in resp_url:
            return (True, resp_url)
        elif 'jumbo.com/INTERSHOP' in resp_url:
            if 'PageNumber=0' in search_url and rec:
                return (True, None)

    elif site == 'bol':
        if 'bol.com/nl/p' in resp_url:
            return (True, resp_url)

    elif site == 'walmart':
        if 'walmart.com/ip/' in resp_url:
            return (True, resp_url)

    elif site == 'kruidvat':
        if filter(None, resp_url.split('/'))[-2] == 'p':
            return (True, resp_url)

    return (False, None)

#==============================================================================
#
#==============================================================================
def get_product_links(session, site, resp, search_url, base_url, st, row_loc, prod_link, page_num):
    """"""
    if check_url(resp.url, search_url):
        html = resp.content
        return process_page(base_url, html, st, row_loc, prod_link, page_num)
    else:
        is_product, prod_url = check_if_product(search_url, resp.url, site)
        if is_product:
            if prod_url:
                if 'prod_end_flag' in site_config[site]:
                    end = prod_url.find(site_config[site]['prod_end_flag'])
                    if end >= 0:
                        prod_url = prod_url[:end]
                return set([(st, str(prod_url).strip(), 0, page_num)])
            else:
                r = session.get(site_config['jumbo']['search_url'] + st)
                return get_product_links(session, site, r, search_url, base_url, st, row_loc, prod_link, page_num)
        else:
            #print search_url + "\n>>> " + resp.url + '\n'
            return set([])

#==============================================================================
#
#==============================================================================
def search_with_requests(session, site, st, search_base_url, search_key, page_key, page_num, order, base_url, row_loc, prod_link):
    """Searching using requests module"""
    links = set([])
    try:
        search_url = build_search_url(search_base_url, search_key, st, page_key, page_num, order)
        resp = session.get(search_url, timeout=timeout)
        links_ = get_product_links(session, site, resp, search_url, base_url, st, row_loc, prod_link, page_num)
        links = links | links_
    except:
        pass
    return links

#==============================================================================
#
#==============================================================================
def process_search_term(site, site_wise_prod_links, session, base_url, search_base_url, search_key, page_key, page_start_index, order, search_term, row_loc, prod_link, pg_limit=2, timeout=300):
    """
    Process a search term. Get the search results and process them to get product urls.
    """
    st = search_term[0].strip()
    links = set([])
    if page_start_index == 1:
        pg_limit += 1

    # TODO: Use threads
    for i in range(page_start_index, pg_limit):
        page_links = search_with_requests(session, site, st, search_base_url, search_key, page_key, i, order, base_url, row_loc, prod_link)
        links = links | page_links
#    return links
    site_wise_prod_links.put(links)

#==============================================================================
#
#==============================================================================
def process_page(base_url, html, st, row_loc, prod_link, page_num, **kwargs):
    """Process search result page shown in UI."""

    html_root = parse_html(html)

    rows = get_child_elements(html_root, row_loc)

    links = set([])
    for index, row in enumerate(rows):
        row_link = get_value(get_child_element(row, prod_link))
        if not row_link.startswith('http'):
            row_url = base_url + row_link
        else:
            row_url = row_link

        site = get_site(row_url)
        if site and 'prod_end_flag' in site_config[site]:
            end = row_url.find(site_config[site]['prod_end_flag'])
            if end >= 0:
                row_url = row_url[:end]

        links.add((st, str(row_url).strip(), index, page_num))

    return links

#==============================================================================
#
#==============================================================================
def get_unique_search_terms(inputs_map):
    """
    Get all unique search terms for all inputs as map of search-term, list of barcodes of respective inputs
    """
    search_terms = {}
    for barcode, _input in inputs_map.items():
        #xmltodict.parse(xml)['inputs']['input'][0]['search-terms']['search-term']
        search_term_elems = get_child_elements(_input, './/search-terms/search-term/value')
        search_items = [get_value(search_term_elem) for search_term_elem in search_term_elems]

        for st in search_items:
            st = st.encode('ascii','ignore').decode('utf-8')
            st = str(st).strip().replace(' ', '+')
            if st in search_terms:
                search_terms[st].add((st, 'search-term', barcode))
            else:
                search_terms[st] = set([(st, 'search-term', barcode)])

        # Add input product name to search items
        pn = _input.find('name').text.encode('ascii','ignore').decode('utf-8')
        pn = str(pn).strip().replace(' ', '+')
        if pn in search_terms:
            search_terms[pn].add((pn, 'product-name', barcode))
        else:
            search_terms[pn] = set([(pn, 'product-name', barcode)])

    return search_terms

#==============================================================================
#
#==============================================================================
def process_search(session, site, search_terms, inputs_map, pg_limit=2, timeout=timeout):
    """
    For given website, search all the required terms and return the product links in all search result pages, limited by page_limit.
    """
    site_wise_prod_links = Queue()

        # Get site configuration
    base_url = site_config[site]['base_url']
    search_base_url = site_config[site]['search_base_url']
    search_key = site_config[site]['search_key']
    page_key = site_config[site]['page_key']
    page_start_index = site_config[site]['page_start_index']
    order = site_config[site]['order']
    row_loc = site_config[site]['row_loc']
    prod_link = site_config[site]['prod_link']

    # Create a thread for each search item
    search_threads = list()
    for search_term in search_terms.items():
        arguments = (site, site_wise_prod_links, session, base_url, search_base_url, search_key, page_key, page_start_index, order, search_term, row_loc, prod_link, pg_limit, timeout)
        t = Thread(name = search_term[0], target=process_search_term, args=arguments)
        search_threads.append(t)
        t.start()

    # for each thread collect the results
    # process as thread is completed
    product_links = {}
    for _ in search_threads:
        # (search-term, product-url, row_index, page_num)
        links = site_wise_prod_links.get()
        for link in links:
            st = link[0]
            prod_url = link[1]
            row_num = link[2]
            page_num = link[3]

            prod_search_items = search_terms[st]
            prod_search_items = {s + (row_num, page_num) for s in prod_search_items}

            if prod_url in product_links:
                prod_search_items = prod_search_items | product_links[prod_url]

            product_links[prod_url] = prod_search_items
        site_wise_prod_links.task_done()

    # wait unitl all threads are done. not necessary.
    for t in search_threads:
        t.join()

    # generate report
    return product_links