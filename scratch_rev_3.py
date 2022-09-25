from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import csv
import jinja2
import os
import re
import time


try:
    os.remove("prod_csv_all.csv")
except Exception as error:
    pass

with open('prod_csv_all.csv', 'w') as f:
    f.write('')

with open('prod_csv_all.csv', 'a') as f:
    f.writelines('store name, name, strain, grower, type, price, weight, thc%, total mg, cost/mg\n')

#set bs4 driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

def prod_parse_ihj(filter):
    store_name = 'BH'

    #class names
    cn_link = "css-6tz98n"
    cn_href = "css-1fbb79j"
    cn_grower = "css-1ad3qm0"
    cn_type_container = "css-m6dbny"
    cn_type = "css-1ad3qm0"
    cn_price = "css-hihqzq"
    cn_thc_container = "css-g89h0y"
    cn_thc = "css-1ad3qm0"
    cn_weight = "css-lh59bd"

    if filter == 'hybrid':
        url = url_ihj_hybrid

    if filter == 'indica':
        url = url_ihj_indica

    if filter == 'sativa':
        url = url_ihj_sativa

    driver.get(url)
    time.sleep(3)

    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, "html.parser")

    #get all the product divs
    product_divs = soup.find_all("div", class_="css-1alyybx")
    print(len(product_divs))

    for data in soup(['svg', 'path',' style', 'script', 'img', 'button']):
        # Remove tags
        data.decompose()

    #write the soup to a file
    with open(f'./soups/soup_ihj_{filter}.html', 'w', encoding="utf-8") as f:
        f.write(soup.prettify())

    #parse the product divs
    for product_div in product_divs:
        try:

            #get link
            prod_link_tag = product_div.find("span", class_=cn_link).find("a", href=True)
            prod_href = prod_link_tag['href']
            print(f'HREF: {prod_href}')

            #get name
            prod_name = product_div.find("div", class_=cn_href).text
            prod_name =  prod_name.strip('|')
            print(f"Name: {prod_name}")
            prod_name = f'<a href="http://www.iheartjane.com{prod_href}">{prod_name}</a> | <a href="https://www.leafly.com/search?q={prod_name}">Leafly</a>'

            #get species indica/sative/hybrid
            prod_strain = filter

            #get grower
            prod_grower = product_div.find("div", class_=cn_grower).text
            print(f"Grower: {prod_grower}")

            #get type flower/fine grind/cache/etc...
            prod_type = product_div.find("div", class_=cn_type_container).find("div", class_=cn_type).text
            print(f"Type: {prod_type}")

            #get price
            prod_price = float(product_div.find("p", class_=cn_price).text[1:6])
            print(f"Price : {prod_price:.2f}")

            #get thc%
            prod_thc = float(product_div.find("div", class_=cn_thc_container).find("div", class_=cn_thc).text[4:9])
            print(f"%THC : {prod_thc}")

            #get weight
            prod_weight = product_div.find("p", class_=cn_weight).text
            if prod_weight == '':
                prod_weight = 0.00
            #remove non-decimals
            non_decimal = re.compile(r'[^\d.]+')
            prod_weight = float(non_decimal.sub('', prod_weight))
            #special case: if weight is something like 1g/3.5g the expression will return back 13.5
            if prod_weight == 13.5:
                prod_weight = 3.5
            print(f"Weight : {prod_weight}")

            #calculate total mg of thc in weight
            prod_mg_thc = ((prod_thc/100) * (prod_weight * 1000))
            print(f"Total mG THC : {prod_mg_thc:.2f}")

            #calculate cents per milligram of thc
            prod_price_per_mg = (prod_price / prod_mg_thc)
            print(f"Price per mg : {prod_price_per_mg:.3f}")

            print('\n')

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

        except Exception as error:
            print(f"{error}")

def prod_parse_dut(filter):
    store_name = 'KC'

    if filter == 'hybrid':
        url = url_dut_hybrid

    if filter == 'indica':
        url = url_dut_indica

    if filter == 'sativa':
        url = url_dut_sativa

    driver.get(url)
    time.sleep(0.5)
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 5):
        driver.execute_script("window.scrollTo(0, {});".format(i))
    time.sleep(0.5)

    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, "html.parser")

    #get all the product divs
    product_divs = soup.find_all("div", class_=re.compile("^desktop-product-list-item__Container"))
    print(len(product_divs))
    for data in soup(['svg', 'path',' style', 'script']):
        # Remove tags
        data.decompose()

    #write the soup to a file
    with open(f'soups/soup_dut_{filter}.html', 'w', encoding="utf-8") as f:
        f.write(soup.prettify())

    #parse the product divs
    for product_div in product_divs:
        try:
            #get link
            prod_link_tag = product_div.find("a", href=True)
            href = prod_link_tag['href']
            print(href)
            prod_href = f'href="http://www.dutchie.com{href}'
            print(f'HREF: {prod_href}')

            #get type flower/fine grind/cache/etc...
            prod_type = product_div.find("div", class_=re.compile("^desktop-product-list-item__ProductName")).text
            if 'Small Flower' in prod_type:
                prod_type = 'Small Flower'

            if 'Ground Flower' in prod_type:
                prod_type = 'Ground Flower'

            if 'Small Flower' not in prod_type and 'Ground Flower' not in prod_type:
                prod_type = 'Flower'

            print(f"Type: {prod_type}")

            #get name
            prod_name = product_div.find("div", class_=re.compile("^desktop-product-list-item__ProductName")).text
            chars_to_strip = [ 'AYR - ', 'AK - ', 'FX - ', 'GTI - ', 'GR - ', 'R - ', 'AY - ',
                               'R - ', 'MI - ', 'PW - ', 'PC - ', 'KT - ',
                               '[H]', '[I]', '[SDH]','[IDH]', '[S]', 'Flower']
            for chars in chars_to_strip:
                prod_name = prod_name.replace(chars, '')

            print(f"Name: {prod_name}")
            prod_name = f'<a {prod_href}">{prod_name}</a> | <a href="https://www.leafly.com/search?q={prod_name}">Leafly</a>'

            #get species indica/sative/hybrid
            prod_strain = filter

            #get grower
            prod_grower = product_div.find("span", class_=re.compile("^desktop-product-list-item__ProductBrand")).text
            print(f"Grower: {prod_grower}")

            #get price
            prod_price = float(product_div.find("span", class_=re.compile("^weight-tile__PriceText")).text[1:6])
            print(f"Price : {prod_price:.2f}")

            #get thc%
            prod_thc = product_div.find("div", class_=re.compile("^desktop-product-list-item__PotencyInfo")).text
            # remove non-decimals
            non_decimal = re.compile(r'[^\d.]+')
            prod_thc = float(non_decimal.sub('', prod_thc))
            print(f"%THC : {prod_thc}")

            #get weight
            prod_weight = product_div.find("span", class_=re.compile("^weight-tile__Label")).text
            if prod_weight == '':
                prod_weight = '0'

            if '1/8' in prod_weight:
                prod_weight = '3.5'

            if '1/4' in prod_weight:
                prod_weight = '7.0'

            if '1g' in prod_weight:
                prod_weight = '1.0'

            prod_weight = float(prod_weight)

            print(f"Weight : {prod_weight}")

            #calculate total mg of thc in weight
            prod_mg_thc = ((prod_thc/100) * (prod_weight * 1000))
            print(f"Total mG THC : {prod_mg_thc:.2f}")

            #calculate cents per milligram of thc
            prod_price_per_mg = (prod_price / prod_mg_thc)
            print(f"Price per mg : {prod_price_per_mg:.3f}")

            print('\n')

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

        except Exception as error:
            print(f"{error}")

def csv_write_row(row):
    # Create a csv file
    with open('prod_csv_all.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(row)


def html_write():
    df1 = pd.read_csv('prod_csv_all.csv')
    df1.drop_duplicates(inplace=True)
    #del df1[df1.columns[0]]
    df1.style.format(precision=3)

    df1.columns = ['Store',
                   'Name',
                   'Strain',
                   'Grower',
                   'Type',
                   'Price',
                   'Weight',
                   'THC%',
                   'THC mg',
                   '$/mg',
                   ]

    #print("The dataframe is:")
    #print(df1)

    html_string = ''
    html_string += df1.to_html(escape=False)
    html_string = html_string.replace('<table', '<table id="table_id"')

    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    t = env.get_template("template.html")
    rendered_template = t.render(body=html_string)

    with open('prod_table.html', 'w') as f:
        f.write(rendered_template)

def get_menus():
    innerHTML = driver.get("https://www.sunnyside.shop/locations")
    time.sleep(5.5)

    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, "html.parser")
    print(soup.prettify())


'''
    dispensary_link_list = []

    dispensaries = soup.find_all("div", class_="col-xs-9")

    for dispensary in dispensaries:
        dispensary_anchor = dispensary.find("a", href=True)
        dispensary_name = dispensary_anchor.text
        dispensary_link_list.append(dispensary_name)

    dispensary_link_list.sort()
    return dispensary_link_list'''

#run
get_menus()
'''
prod_parse_ihj('sativa')

prod_parse_ihj('hybrid')
prod_parse_ihj('indica')


prod_parse_dut('hybrid')
prod_parse_dut('indica')
prod_parse_dut('sativa')'''
driver.quit()
html_write()


