import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


pa_urls = []
with open('urls_list_menus_dut.text', 'w') as f:
    f.write('')

'''set driver'''
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)


def get_menus_dut():

    driver.get('https://dutchie.com/cities')
    time.sleep(1)
    html = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(html, "html.parser")

    '''print(soup.prettify())'''

    states = soup.find_all("div", class_="cities-by-state__LinksContainer-sc-1eosbd8-1 hNmOIE")

    for state in states:
        if 'Pennsylvania' in state.text:
            '''print(state)'''
            print('found pa')

            pa_cities = state.find_all("a", class_= "link__StyledLink-hbyqoc-0 ktDwDx cities-by-state__CityPageLink-sc-1eosbd8-3 bQlMMm css-vurnku", href=True)

            city_links = []
            for city in pa_cities:
                city_url = f'http://www.dutchie.com/{city["href"]}'
                #print(f'city_url: {city_url}\n')

                driver.get(city_url)
                time.sleep(0.5)
                html = driver.execute_script("return document.body.innerHTML")
                soup = BeautifulSoup(html, "html.parser")

                location_links = soup.find_all('a', class_="dispensary-card__Container-sc-1wd9p5b-0 jpwVve", href=True)
                for link in location_links:
                    print(link["href"])
                    if '-nj-' not in link["href"]:

                        with open('urls_list_menus_dut.text', 'a') as f:
                            url = f'http://www.dutchie.com{link["href"]}'
                            print(f'Writing: {url}\n')
                            f.write(url+"/products/flower?straintypes=hybrid\n")
                            f.write(url + "/products/flower?straintypes=indica\n")
                            f.write(url + "/products/flower?straintypes=sativa\n")


if __name__ == '__main__':
    get_menus_dut()


