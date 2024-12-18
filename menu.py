import requests
from bs4 import BeautifulSoup
import re

# Базовый URL
base_url = 'https://hitebbq.com/'

# Парсим меню и извлекаем ссылки на каждую страницу раздела
menu_url = 'https://hitebbq.com/menu/'
response = requests.get(menu_url)
soup = BeautifulSoup(response.content, 'html.parser')
lis = soup.select("nav.aside-nav > ul > li")
menu_links = []
for li in lis:
    a = li.find("a")
    if a:
        menu_links.append(a.get('href'))

menu_links = menu_links[:10]

# Парсим список страниц меню
pages = []
for link in menu_links:
    response = requests.get(base_url + link)
    soup = BeautifulSoup(response.content, 'html.parser')
    page_nav = soup.find('ul', class_="page-pagination")
    if not page_nav:
        pages.append(base_url + link + '?PAGEN_1=1')
    else:
        lis =  page_nav.find_all('li')
        for i in range(1, len(lis) + 1):
            pages.append(base_url + link + '?PAGEN_1=' + str(i))

# Получаем список страниц блюд
dishes_pages = []
for page in pages:
    response = requests.get(page)
    soup = BeautifulSoup(response.content, 'html.parser')
    cards = soup.select('div.grid--item.-span-1-2.-sm-span-1-2.-lg-span-1-3>div.item-tile>a[href]')
    links = [card['href'] for card in cards]
    dishes_pages.extend(links)

# Создаем файл для хранения информации о блюдах
with open('dishes.txt', 'w', encoding='utf-8') as f:
    # Переходим по каждой карточке блюда
    for dish_page in dishes_pages:
        response = requests.get(base_url + dish_page)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(base_url + dish_page)

        name = soup.find('p', itemprop='name').text.strip()
        description = soup.find('p', itemprop='description').text.strip()

        table = soup.find('table', class_='item-card--meta')
        if  table:
            tbody =  table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                nutrients = {}
                if rows:
                    for row in rows:
                        cells = row.find_all('td', attrs={'colspan': None})
                        if cells:
                            nutrient = cells[0].text.strip()
                            value_portion = cells[2].text.strip() if len(cells) >= 3  else '-'
                            nutrients[nutrient] = value_portion
                    
                    # Извлекаем общий вес продукта/порции
                    weight_td = soup.find('td', colspan='3')
                    if weight_td:
                        weight = weight_td.text.strip()[4:]
        else:
            weight_div = soup.find('div', class_='item-card--body')
            if weight_div:
                weight_text = weight_div.get_text()
                weight_match = re.search(r'Вес (\d+) гр', weight_text)
                if weight_match:
                    weight = weight_match.group(1)[4:]
            
        # Создаем строку с информацией о блюде
        dish_info = f"{name}\n"
        dish_info += f"{description}\n"
        if nutrients:
            dish_info += "Пищевая ценность:\n"
            for nutrient, values in nutrients.items():
                dish_info += f"  {nutrient}: {nutrients[nutrient]} на порцию\n"
        if weight:
            dish_info += f"Вес: {weight}\n\n"
            
        # Записываем информацию о блюде в файл
        f.write(dish_info)
