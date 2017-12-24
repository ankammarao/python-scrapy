# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 15:34:29 2016

@author: abattula
"""
import json
import time
from fuzzywuzzy import fuzz
from selenium import webdriver
import os
import sys
from threading import Thread
if sys.version[0] == '2':
    from Queue import Queue
else:
    from queue import Queue
from ssl import SSLError

from pkg.config import timeout, site_config, cookies, screenshot_threads
from pkg.dom import get_child_elements, get_value, get_child_element, parse_html
from pkg.util import check_url, print_error, create_dir

#==============================================================================
#
#==============================================================================
def get_products_details(resp, site):
    """"""
    html = parse_html(resp.content)
    collections = site_config[site]['collections']
    prod_url = str(resp.url).strip()

    details = { 'prod_url': prod_url, 'id': get_id(prod_url) }
    for collection in collections:
        _map = collection['map']
        _multiple = collection['multiple']
        #_type = collection['type']
        _value = collection['value']

        try:

            if _map == 'image-urls' and 'img_embedded' in site_config[site]:
                e = get_child_element(html, _value)
                images = []
                data_config = json.loads(get_value(e).strip())
                keys = site_config[site]['img_embedded']
                imgs = data_config[keys[0]]
                for i in range(len(imgs)):
                    images.append(site_config[site]['base_url'] + imgs[i][keys[1]][1:])
                if images:
                    details[_map] = images

            elif _multiple == 'yes':
                values = []
                for e in get_child_elements(html, _value):
                    values.append(get_value(e).strip())
                if values:
                    details[_map] = values
            else:
                e = get_child_element(html, _value)
                if e is not None:
                    details[_map] = get_value(e).strip()

            if _map == 'image-urls':
                for i in range(len(details[_map])):
                    img = details[_map][i]
                    if not img.startswith('http'):
                        details[_map][i] = site_config[site]['base_url'] + img

        except:
            pass

    return details

#==============================================================================
#
#==============================================================================
def get_id(url):
    if url.endswith('/'):
        url = url[:-1]
    return url[url.rindex('/') + 1:]

#==============================================================================
#
#==============================================================================
def is_same_product(loaded_url, original_url):
    try:
        if check_url(loaded_url, original_url):
            return True
        else:
            lid = get_id(loaded_url)
            oid = get_id(original_url)
            return lid == oid
    except:
        return False

#==============================================================================
#
#==============================================================================
def get_match_score(exp_val, act_val, **kwargs):
    """Return match score."""
    return float(fuzz.token_set_ratio(exp_val, act_val))

#==============================================================================
#
#==============================================================================
def get_score(scores, total_weightage_possible, site):
    """Checks if product is matching eqaul to or above cut-off-perc. of input"""
    cut_off_perc = site_config[site]['match_rules']['cut_off']
    cut_off_weightage = (float(total_weightage_possible) * float(cut_off_perc))/100
    total_weightage_found = sum(scores.values())

    score = total_weightage_found/len(scores)

    if total_weightage_found >= cut_off_weightage:
        return (True, score)
    else:
        return (False, score)

#==============================================================================
#
#==============================================================================
def get_input_score(html, input_, site):
    """For given product and input, compute match score"""
    scores = {}

    total_weightage_possible = 0.0
    match_elements = site_config[site]['match_rules']['matches']

    for match_item in match_elements:
        attr_name = match_item['attribute']
        attr_weightage = match_item['weightage']
        attr_value = match_item['value']
        total_weightage_possible += float(attr_weightage)
        attr_value_exp = get_value(get_child_element(input_, './/{}'.format(attr_name)))

        attr_value_actual = get_value(get_child_element(html, attr_value))
        match_item_score = get_match_score(attr_value_exp, attr_value_actual)
        scores[attr_name] = (match_item_score/100) * float(attr_weightage)

    is_matching, score = get_score(scores, total_weightage_possible, site)
    return is_matching, score

#==============================================================================
#
#==============================================================================
def get_matching_inputs(resp, site, inputs, inputs_map):
    """"""
    matching_inputs = {}
    matching_barcodes = {}
    barcodes = {i[2] for i in inputs}

    body = resp.content
    if body:
        html = parse_html(body)

        for barcode in barcodes:
            input_ = inputs_map[barcode]
            is_matching, score = get_input_score(html, input_, site)
            if is_matching:
                matching_barcodes[barcode] = score

        for i in inputs:
            barcode = i[2]
            if barcode in matching_barcodes:
                type_ = i[1]
                st = i[0]
                row_num = i[3]
                page_num = i[4]
                score = matching_barcodes[barcode]

                if barcode in matching_inputs:
                    matching_inputs[barcode].append((st, type_, score, row_num, page_num))
                else:
                    matching_inputs[barcode] = [(st, type_, score, row_num, page_num)]

    return matching_inputs

#==============================================================================
#
#==============================================================================
def get_resp(session, prod_url):
    try:
        resp = session.get(prod_url, timeout=timeout)
    except SSLError:
        if 'http:' in prod_url:
            prod_url = prod_url.replace('http:', 'https:')
            resp = session.get(prod_url, timeout=timeout)
        else:
            raise
    except:
        raise

    return resp

#==============================================================================
#
#==============================================================================
def process_product(products_details, session, prod_url, site, inputs, inputs_map, rep_path):
    """
    For given product url, get all matching inputs and their respective scores. Extract product details.
    """
    prod_details = {}
    matching_inputs = {}
    details = (prod_url, prod_details, matching_inputs)
    try:
        resp = get_resp(session, prod_url)

        if resp and resp.ok:
            if is_same_product(resp.url, prod_url):
                matching_inputs = get_matching_inputs(resp, site, inputs, inputs_map)
                if matching_inputs:
                    prod_details = get_products_details(resp, site)
                    #screenshots_dir = site_config[site]['screenshots_path']
                    #path = os.path.join(rep_path, screenshots_dir, prod_details['id'] + '.png')
                    #prod_details['screenshot_loc'] = path
                    details = (prod_url, prod_details, matching_inputs)

    except Exception as e:
        print_error(prod_url, e)
        pass

    products_details.put(details)

#    if screen_shot_capture and matching_inputs and 'screenshot_loc' in prod_details:
#        arguments = (site, prod_url, prod_details['screenshot_loc'])
#        t = Thread(target=capture_screenshot, args=arguments)
#        t.start()
##        t.join()
#        return t
#    else:
#        return None

#==============================================================================
#
#==============================================================================
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

#==============================================================================
#
#==============================================================================
def process_products(session, site, product_links, inputs_map, rep_path):
    """"""
    results = {}
    products_details = Queue()

    # process all products serially
#    screen_shot_threads = []
#    for prod_url in product_links:
#        print(prod_url)
#        inputs = product_links[prod_url]
#        t = process_product(products_details, session, prod_url, site, inputs, inputs_map, rep_path)
#        if t:
#            screen_shot_threads.append(t)
#        prod_url, prod_details, matching_inputs = products_details.get()
#        if matching_inputs:
#            for input_ in matching_inputs:
#                if input_ not in results:
#                    results[input_] = []
#                results[input_].append((prod_details, matching_inputs[input_]))
#        products_details.task_done()
#
#    for t in screen_shot_threads:
#        t.join()


    # process each product in a thread
    product_threads = []
    for prod_url in product_links:
        inputs = product_links[prod_url]
        arguments = (products_details, session, prod_url, site, inputs, inputs_map, rep_path)
        t = Thread(name=prod_url, target=process_product, args=arguments)
        t.start()
        product_threads.append(t)

    for _ in product_links:
        prod_url, prod_details, matching_inputs = products_details.get()
        if matching_inputs:
            for input_ in matching_inputs:
                if input_ not in results:
                    results[input_] = []
                results[input_].append((prod_details, matching_inputs[input_]))
        products_details.task_done()

    for t in product_threads:
        t.join()

    #print('DONE PROCESSING THE PRODUCTS', site)
    return results

#==============================================================================
#
#==============================================================================
def get_driver(c = 0):
    """"""
    if c > 5:
        return None
    try:
        driver = webdriver.PhantomJS()
        driver.maximize_window()
        driver.set_page_load_timeout(timeout)
        return driver
    except:
        time.sleep(1)
        return get_driver(c + 1)

#==============================================================================
#
#==============================================================================
def capture_screenshot(site, url, path):
    """"""
    try:
        driver = get_driver()
        if driver:
            try:
                # cookie for location
                if site == 'kruidvat' and '?country=NL' not in url:
                    url = url + '?country=NL'

                driver.get(url)

                # set cookies
                for cookie in cookies[site]:
                    driver.add_cookie(cookie)

                if not os.path.exists(os.path.dirname(path)):
                    create_dir(os.path.dirname(path))

                if not check_if_blocked(driver, site):
                    driver.save_screenshot(path)
            except:
                pass
            driver.quit()
    except:
        pass

#==============================================================================
#
#==============================================================================
def check_if_blocked(driver, site):
    if 'blocked' in site_config[site]:
        blocked = site_config[site]['blocked']
        if blocked in driver.title.lower():
            return True

    return False

#==============================================================================
#
#==============================================================================
def save_screenshots(screenshot_urls, site):
    """"""
    drivers = []
    worker_threads = []

    q = Queue()
    for url, paths in screenshot_urls.items():
#        print url
        q.put((url, paths))

    no_of_workers = min(len(screenshot_urls), screenshot_threads)

    for i in range(no_of_workers):
        driver = get_driver()
        drivers.append(driver)
        t = Thread(target=worker, args=(driver, q, site))
        t.setDaemon(True)
        worker_threads.append(t)
        t.start()

    q.join()

    for driver in drivers:
        driver.quit()

#==============================================================================
#
#==============================================================================
def save_png(png, path):
    """Save screen shot data to disk"""
    if not os.path.exists(os.path.dirname(path)):
        create_dir(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(png)
        f.flush()

#==============================================================================
#
#==============================================================================
def worker(driver, q, site):
    """"""
    while True:
        url, paths = q.get()
#        print(url)
        try:
            # cookie for location
            if site == 'kruidvat' and '?country=NL' not in url:
                url = url + '?country=NL'

            driver.get(url)

            # set cookies
            for cookie in cookies[site]:
                driver.add_cookie(cookie)

            # check if site is blocked
            if not check_if_blocked(driver, site):
                png = driver.get_screenshot_as_png()

#                scr_thrds = []
                for path in paths:
                    save_png(png, path)
#                    t = Thread(target=save_png, args=(png, path))
#                    t.start()
#                    scr_thrds.append(t)
#
#                for t in scr_thrds:
#                    t.join()
        except:
            pass
        q.task_done()