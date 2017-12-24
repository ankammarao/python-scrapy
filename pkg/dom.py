# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 15:30:44 2016

@author: abattula
"""
from lxml import etree

#==============================================================================
#
#==============================================================================
def create_root(name='results'):
    "Create and return root element."
    return etree.Element(name)

#==============================================================================
#
#==============================================================================
def create_dom(element):
    "Return dom tree."
    return etree.ElementTree(element)

#==============================================================================
#
#==============================================================================
def save_dom(dom_obj, xml_file, xml_declaration=True, pretty_print=True, encoding='utf-8'):
    "Writes dom document into xml file."
    dom_obj.write(xml_file, xml_declaration=True, pretty_print=True, encoding='utf-8')

#==============================================================================
#
#==============================================================================
def add_child(parent, child_name, **kwargs):
    "Adds child element to parent and returns it."
    return etree.SubElement(parent, child_name, **kwargs)

#==============================================================================
#
#==============================================================================
def get_child_elements(ref_element, xpath):
    "Finds all matching elements by XPATH and returns those in a list."
    return ref_element.xpath(xpath)

#==============================================================================
#
#==============================================================================
def get_child_element(ref_element, xpath):
    "Finds all matching elements by XPATH and returns the firts element."
    if ref_element.xpath(xpath):
        return ref_element.xpath(xpath)[0]
    else:
        return None

#==============================================================================
#
#==============================================================================
def get_value(element):
    "Rerurns element text or one of its attribute values."
    if element.__class__.__name__ == '_Element':
        return " ".join(element.xpath('descendant-or-self::text()'))
    elif element.__class__.__name__ == '_ElementUnicodeResult':
        return element
    elif element.__class__.__name__ == '_ElementStringResult':
        return element
    else:
        return None

#==============================================================================
#
#==============================================================================
def get_inputs(prod_cfg):
    """Return all product elements."""
    inputs = etree.parse(prod_cfg).xpath('//input')
    #xmltodict.parse(xml)['inputs']['input']
    barcodes = [str(i.find('barcode').text.encode('ascii','ignore').decode('utf-8')).strip() for i in inputs]
    inputs_map = dict(zip(barcodes, inputs))
    return inputs_map

#==============================================================================
#
#==============================================================================
def parse_html(html_content):
    "Parses HTML content and returns root element."
    return etree.HTML(html_content)