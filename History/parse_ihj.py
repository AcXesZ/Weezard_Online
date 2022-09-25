from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import re
import time


#set bs4 driver
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

def prod_parse_ihj():
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


def csv_write_row(row):
    # Create a csv file
    with open('../prod_csv_all.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(row)


if __name__ == '__main__':
    prod_parse_ihj()


