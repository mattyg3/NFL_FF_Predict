
import pandas as pd
import numpy as np
import bs4
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


import requests


#### Pro Football Reference scraping utility functions

# def html_JS_scrape(url):
#     from requests_html import HTMLSession
#     session = HTMLSession()
#     r = session.get(url)

#     # Render JavaScript (uses pyppeteer under the hood)
#     r.html.render(timeout=20)

#     # Extract text or links
#     print(r.html.find("title", first=True).text)



# def playwright_scrape(url):
#     from playwright.sync_api import sync_playwright

#     with sync_playwright() as p:
#         browser = p.firefox.launch(headless=True)
#         page = browser.new_page()
#         page.goto(url, wait_until="networkidle", timeout=0)
#         print("Title:", page.title())
        
#         # # Extract content
#         # content = page.content()
#         # print(content)
        
#         browser.close()

# def request_func(url):
#     headers = {"User-Agent": "Mozilla/5.0"}  
#     response = requests.get(url, headers=headers)
#     # soup = bs4.BeautifulSoup(response.text, "lxml")
#     soup = bs4.BeautifulSoup(response.text, 'html.parser')
#     print(soup)

def get_html_w_selenium(url):

    #selenium options
    options = Options()
    ##Disable images, CSS, and other unnecessary content
    options.set_preference("permissions.default.image", 2)   # Block images
    options.set_preference("permissions.default.stylesheet", 2)  # Block CSS
    options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")  # Disable Flash

    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    #Selenium to open, grab html, then close
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    time.sleep(1)
    html_raw = driver.page_source
    driver.close()
    
    return html_raw


def get_player_hrefs(letters):
    all_player_links=[]

    for alpha in letters:
        url_s =  'https://www.pro-football-reference.com/players/' + alpha + '/'

        html_raw = get_html_w_selenium(url_s)

        ##Parse html with bs4, grab player hrefs
        soup = bs4.BeautifulSoup(html_raw, 'html.parser')
        soup_p = soup.find("div", {"id": "div_players"})
        for a in soup_p.findAll('a', href=True):
            s = a['href']
            # all_player_links.append(s[:-4])
            all_player_links.append(re.sub('.htm', '', s))
    return all_player_links



def get_player_metadata(soup):
        soup_p = soup.find("div", {"id": "meta"})

        try:
            player_name = soup_p.find("h1").text.strip()
        except NameError as e:
            print("Caught an error:", e)
            raise ValueError("No player name found (bs4)")  from e

        try:
            player_position = soup_p.find("strong", string="Position").next_sibling.strip(": ").strip()
        except NameError as e:
            print("Caught an error:", e)
            raise ValueError("No player position found (bs4)")  from e

        try:
            player_college = soup_p.find("strong", string="College").find_next("a").text.strip()
        except:
            None

        return {'player_name': player_name, 'player_position': player_position, 'player_college': player_college}


def grab_gamelogs(href_list):
    for href in href_list:
        url_s = 'https://www.pro-football-reference.com' + href + '/gamelog/'

        html_raw = get_html_w_selenium(url_s)
        soup = bs4.BeautifulSoup(html_raw, 'html.parser')

        meta_info = get_player_metadata(soup)
        











#########OLD


#######Pull all Player Page Links into player_links[]
#Create list of captial letters to loop over
# letters = list(string.ascii_uppercase)
# letters = ['A']
#Initialize list to store links to indv player pages
# check1 = []
#Loop over 'letter' to collect links for all players

# url_s = 'https://www.pro-football-reference.com/players/' + 'A' + '/'
# # res = requests.get(url_s)
# # print(res._content)

# driver = webdriver.Firefox(options=options)
# driver.get(url_s)
# time.sleep(1)
# html_raw = driver.page_source
# # driver.save_full_page_screenshot('dev_screenshots/bs4_testing.png')
# driver.close()

# soup = bs4.BeautifulSoup(html_raw, 'html.parser')
# # print(soup)

# soup_p = soup.find("div", {"id": "div_players"})
    
# # print(soup_p)

# player_links = []
# for a in soup_p.findAll('a', href=True) :
#     s = a['href']
#     # print(s)
#     # player_links.append(s[11:])
#     player_links.append(s)

# print(player_links[0])
    


# print(res.content)
# soup = bs4.BeautifulSoup(res.content, 'html.parser')
# print('PARSED...')

# print(soup)
# # for i in letters:
#     url_s = 'https://www.pro-football-reference.com/players/' + i + '/'

#     res = requests.get(url_s)
#     soup = bs4.BeautifulSoup(res.content, 'html.parser')
#     print(soup)
#     # #find only players links
    # soup_p = soup.find("div", {"id": "div_players"})
    
    # print(soup_p)

#     player_links = []
#     for a in soup_p.findAll('a', href=True) :
#         s = a['href']
#         print(s)
#         player_links.append(s[11:])
    
#     ##########Go into each player page, pull metadata and player gamelogs
#     # url = 'https://www.pro-football-reference.com/players/A/AaitIs00/gamelog/'
    
#     for player in range(len(player_links)) :
#         href = str(player_links[player])
#         url = 'https://www.pro-football-reference.com/players/' + i + '/' + href + '/gamelog/'
#         #######Get player meta data
#         res = requests.get(url)
#         soup = bs4.BeautifulSoup(res.content, 'html.parser')
#         soup_p = soup.find("div", {"id": "meta"})
#         elem = soup_p.select('span')[0]
#         elem = str(elem)
#         s_name = elem[6:-7] #removes "span" key words

#         elem = str(soup_p.findAll('p')[1])
#         elem = elem.split(' ')

#         if len(elem) == 1 : #incase there is no space
#             elem = str(elem)
#         else : 
#             elem = str(elem[1])

#         elem = elem[:-4] #remove unneed html syntax
#         s_position = elem.strip()

#         df_name = s_name + "_" + s_position #combine name and position meta data as dataframe ID
#         check1.append(df_name)

#     print('\nFinished page ' + i)
            

# # print(player_links)
# # print(len(player_links))

# print(check1)






# #######Pull career game-logs for all player_links[], correct col names
# df = pd.read_html(url)[0]
# df = pd.DataFrame(df)

# #######Fix double-lined column names
# cols = df.columns
# col_names = []
# for i in range(len(cols)) :
#     s = str(cols[i][0])
#     s2 = str(cols[i][1])
#     if s.startswith('Unnamed') :
#         if s2.startswith('Unnamed') :
#             col_names.append('AT')
#         else :
#             col_names.append(cols[i][1])
#     else :
#         col_names.append(cols[i][0] + '_' + cols[i][1])

# df.set_axis(col_names, axis=1, inplace=True)

# print(df)