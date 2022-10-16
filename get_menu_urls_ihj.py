import asyncio
import time
import logging

from arsenic import get_session, browsers, services

import structlog
start_time = time.time()


menu_list_ihj = []

with open('urls_list_menus_ihj.text', 'w') as f:
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


async def scraper(url, sema):
    print(f'Adding...{url}')
    service = services.Chromedriver()
    browser = browsers.Chrome()
    browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-logging", "--silent"]}}

    async with sema, get_session(service, browser) as session:
        print(f'Trying...{url}')
        await session.get(url)
        await asyncio.sleep(0.01)
        print(f'Got RAW from...{url}')
        html = await session.execute_script("return document.body.innerHTML")
        # print(html)
        print(f'Got inner HTML for...{url}')
        await find_pa(url, html)


async def find_pa(url, html):
    print(f'Checking...{url}')
    if 'Pennsylvania' in html:
        print("GOT ONE")
        menu_list_ihj.append(url)
        with open('urls_list_menus_ihj.text', 'a') as f:
            for url in menu_list_ihj:
                f.writelines(f'{url}?refinementList%5Broot_types%5D%5B0%5D='
                             f'flower&refinementList%5Bcategory%5D%5B0%5D=hybrid\n')
                f.writelines(f'{url}?refinementList%5Broot_types%5D%5B0%5D='
                             f'flower&refinementList%5Bcategory%5D%5B0%5D=indica\n')
                f.writelines(f'{url}?refinementList%5Broot_types%5D%5B0%5D='
                             f'flower&refinementList%5Bcategory%5D%5B0%5D=sativa\n')


async def spawn_task(urls,):
    sema = asyncio.BoundedSemaphore(6)
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(scraper(url, sema)))
    await asyncio.gather(*tasks)


def main():

    urls = []
    for store_number in range(6900, 9999):
        url = f'https://www.iheartjane.com/embed/stores/{store_number}/menu'
        urls.append(url)

    print('running tasks')
    time.sleep(1)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(spawn_task(urls))
    print(menu_list_ihj)


if __name__ == '__main__':
    main()
    print(f'Execution time in seconds: {start_time - time.time()}')
