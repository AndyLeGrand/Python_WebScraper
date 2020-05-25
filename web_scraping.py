"""
This program connects to the website "ebay-kleinanzeigen.de", which is sort of the German version of Craigslist.
The objective is to extract information from the website and make it accessible for further analysis.
So far, the program focuses on used cars, but could be simply modified to search in other categories as well.
Usage:
>python web-scrapping.py
    -m [specify make of desired car]
    -my [optional: year or model]
    -b [browser mode: True (headless) or False (visible browser]
"""

import time
import argparse
import math
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup


WEBSITE = "https://www.ebay-kleinanzeigen.de"
SEARCH_RESULTS_PER_PAGE = 25
MAX_PAGES = 50


def main():
    with open("Output\\results.csv", "w") as f:
        f.write("Title, Mileage, Year, Price\n")
    # parse options given by user
    options = parse_arguments()

    # create browser instance
    firefox_driver = create_driver_with_options(options.browser)

    # go to website, place search and get number of results
    url = construct_url(WEBSITE, options.make, options.model_or_year)
    firefox_driver.get(url)
    num_results = find_number_search_results(firefox_driver)
    num_pages_results = number_results_pages(num_results)

    # extract listings found for search
    for page_num in range(1, num_pages_results + 1):
        url = construct_url(WEBSITE, options.make, options.model_or_year, page_num)
        html_body = get_html_from_website(url)
        results_dict = extract_listings_from_html(html_body)
        write_dict_to_csv("Output\\results.csv", results_dict)
        time.sleep(1)

    firefox_driver.close()


def construct_url(page_to_be_crawled, car_make, car_model_or_year, page_num=1):
    if car_model_or_year == "":
        url = "{}/s-autos/seite:{}/{}/k0c216".format(page_to_be_crawled, page_num, car_make)
    else:
        url = "{}/s-autos/seite:{}/{}-{}/k0c216".format(page_to_be_crawled, page_num, car_make, car_model_or_year)
    return url


def parse_arguments():
    parser = argparse.ArgumentParser(
        usage=(
            "    -m <make of car>\n"
            "    -my <make or year of car>\n"
            "    -b <browser mode headless> True / False; default is True"
        ),
    )
    parser.add_argument("-m", "--make", dest="make", required=True)
    parser.add_argument("-my", "--model_or_year", dest="model_or_year", default="")
    parser.add_argument("-b", "--browser", dest="browser", default="True")
    options = parser.parse_args()
    return options


def find_number_search_results(driver):
    """
    find the number of search results for a particular search
    :param driver: webdriver instance
    :return: num_results
    """
    tag_results = driver.find_element_by_xpath('//span[@class="breadcrump-summary"]')
    string_results = tag_results.text.split()
    num_results = float(string_results[4])
    return num_results


def number_results_pages(num_results):
    """
    get the number of result pages for a particular search
    """
    num_pages = math.ceil(num_results / SEARCH_RESULTS_PER_PAGE)
    if num_pages > 50:
        return 50
    else:
        return num_pages


def extract_listings(url, driver):
    """
    this function extracts listings using selenium, based on tags with the keyword driver
    :param url: page to be crawled
    :param driver: webdriver instance
    :return: a list of search results
    """
    driver.get(url)
    search_results = []
    listings = driver.find_elements_by_class_name("ellipsis")

    num_listings = len(listings)
    for i in range(num_listings):
        listing = listings[i].text
        search_results.append(listing)
    return search_results


def get_html_from_website(url):
    """
    this function extracts a website's html body
    :param url: page to be crawled
    :return:
    """
    page = requests.get(url)
    html_body = BeautifulSoup(page.text, "html.parser")
    return html_body


def extract_listings_from_html(html_body):
    """
    this function takes the body of a website's html as input
    it then extracts certain elements from it and populates a dict with it.
    :param html_body: the website's html body
    :return: dict_listings: a dict of the extracted html elements
    """
    listings = html_body.find_all("article", class_="aditem")
    num_listings = len(listings)
    dict_listings = {}
    for i in range(num_listings):
        title = listings[i].a.text
        mileage = listings[i].find_all("span")[0].text
        year = listings[i].find_all("span")[1].text
        price = listings[i].strong.text
        dict_listings[i] = title, mileage, year, price
    return dict_listings


def write_dict_to_csv(csv_file, dict_r):
    """
    This function takes a csv file and a dictionary is inputs. It unpacks the the
    dictionaries values and writes them to the specified csv file.
    :param csv_file: destination csv_file
    :param dict_r: input dict
    :return: csv_file with dict values
    """
    with open(csv_file, "a") as f:
        for key in dict_r.keys():
            f.write("{},{},{},{}\n".format(dict_r[key][0], dict_r[key][1], dict_r[key][2], dict_r[key][3]))
    return csv_file


def create_driver_with_options(browser_mode):
    firefox_options = FirefoxOptions()
    firefox_options.headless = browser_mode
    driver = webdriver.Firefox(options=firefox_options)
    return driver


if __name__ == '__main__':
    main()
