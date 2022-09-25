from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
import time
import asyncio
import logging
import structlog
import csv

start_time = time.time()

with open('prod_csv_sun.text', 'w') as f:
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
    store_name = 'SUN'
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-logging", "--silent"]}}

    async with sema, get_session(service, browser) as session:
        try:
            print(f'Trying: {url}')
            store_name = 'SUN'

            await session.get(url)
            await asyncio.sleep(5)

            html = await session.execute_script("return document.body.innerHTML")
            soup = BeautifulSoup(html, "html.parser")

            store_name = soup.find('p', class_="Dropdown__StlStoreName-sc-t2betb-1")
            store_name = store_name.text
            store_name = store_name.replace(', PA', '')
            #print(f'Raw store name: {store_name}')
            store_name = store_name.strip()

            product_buttons = soup.select('button[data-cy="ProductListItem"]')

            print(f'I got {len(product_buttons)} products.')
            for btn in product_buttons:
                soup = btn.prettify()
                #print(f'{soup}\n')

                # strain
                prod_strain = btn.find('span', class_="MuiChip-label")
                prod_strain = prod_strain.text
                #print(f'Product Strain: {prod_strain}')

                # grower
                prod_grower = btn.find('h5', class_="preheader")
                prod_grower = prod_grower.text
                #print(f'Product Grower: {prod_grower}')

                #print(soup)
                prod_name = btn.find('h4', class_="jss192")
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss202")
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss185")
                if prod_name is None:
                    prod_name = btn.find('h4', class_="jss189")

                prod_name = prod_name.text
                #print(f'Raw name : {prod_name}')

                # prod type
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
                if prod_price is None:
                    prod_price = btn.find('span', class_="sc-hmjpVf")

                prod_price = prod_price.text
                prod_price = prod_price.strip('$')
                prod_price = float(prod_price)
                #print(f'Price: {prod_price}')

                # thc%
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
                print(row)

                with open('prod_csv_sun.text', 'a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',')
                    csv_writer.writerow(row)

        except Exception as error:
            print(f'Problem with {url}:\n {error}')
            print(soup.prettify())


async def spawn_task(urls):
    sema = asyncio.BoundedSemaphore(8)
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(prod_parse_sun(url, sema)))
    await asyncio.gather(*tasks)


def main():

    with open('urls_list_menus_sun.text', 'r') as f:
        url_list_sun = f.readlines()
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



