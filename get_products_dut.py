from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
import re
import time
import asyncio
import logging
import structlog
import csv


with open('prod_csv_dut.text', 'w') as f:
    f.write('')

with open('prod_errors_dut.text', 'w') as f:
    f.write('')


def set_arsenic_log_level(level=logging.ERROR):
    # Create logger
    logger = logging.getLogger('arsenic')

    # We need factory, to return application-wide logger
    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)


set_arsenic_log_level()


async def prod_parse_dut(url, sema):
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--disable-logging", "--silent"]}}

    async with sema, get_session(service, browser) as session:
        await session.get(url)
        await asyncio.sleep(0.01)
        total_height = int(await session.execute_script("return document.body.scrollHeight"))
        for i in range(1, total_height, 5):
            await session.execute_script("window.scrollTo(0, {});".format(i))
        await asyncio.sleep(0.5)
        html = await session.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(html, "html.parser")

        '''get all the product divs'''
        product_divs = soup.find_all("div", class_=re.compile("^desktop-product-list-item__Container"))
        print(len(product_divs))
        for data in soup(['svg', 'path', ' style', 'script']):
            # Remove tags
            data.decompose()

        '''parse the product divs'''
        for product_div in product_divs:
            '''get product link'''
            try:
                prod_href = None
                prod_link_tag = product_div.find("a", href=True)
                href = prod_link_tag['href']
                prod_href = f'href="http://www.dutchie.com{href}"'
                print(f'HREF: {prod_href}')
            except Exception as error:
                await write_error('product_div', url, error)
            finally:
                if prod_href is None:
                    await write_error('product_div', url, 'NONE TYPE')
                    return

            print(f'\n\n{url}')

            '''get store location'''
            try:
                store_location = None
                store_location = prod_href.split('/')
                store_location = store_location[4]
                store_location = store_location.replace('-', ' ')
                store_location = store_location.title()
                store_location = store_location.replace('O', 'o')
                print(f'Store Location: {store_location}')
            except Exception as error:
                await write_error(f'store_location\n{prod_href}', url, error)
            finally:
                if store_location is None:
                    await write_error('store_location', url, 'NONE TYPE')
                    return

            '''get store zip'''
            try:
                store_zip = None
                with open('zipcodes.csv', 'r') as f_zips:
                    zips = csv.reader(f_zips, delimiter=',')
                    word_list = store_location.split(' ')

                    for zip_line in zips:
                        if store_zip is None:
                            town = zip_line[1]
                            for word in word_list:
                                word = word.upper()
                                if 'OF' not in word:
                                    if word.upper() in town:
                                        store_zip = zip_line[0]
                                        print(f'Store Zip: {store_zip}')
            except Exception as error:
                await write_error(f'store_zip\n{store_zip}', url, error)
            finally:
                if store_zip is None:
                    await write_error('store_zip', url, 'NONE TYPE')
                    return

            '''get type flower/fine grind/cache/etc...'''
            try:
                prod_type = None
                prod_type = product_div.find("div", class_=re.compile("^desktop-product-list-item__ProductName")).text
                if 'Small Flower' in prod_type:
                    prod_type = 'Small Flower'

                if 'Ground Flower' in prod_type:
                    prod_type = 'Ground Flower'

                if 'Small Flower' not in prod_type and 'Ground Flower' not in prod_type:
                    prod_type = 'Flower'

                print(f"Type: {prod_type}")
            except Exception as error:
                await write_error('product_type', url, error)
            finally:
                if prod_type is None:
                    await write_error('product_type', url, 'NONE TYPE')
                    return

            '''get product name'''
            try:
                prod_name = None
                prod_name = product_div.find("div", class_=re.compile("^desktop-product-list-item__ProductName")).text
                chars_to_strip = ['AYR - ', 'AK - ', 'FX - ', 'GTI - ', 'GR - ', 'R - ', 'AY - ',
                                  'R - ', 'MI - ', 'PW - ', 'PC - ', 'KT - ',
                                  '[H]', '[I]', '[SDH]', '[IDH]', '[S]', 'Flower']
                for chars in chars_to_strip:
                    prod_name = prod_name.replace(chars, '')

                prod_name = f'<a {prod_href}>{prod_name}</a><br>' \
                            f'<a href=\"https://www.leafly.com/search?q={prod_name}\">Leafly</a>'

                print(f"Name: {prod_name}")
            except Exception as error:
                await write_error('product_name', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_name', url, 'NONE TYPE')
                    return

            '''get species indica/sativa/hybrid'''
            try:
                prod_strain = url.split('=')
                prod_strain = prod_strain[1]
                prod_strain = prod_strain.capitalize()
                print(f'Strain: {prod_strain}')
            except Exception as error:
                await write_error(f'product_strain', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_strain', url, 'NONE TYPE')
                    return

            '''get grower'''
            try:
                prod_grower = None
                prod_grower = product_div.find("span",
                                               class_=re.compile("^desktop-product-list-item__ProductBrand")).text
                print(f"Grower: {prod_grower}")
            except Exception as error:
                await write_error('product_grower', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_grower', url, 'NONE TYPE')
                    return

            '''get price'''
            try:
                prod_price = None
                prod_price = float(product_div.find("span", class_=re.compile("^weight-tile__PriceText")).text[1:6])
                print(f"Price : {prod_price:.2f}")
            except Exception as error:
                await write_error('product_price', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_price', url, 'NONE TYPE')
                    return

            '''get thc%'''
            try:
                prod_thc = None
                prod_thc = product_div.find("div", class_=re.compile("^desktop-product-list-item__PotencyInfo")).text
                prod_thc_raw = prod_thc
                if prod_thc.count('%') > 1:
                    prod_thc = prod_thc.split('%')
                    prod_thc = prod_thc[0]

                if prod_thc == '':
                    prod_thc = 0.00

                # remove non-decimals
                non_decimal = re.compile(r'[^\d.]+')
                prod_thc = float(non_decimal.sub('', prod_thc))
                print(f"%THC : {prod_thc}")
            except Exception as error:
                await write_error(f'product_thc\n{prod_thc_raw}\n{prod_name}', url, error)
            finally:
                if prod_name is None:
                    await write_error(f'product_thc', url, 'NONE TYPE')
                    return

            '''get weight'''
            try:
                prod_weight = None
                prod_weight = product_div.find("span", class_=re.compile("^weight-tile__Label")).text
                prod_weight_raw = prod_weight
                if prod_weight == '':
                    prod_weight = '0'

                if '1/8' in prod_weight or '3.5g':
                    prod_weight = '3.5'

                if '1/4' in prod_weight:
                    prod_weight = '7.0'

                if '1g' in prod_weight:
                    prod_weight = '1.0'

                prod_weight = float(prod_weight)
                print(f"Weight : {prod_weight}")
            except Exception as error:
                await write_error(f'product_weight: {prod_weight_raw}\n{prod_name}', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_weight', url, 'NONE TYPE')
                    return

            '''calculate total mg of thc in weight'''
            try:
                prod_mg_thc = None
                prod_mg_thc = ((prod_thc/100) * (prod_weight * 1000))
                print(f"Total mG THC : {prod_mg_thc:.2f}")
            except Exception as error:
                await write_error(f'product_total_mg\n{prod_name}', url, error)
            finally:
                if prod_name is None:
                    await write_error('product_total_mg', url, 'NONE TYPE')
                    return

            '''calculate cents per milligram of thc'''
            try:
                prod_price_per_mg = None
                prod_price_per_mg = (prod_price / prod_mg_thc)
                print(f"Price per mg : {prod_price_per_mg:.3f}")
            except Exception as error:
                await write_error(f'product_total_cost_per_mg\n{prod_name}', url, error)
            finally:
                if prod_price_per_mg is None:
                    await write_error('product_total_cost_per_mg', url, 'NONE TYPE')
                    return
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
            except Exception as error:
                await write_error('row', url, error)
                return

            with open('prod_csv_dut.text', 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_NONE, quotechar='', escapechar='\\')
                csv_writer.writerow(row)


async def spawn_task(urls):
    sema = asyncio.BoundedSemaphore(2)
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(prod_parse_dut(url, sema)))
    await asyncio.gather(*tasks)


async def write_error(problem, url, error):
    with open('prod_errors_dut.text', 'a') as f_error:
        f_error.write(f'{url}\n{problem}\n{error}\n\n')


def main():
    with open('urls_list_menus_dut.text', 'r') as f_menus:
        url_list_dut = f_menus.readlines()
        url_list_dut = [line.rstrip() for line in url_list_dut]
        url_list_dut = list(set(url_list_dut))
        print(f'Dutchie has {len(url_list_dut)} entries.')

    print('running tasks')
    time.sleep(1)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(spawn_task(url_list_dut))


if __name__ == '__main__':
    main()
