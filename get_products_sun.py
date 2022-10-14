from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
import time
import asyncio
import logging
import structlog
import csv

start_time = time.time()

'''delete all data from error and product files'''
with open('prod_errors_sun.text', 'w') as f:
    f.write('')

with open('prod_sun.csv', 'w') as f:
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


async def prod_parse_sun(url, sema):
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-logging", "--silent"]}}

    async with sema, get_session(service, browser) as session:
        print(f'Trying: {url}')

        await session.get(url)
        await asyncio.sleep(5)

        html = await session.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(html, "html.parser")

        '''get store location'''
        try:
            store_location = None
            store_location = soup.find('p', class_="Dropdown__StlStoreName-sc-t2betb-1")
            store_location = store_location.text
            store_location = store_location.replace(', PA', '')
            # print(f'Raw store name: {store_name}')
            store_location = store_location.strip()
        except Exception as error:
            await write_error('store_name', url, error)
        finally:
            if store_location is None:
                await write_error('store_name', url, 'NONE TYPE')
                return

        '''get store zip'''
        try:
            store_zip = None
            store_zip = 00000
        except Exception as error:
            await write_error('store_zip', url, error)
        finally:
            if store_zip is None:
                await write_error('store_zip', url, 'NONE TYPE')
                return

        product_buttons = soup.select('button[data-cy="ProductListItem"]')

        for btn in product_buttons:
            soup = btn.prettify()
            print(f'{soup}\n')

            # strain
            try:
                prod_strain = None
                prod_strain = btn.find('span', class_="MuiChip-label")
                prod_strain = prod_strain.text
                # print(f'Product Strain: {prod_strain}')
            except Exception as error:
                await write_error('prod_strain', url, error)
            finally:
                if prod_strain is None:
                    await write_error('prod_strain', url, 'NONE TYPE')
                    return

            '''get grower'''
            try:
                prod_grower = None
                prod_grower = btn.find('h5', class_="preheader")
                prod_grower = prod_grower.text
                # print(f'Product Grower: {prod_grower}')
            except Exception as error:
                await write_error('prod_grower', url, error)
            finally:
                if prod_grower is None:
                    await write_error('prod_grower', url, 'NONE TYPE')
                    return

            '''get product name'''
            try:
                prod_name = btn.find('h4', class_="jss192")
                print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss202")
                    print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss185")
                    print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss189")
                    print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss183")
                    print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss190")
                    print(f'Raw name : {prod_name}')
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss200")

                prod_name = prod_name.text
                print(f'Raw name : {prod_name}')
            except Exception as error:
                await write_error('prod_name', url, error)
            finally:
                if prod_name is None:
                    await write_error('prod_name', url, 'NONE TYPE')
                    return

            '''get product type'''
            try:
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
                # print(f'Product type: {prod_type}')

                words_to_remove = ['Flower', 'Lightly', 'Ground', 'Smalls', 'Small', 'Trim', 'Fine']
                for word in words_to_remove:
                    prod_name = prod_name.replace(word, '')


            except Exception as error:
                await write_error('prod_type', url, error)
            finally:
                if prod_type is None:
                    await write_error('prod_type', url, 'NONE TYPE')
                    return

            '''get product weight'''
            try:
                prod_weight = None
                prod_weight = btn.find('span', class_="gray")
                prod_weight = prod_weight.text
                prod_weight = prod_weight.replace('g', '')
                prod_weight = float(prod_weight)
                # print(f'weight: {prod_weight}')
            except Exception as error:
                await write_error('prod_weight', url, error)
            finally:
                if prod_weight is None:
                    await write_error('prod_weight', url, 'NONE TYPE')
                    return

            '''get product price'''
            try:
                prod_price = None
                prod_price = btn.find('span', class_="sc-eLwHnm")
                if prod_price is None:
                    prod_price = btn.find('span', class_="sc-hmjpVf")

                prod_price = prod_price.text
                prod_price = prod_price.strip('$')
                prod_price = float(prod_price)
                # print(f'Price: {prod_price}')
            except Exception as error:
                await write_error('prod_price', url, error)
            finally:
                if prod_price is None:
                    await write_error('prod_price', url, 'NONE TYPE')
                    return

            '''get thc%'''
            try:
                prod_thc = None
                prod_h6s = btn.find_all('h6')

                for h6 in prod_h6s:
                    if prod_thc is None:
                        if '%' in h6.text:
                            prod_thc = h6.text
                            prod_thc = prod_thc.strip('%')
                            prod_thc = float(prod_thc)

                # print(f'THC%: {prod_thc}')
            except Exception as error:
                await write_error('prod_thc', url, error)
            finally:
                if prod_thc is None:
                    await write_error('prod_thc', url, 'NONE TYPE')
                    return

            '''calculate total mg of thc in weight'''
            try:
                prod_mg_thc = None
                prod_mg_thc = ((prod_thc / 100) * (prod_weight * 1000))
                # print(f'Total mG THC : {prod_mg_thc:.2f}')
            except Exception as error:
                await write_error('prod_mg_thc', url, error)
            finally:
                if prod_mg_thc is None:
                    await write_error('prod_mg_thc', url, 'NONE TYPE')
                    return

            '''calculate cents per milligram of thc'''
            try:
                prod_price_per_mg = None
                prod_price_per_mg = (prod_price / prod_mg_thc)
                # print(f"Price per mg : {prod_price_per_mg:.3f}")
            except Exception as error:
                await write_error('prod_price_per_mg', url, error)
            finally:
                if prod_price_per_mg is None:
                    await write_error('prod_price_per_mg', url, 'NONE TYPE')
                    return

            '''write the row'''
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

            with open('prod_sun.csv', 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',')
                csv_writer.writerow(row)


async def spawn_task(urls):
    sema = asyncio.BoundedSemaphore(8)
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(prod_parse_sun(url, sema)))
    await asyncio.gather(*tasks)


async def write_error(problem, url, error):
    with open('prod_errors_sun.text', 'a') as f_error:
        f_error.write(f'{url}\n{problem}\n{error}\n\n')


def main():

    with open('urls_list_menus_sun.text', 'r') as f_urls:
        url_list_sun = f_urls.readlines()
        url_list_sun = [line.rstrip() for line in url_list_sun]
        url_list_sun = list(set(url_list_sun))
        print(f'Sunnyside has {len(url_list_sun)} entries.')

    print('running tasks')
    time.sleep(1)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(spawn_task(url_list_sun))


if __name__ == '__main__':
    main()
    print(f'Execution time in seconds: {start_time - time.time()}')
