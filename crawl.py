#!/usr/bin/env python3
import os
import sys

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver

import json
import argparse
from jinja2 import Template

JSON_OUT = 'data/results.json'
link = "https://www.kleinanzeigen.de/s-multimedia-elektronik/leipzig/anbieter:privat/anzeige:angebote/preis::500/%s/c161l4233"

def get_args():
    parser = argparse.ArgumentParser(description='Crawl ebay kleinanzeigen', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--url', default=link, help='The start url. Must have a [percent-sign]s portion in the url to insert the "options" like the page num, price etc.')
    parser.add_argument('--page-start', default=1, type=int, help='The page number to start at')
    parser.add_argument('--page-end', default=1, type=int, help='The page number to end at')
    parser.add_argument('--json-out', default=JSON_OUT, help='The path for the output json.')
    parser.add_argument('--options', default='', help='Options for kleinanzeigen. Get from the site. Example: "--options preis:0:20"')
    args = parser.parse_args()
    if args.options:
        args.url = args.url % (args.options + '/%s')
    return args

def resource_path(relative_path) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(__file__)
    return str(os.path.join(base_path, relative_path))

def main():
    args = get_args()
    service = Service(resource_path('./driver/geckodriver.exe'))
    browser: WebDriver = webdriver.Firefox(service=service)

    results = []
    print("Starting to crawl. Options:\n{}\n".format(args))
    for page_num in range(args.page_start, args.page_end + 1):
        url = args.url % ('seite:' + str(page_num))
        print("\tCrawling page: {:2}/{:2} ({})".format(page_num, args.page_end, url))
        results += get_results(browser, url)
    browser.quit()
    with open(args.json_out, 'w') as f:
        json.dump(results, f, indent=4, sort_keys=True)
    render(results)


def render(ads):
    template = Template(open('index.html.tpl').read())
    with open('data/index.html', 'w', encoding="utf-8") as f:
        f.write(template.render(ads=ads))


def get_results(browser: WebDriver, url):
    browser.get(url)
    results = []
    for el in browser.find_elements(By.CSS_SELECTOR, 'article.aditem'):
        try:
            try:
                # Schließe beworbene Anzeigen aus
                el.find_element(By.XPATH, './ancestor::*[contains(@class, "is-topad")]')
                continue
            except NoSuchElementException:
                pass

            out = {"link": el.find_elements(By.CSS_SELECTOR, 'a[href^="/s-anzeige"]')[0].get_attribute('href'),
                   "title": el.find_elements(By.CSS_SELECTOR, '.text-module-begin a')[0].text.strip(),
                   "desc": el.find_elements(By.CSS_SELECTOR, '.aditem-main p')[0].text.strip(),
                   "price": el.find_elements(By.CSS_SELECTOR, '.aditem-main--middle--price-shipping p')[0].text.strip(),
                   "added": el.find_elements(By.CSS_SELECTOR, '.aditem-main--top--right')[0].text.strip(),
                   "img": el.find_elements(By.CSS_SELECTOR, '.aditem-image img')[0].get_attribute('srcset').strip(),
            }
            results.append(out)
        except IndexError:
            continue
    return results

if __name__ == '__main__':
    main()
