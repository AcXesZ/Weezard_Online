from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import csv
import jinja2
import os
import re
import time


#set bs4 driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

def prod_parse_sun():
    store_name = 'SUN'

    driver.get('https://www.sunnyside.shop/menu/philadelphia-pa/products/flower?strain_types=sativa')
    time.sleep(3)

    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, "html.parser")

    store_name = soup.find('p', class_="Dropdown__StlStoreName-sc-t2betb-1")
    store_name = store_name.text
    store_name = store_name.split('-')
    store_name = store_name[1]
    store_name = store_name.strip()

    #print(soup.prettify())

    product_buttons = soup.select('button[data-cy="ProductListItem"]')

    print(f'I got {len(product_buttons)} products.')
    for btn in product_buttons:
        soup = (btn).prettify()
        #print(f'{soup}\n')

        #strain
        prod_strain = btn.find('span', class_="MuiChip-label")
        prod_strain = prod_strain.text
        #print(f'Product Strain: {prod_strain}')

        #grower
        prod_grower = btn.find('h5', class_="preheader")
        prod_grower = prod_grower.text
        #print(f'Product Grower: {prod_grower}')

        prod_name = btn.find('h4', class_="jss192")
        prod_name = prod_name.text
        print(f'Raw name : {prod_name}')

        #prod type
        prod_type = 'Flower'
        if 'Lightly Ground Flower' in prod_name:
            prod_type = 'Lightly Ground Smalls'
        if 'Lightly Ground Trim' in prod_name:
            prod_type = 'Lightly Ground Trim'
        if 'Ground Flower' in prod_name:
            prod_type = 'Ground Flower'
        if 'Small' in prod_name:
            prod_type = 'Small'
        if 'Smalls' in prod_name:
            prod_type = 'Smalls'
        if 'Fine Grind Flower' in prod_name:
            prod_type = 'Fine Grind Flower'
        #print(f'Product type: {prod_type}')

        words_to_remove = ['Flower', 'Lightly', 'Ground', 'Smalls', 'Small', 'Trim', 'Fine']
        for word in words_to_remove:
            prod_name = prod_name.replace(word, '')
        #print(f'product name: {prod_name}')

        prod_weight = btn.find('span', class_="gray")
        prod_weight = prod_weight.text
        prod_weight = prod_weight.replace('g', '')
        prod_weight = float(prod_weight)
        #print(f'weight: {prod_weight}')

        prod_price = btn.find('span', class_="sc-eLwHnm")
        prod_price = prod_price.text
        prod_price = prod_price.strip('$')
        prod_price = float(prod_price)
        #print(f'Price: {prod_price}')

        #thc%
        prod_h6s = btn.find_all('h6')

        prod_thc = None
        thc_values = []
        for h6 in prod_h6s:
            if prod_thc is None:
                if '%' in h6.text:
                    prod_thc = h6.text
                    prod_thc = prod_thc.strip('%')
                    prod_thc = float(prod_thc)

        #print(f'THC%: {prod_thc}')

        # calculate total mg of thc in weight
        prod_mg_thc = ((prod_thc / 100) * (prod_weight * 1000))
        #print(f'Total mG THC : {prod_mg_thc:.2f}')

        # calculate cents per milligram of thc
        prod_price_per_mg = (prod_price / prod_mg_thc)
        #print(f"Price per mg : {prod_price_per_mg:.3f}")

        row = [f'{store_name}',
               f'{prod_name}',
               f'{prod_strain}',
               f'{prod_grower}',
               f'{prod_type}',
               f'${prod_price:.2f}',
               f'{prod_weight}g',
               f'{prod_thc:.2f}%',
               f'{prod_mg_thc:.2f}mg',
               f'{prod_price_per_mg:.3f}/mg']

        csv_write_row(row)

def csv_write_row(row):
    # Create a csv file
    with open('../prod_all.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(row)


if __name__ == '__main__':
    prod_parse_sun()



