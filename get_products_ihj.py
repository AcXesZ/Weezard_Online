from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
import re
import time
import asyncio
import logging
import structlog
import traceback
import csv

with open('errors.html', 'w') as f:
    f.write(f'')

with open('prod_csv_ihj.text', 'w') as f:
    f.write(f'')

def set_arsenic_log_level(level=logging.ERROR):
    # Create logger
    logger = logging.getLogger('arsenic')

    # We need factory, to return application-wide logger
    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)


set_arsenic_log_level()


async def prod_parse_ihj(url, sema):
    store_name = 'IHJ'
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-logging", "--silent"]}}

    # class names
    cn_link = "css-6tz98n"
    cn_href = "css-1fbb79j"
    cn_grower = "css-1ad3qm0"
    cn_type_container = "css-m6dbny"
    cn_type = "css-1ad3qm0"
    cn_price = "css-hihqzq"
    cn_thc_container = "css-g89h0y"
    cn_thc = "css-1ad3qm0"
    cn_weight = "css-lh59bd"

    async with sema, get_session(service, browser) as session:
        #print(f'Trying: {url}')
        await session.get(url)
        await asyncio.sleep(3)

        html = await session.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(html, "html.parser")
        #print(f'{soup.prettify()}')

        # get all the product divs
        product_divs = soup.find_all("div", class_="css-1alyybx")

        for data in soup(['svg', 'path', ' style', 'script', 'img', 'button']):
            # Remove tags
            data.decompose()

        '''write the soup to a file
        with open(f'./soups/soup_ihj_{filter}.html', 'w', encoding="utf-8") as f:
            f.write(soup.prettify())'''

        # parse the product divs
        for product_div in product_divs:
            try:

                # get link
                prod_link_tag = product_div.find("span", class_=cn_link).find("a", href=True)
                prod_href = prod_link_tag['href']
                #print(f'HREF: {prod_href}')

                # get name
                prod_name = product_div.find("div", class_=cn_href).text
                prod_name = prod_name.strip('|')
                #print(f"Name: {prod_name}")
                prod_name = f'<a href="http://www.iheartjane.com{prod_href}">{prod_name}</a><br><a href="https://www.leafly.com/search?q={prod_name}">Leafly</a>'

                # get species indica/sativa/hybrid
                prod_strain = filter

                # get grower
                prod_grower = product_div.find("div", class_=cn_grower).text
                #print(f"Grower: {prod_grower}")

                # get type flower/fine grind/cache/etc...
                prod_type = product_div.find("div", class_=cn_type_container).find("div", class_=cn_type).text
                #print(f"Type: {prod_type}")

                # get price
                prod_price = float(product_div.find("p", class_=cn_price).text[1:6])
                #print(f"Price : {prod_price:.2f}")

                # get thc%
                prod_thc = product_div.find("div", class_=cn_thc_container).find("div", class_=cn_thc).text
                print(f"RAW %THC : {prod_thc}")
                if 'THCa' in prod_thc:
                    print('Found THCa')
                    prod_thc = prod_thc.split('THCa')
                    prod_thc = prod_thc[1].split('%')
                    prod_thc = float(prod_thc[0])
                elif 'THC' in prod_thc:
                    print('Found THC')
                    prod_thc = prod_thc.split('THC')
                    prod_thc = prod_thc[1].split('%')
                    prod_thc = float(prod_thc[0])
                else:
                    print('did not find thca')
                    print(prod_thc)
                    non_decimal = re.compile(r'[^\d.]+')
                    prod_thc = float(non_decimal.sub('', prod_thc))


                print(f"%THC : {prod_thc}")

                # get weight
                prod_weight = product_div.find("p", class_=cn_weight).text
                if prod_weight == '':
                    prod_weight = 0.00
                # remove non-decimals
                non_decimal = re.compile(r'[^\d.]+')
                prod_weight = float(non_decimal.sub('', prod_weight))
                # special case: if weight is something like 1g/3.5g the expression will return 13.5
                if prod_weight == 13.5:
                    prod_weight = 3.5
                #print(f"Weight : {prod_weight}")

                # calculate total mg of thc in weight
                prod_mg_thc = ((prod_thc / 100) * (prod_weight * 1000))
                #print(f"Total mG THC : {prod_mg_thc:.2f}")

                # calculate cents per milligram of thc
                prod_price_per_mg = (prod_price / prod_mg_thc)
                #print(f"Price per mg : {prod_price_per_mg:.3f}")
                #print('\n')

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

                print(row)
                with open('prod_csv_ihj.text', 'a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',')
                    csv_writer.writerow(row)

            except Exception as error:
                '''print(f"{error}")
                print(product_div.text)
                print(prod_name)'''
                with open('errors.html', 'a') as f:
                    f.write(f'Error: {traceback.format_exc()}\n DIV: {product_div.text}\nLink: {prod_name}\n\n')
                await asyncio.sleep(0.25)


async def spawn_task(urls):
    sema = asyncio.BoundedSemaphore(7) # was 7
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(prod_parse_ihj(url, sema)))
    await asyncio.gather(*tasks)


def main():
    with open('urls_list_menus_ihj.text', 'r') as f:
        url_list_ihj = f.readlines()
        url_list_ihj = [line.rstrip() for line in url_list_ihj]
        url_list_ihj = list(set(url_list_ihj))
        print(f'I Heart Jane has {len(url_list_ihj)} entries.')

    print('running tasks')
    time.sleep(1)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(spawn_task(url_list_ihj))



if __name__ == '__main__':
    main()



