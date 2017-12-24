# -*- coding: utf-8 -*-
"""
Created on Fri Dec 23 15:35:51 2016

@author: abattula
"""

import os

from pkg.config import site_config
from pkg.dom import create_root, create_dom, save_dom, add_child, get_child_elements, get_value
from pkg.util import create_dir

#==============================================================================
#
#==============================================================================
def convert_search_item(s):
    return str(s.encode('ascii','ignore').decode('utf-8')).strip().replace(' ', '+')

#==============================================================================
#
#==============================================================================
def map_products_inputs(site_results, inputs_map):
    """"""
    input_search_products_map = {}
    for barcode, _input in inputs_map.items():
        search_products_map = {}
        if barcode in site_results:
            search_term_elems = get_child_elements(_input, './/search-terms/search-term/value')
            search_items = [get_value(search_term_elem) for search_term_elem in search_term_elems]
            search_products_map = dict([((convert_search_item(st), 'search-term'), []) for st in search_items])
            pn = convert_search_item(_input.find('name').text)
            search_products_map[(pn, 'product-name')] = []

            details = site_results[barcode]
            for pd, sis in details:
                for si in sis:
                        st = si[0]
                        _type = si[1]
                        score = si[2]
                        row_num = si[3]
                        page_num = si[4]

                        search_products_map[(st, _type)].append((pd, score, row_num, page_num))
        input_search_products_map[barcode] = search_products_map
    return input_search_products_map

#==============================================================================
#
#==============================================================================
def generate_report_xml(site_results, site, inputs_map, rep_path):
    screenshots = {}
    input_search_products_map = map_products_inputs(site_results, inputs_map)

    rep_name = site_config[site]['report_name']
    cur_type = site_config[site]['currency_symbol']
    pg_size = site_config[site]['page_size']
    screenshots_dir = site_config[site]['screenshots_path']

    results_elem = create_root()
    dom_obj = create_dom(results_elem)

    for barcode, _input in inputs_map.items():
        #
        search_products_map = input_search_products_map.get(barcode, [])

        result_elem = add_child(results_elem, 'result')
        result_elem.append(_input)
        output_elem = add_child(result_elem, 'output')
        search_results_elem = add_child(output_elem, 'search-results')
        #
        search_term_elems = get_child_elements(_input, './/search-terms/search-term/value')
        search_items = [get_value(search_term_elem) for search_term_elem in search_term_elems]
        search_items.insert(0, _input.find('name').text)

        for idx, search_item in enumerate(search_items):
            if idx == 0:
                search_result_elem = add_child(search_results_elem, 'search-result', type='product-name')
            else:
                search_result_elem = add_child(search_results_elem, 'search-result', type='search-term')
            search_item_elem = add_child(search_result_elem, 'search-item')
            search_item_elem.text = search_item
            found_elem = add_child(search_result_elem, 'found')
            found_elem.text = 'false'
            matches_elem = add_child(search_result_elem, 'matches')

            for search, products in search_products_map.items():
                if search[0] == convert_search_item(search_item):
                    for product, score, row_num, page_num in products:
                        matches_elem.getparent().find('found').text = 'true'
                        match_elem = add_child(matches_elem, 'match')
                        match_url_elem = add_child(match_elem, 'match-url')
                        match_url_elem.text = product['prod_url']

                        screenshot_elem = add_child(match_elem, 'screenshot')
                        #if 'screenshot_loc' in product:
                            #screenshot_elem.text = product['screenshot_loc']
                        img_name = _input.find('name').text + '_' + search_item + '_' + str(page_num) + '_' + str(row_num) +'.PNG'
                        screenshot_loc = os.path.join(rep_path, screenshots_dir, img_name)
                        screenshot_elem.text = screenshot_loc

                        if not product['prod_url'] in screenshots:
                            screenshots[product['prod_url']] = []
                        screenshots[product['prod_url']].append(screenshot_loc)


                        categories_elem = add_child(match_elem, 'categories')
                        if 'categories' in product:
                            for category in product['categories']:
                                category_elem = add_child(categories_elem, 'category')
                                cat_val_elem = add_child(category_elem, 'value')
                                cat_val_elem.text = category

                        position_elem = add_child(match_elem, 'position')
                        row_index_elem = add_child(position_elem, 'index-on-page')
                        row_index_elem.text = str(row_num)
                        pg_no_elem = add_child(position_elem, 'page-number')
                        pg_no_elem.text = str(page_num)
                        pg_size_elem = add_child(position_elem, 'page-size')
                        pg_size_elem.text = str(pg_size)

                        prices_elem = add_child(match_elem, 'prices')
                        selling_price_elem = add_child(prices_elem, 'selling_price')
                        selling_price_cur = add_child(selling_price_elem, 'currency')
                        if 'currency' in product:
                            selling_price_cur.text = product['currency']
                        else:
                            selling_price_cur.text = cur_type
                        selling_price_val = add_child(selling_price_elem, 'value')
                        if 'selling_price' in product:
                            selling_price_val.text = product['selling_price']
                        standard_price_elem = add_child(prices_elem, 'standard_price')
                        standard_price_cur = add_child(standard_price_elem, 'currency')
                        standard_price_cur.text = cur_type
                        standard_price_val = add_child(standard_price_elem, 'value')
                        if 'standard_price' in product:
                            standard_price_val.text = product['standard_price']

                        score_elem = add_child(match_elem, 'score')
                        score_elem.text = str(score)

                        data_elem = add_child(match_elem, 'data')
                        prod_summ_elem = add_child(data_elem, 'product-summary')
                        for prod_summary_item in filter(lambda col: col['type'] == 'product_summary', site_config[site]['collections']):
                            if prod_summary_item['map'] in product:
                                if prod_summary_item['multiple'] == 'yes':
                                    level1_elem = add_child(prod_summ_elem, prod_summary_item['map'])
                                    for el in product[prod_summary_item['map']]:
                                        child_elem = add_child(level1_elem, prod_summary_item['map'][:-1])
                                        child_elem_value = add_child(child_elem, 'value')
                                        child_elem_value.text = el
                                else:
                                    child_elem = add_child(prod_summ_elem, prod_summary_item['map'])
                                    data_match_elem = add_child(child_elem, 'data-match')
                                    data_match_found = add_child(data_match_elem, 'found')
                                    data_match_found.text = 'true'
                                    data_match_score = add_child(data_match_elem, 'score')
                                    data_match_score.text = str(score)
                                    child_elem_value = add_child(child_elem, 'value')
                                    child_elem_value.text = product[prod_summary_item['map']]

                        attributes_elem = add_child(data_elem, 'attributes')
                        attributes_elem.text = ''

    create_dir(rep_path)
    save_dom(dom_obj, os.path.join(rep_path, rep_name))
    return screenshots
