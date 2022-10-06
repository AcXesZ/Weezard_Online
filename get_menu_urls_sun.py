import time
start_time = time.time()

with open('urls_list_menus_sun.text', 'a') as f:
    f.write('')


def get_menus_sun():
    base_urls = [
                'https://www.sunnyside.shop/menu/ambler-pa/products/flower',
                'https://www.sunnyside.shop/menu/butler-pa/products/flower',
                'https://www.sunnyside.shop/menu/lancaster-pa/products/flower',
                'https://www.sunnyside.shop/menu/montgomeryville-pa/products/flower',
                'https://www.sunnyside.shop/menu/new-kensington-pa/products/flower',
                'https://www.sunnyside.shop/menu/philadelphia-city/products/flower',
                'https://www.sunnyside.shop/menu/philadelphia-pa/products/flower',
                'https://www.sunnyside.shop/menu/phoenixville-pa/products/flower',
                'https://www.sunnyside.shop/menu/pittsburgh-pa/products/flower'
                ]

    with open('urls_list_menus_sun.text', 'a') as f_urls:
        for url in base_urls:
            f_urls.writelines(
                f'{url}?strain_types=sativa\n'
                f'{url}?strain_types=indica\n'
                f'{url}?strain_types=hybrid\n')


if __name__ == '__main__':
    get_menus_sun()
    print(f'Execution time in seconds: {start_time - time.time()}')
