
import pandas as pd
import numpy as np
import bs4
import enum
import requests
import string
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

##selenium options
options = Options()
options.add_argument("--headless")



#######Pull all Player Page Links into player_links[]
# Create list of captial letters to loop over
# letters = list(string.ascii_uppercase)
letters = ['A', 'C']

def get_player_hrefs(scrape_url):
    driver = webdriver.Firefox(options=options)
    driver.get(scrape_url)
    time.sleep(1)
    html_raw = driver.page_source
    driver.close()

    soup = bs4.BeautifulSoup(html_raw, 'html.parser')
    soup_p = soup.find("div", {"id": "div_players"})

    player_links = []
    for a in soup_p.findAll('a', href=True):
        s = a['href']
        # player_links.append(s[11:])
        player_links.append(s)

    return player_links

all_player_links=[]
for alpha in letters:
    url_s = 'https://www.pro-football-reference.com/players/' + alpha + '/'

    all_player_links.append(get_player_hrefs(url_s))

print(all_player_links)


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