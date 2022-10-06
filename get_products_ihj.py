from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
import re
import time
import asyncio
import logging
import structlog
import csv
import json

with open('prod_errors_ihj.text', 'w') as f:
    f.write('')

with open('prod_ihj.csv', 'w') as f:
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
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-logging", "--silent"]}}

    # class names
    cn_prod_div = "css-13v290s"
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
        print(f'Trying: {url}')
        await session.get(url)
        await asyncio.sleep(5)

        html = await session.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(html, "html.parser")
        # print(f'{soup.prettify()}')

        # get all the product divs
        product_divs = soup.find_all("div", class_=cn_prod_div)
        json_script = soup.find("script", attrs={"type": True})

        if json_script is not None:
            json_script = json_script.text
            parsed_json = json.loads(json_script)

        for data in soup(['svg', 'path', ' style', 'script', 'img', 'button']):
            # Remove tags
            data.decompose()

        '''get HREF'''
        for product_div in product_divs:
            try:
                # get link
                prod_link_tag = product_div.find("span", class_=cn_link).find("a", href=True)
                prod_href = prod_link_tag['href']
                print(f'HREF: {prod_href}')
            except Exception as error:
                await write_error('product_div', url, error)
            finally:
                if prod_href is None:
                    await write_error('product_div', url, 'NONE TYPE')
                    return

            '''get location from json (city and zip)'''
            try:
                store_location = None
                store_zip = None
                print(f'trying JSON')
                store_address = parsed_json.get('address')
                store_location = store_address.get('addressLocality')
                store_zip = store_address.get('postalCode')
                print(f'Store Location: {store_location}\nStore Zip: {store_zip}')

            except Exception as error:
                await write_error('product_json_location/zip', url, error)
                print(error)
                time.sleep(5)
            finally:
                if store_location is None or store_zip is None:
                    await write_error('product_json_location/zip', url, 'NONE TYPE')
                    return

            '''get name'''
            try:
                prod_name = None
                prod_name = product_div.find("div", class_=cn_href).text
                prod_name = prod_name.strip('|')
                print(f'Name: {prod_name}')
                prod_name = f'<a href="http://www.iheartjane.com{prod_href}">{prod_name}</a><br>' \
                            f'<a href="https://www.leafly.com/search?q={prod_name}">Leafly</a>'
            except Exception as error:
                await write_error(f'product_name\n{prod_name}', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_name', url, 'NONE TYPE')
                    return

            '''get species indica/sativa/hybrid'''
            try:
                prod_strain = filter
            except Exception as error:
                await write_error(f'prod_strain\n{prod_strain}', url, error)
            finally:
                if prod_strain is None:
                    await write_error('product_strain', url, 'NONE TYPE')
                    return

            '''get grower'''
            try:
                prod_grower = None
                prod_grower = product_div.find("div", class_=cn_grower).text
                '''print(f"Grower: {prod_grower}")'''
            except Exception as error:
                await write_error(f'prod_grower\n{prod_grower}', url, error)
            finally:
                if prod_grower is None:
                    await write_error('product_div', url, 'NONE TYPE')
                    return

                '''get type flower/fine grind/cache/etc...'''
            try:
                prod_type = None
                prod_type = product_div.find("div", class_=cn_type_container).find("div", class_=cn_type).text
                '''print(f"Type: {prod_type}")'''
            except Exception as error:
                await write_error(f'prod_type\n{prod_type}', url, error)
            finally:
                if prod_type is None:
                    await write_error('product_type', url, 'NONE TYPE')
                    return

            '''get price'''
            try:
                prod_price = None
                prod_price = float(product_div.find("p", class_=cn_price).text[1:6])
                '''print(f"Price : {prod_price:.2f}")'''
            except Exception as error:
                await write_error(f'prod_price\n{prod_price}', url, error)
            finally:
                if prod_price is None:
                    await write_error('product_price', url, 'NONE TYPE')
                    return

            '''get thc%'''
            try:
                prod_thc = None
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
                    '''print(f"%THC : {prod_thc}")'''
            except Exception as error:
                await write_error(f'prod_thc\n{prod_thc}', url, error)
            finally:
                if prod_thc is None:
                    await write_error('product_thc', url, 'NONE TYPE')
                    return

            '''get weight'''
            try:
                prod_weight = None
                prod_weight = product_div.find("p", class_=cn_weight).text
                if prod_weight == '':
                    prod_weight = 0.00
                # remove non-decimals
                non_decimal = re.compile(r'[^\d.]+')
                prod_weight = float(non_decimal.sub('', prod_weight))
                # special case: if weight is something like 1g/3.5g the expression will return 13.5
                if prod_weight == 13.5:
                    prod_weight = 3.5
                '''print(f"Weight : {prod_weight}")'''
            except Exception as error:
                await write_error(f'prod_weight\n{prod_weight}', url, error)
            finally:
                if prod_weight is None:
                    await write_error('product_weight', url, 'NONE TYPE')
                    return

            '''calculate total mg of thc in weight'''
            try:
                prod_mg_thc = None
                prod_mg_thc = ((prod_thc / 100) * (prod_weight * 1000))
                '''print(f"Total mG THC : {prod_mg_thc:.2f}")'''
            except Exception as error:
                await write_error(f'prod_mg_thc\n{prod_mg_thc}', url, error)
            finally:
                if prod_mg_thc is None:
                    await write_error('product_mg_thc', url, 'NONE TYPE')
                    return

            '''calculate cents per milligram of thc'''
            try:
                prod_price_per_mg = None
                prod_price_per_mg = (prod_price / prod_mg_thc)
                '''print(f"Price per mg : {prod_price_per_mg:.3f}")'''
            except Exception as error:
                await write_error(f'prod_price_per_mg\n{prod_price_per_mg}', url, error)
            finally:
                if prod_mg_thc is None:
                    await write_error('product_price_per_mg', url, 'NONE TYPE')
                    return

            '''write the row'''
            try:
                row = [f'{store_location}',
                       f'{store_zip}',
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
            except Exception as error:
                await write_error(f'Error writing row:', url, error)
                return

            if row is not None:
                with open('prod_ihj.csv', 'a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',')
                    csv_writer.writerow(row)


async def spawn_task(urls):
    sema = asyncio.BoundedSemaphore(1)  # was 7
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(prod_parse_ihj(url, sema)))
    await asyncio.gather(*tasks)


async def write_error(problem, url, error):
    with open('prod_errors_ihj.text', 'a') as f_error:
        f_error.write(f'{url}\n{problem}\n{error}\n\n')


def main():
    with open('urls_list_menus_ihj.text', 'r') as f_menus:
        url_list_ihj = f_menus.readlines()
        url_list_ihj = [line.rstrip() for line in url_list_ihj]
        url_list_ihj = list(set(url_list_ihj))
        print(f'I Heart Jane has {len(url_list_ihj)} entries.')

    print('running tasks')
    time.sleep(1)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(spawn_task(url_list_ihj))


if __name__ == '__main__':
    main()
