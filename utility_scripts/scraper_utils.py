"""
Pro-Football-Reference Web Scraper
----------------------------------

This module provides tools to scrape player metadata and game logs from
Pro-Football-Reference (https://www.pro-football-reference.com).

Features:
- Fetch raw HTML pages using Selenium (with optimized Firefox options).
- Collect player profile links by alphabetical index.
- Extract player metadata (name, position, college).
- Retrieve and clean game logs for QBs, RBs, WRs, and TEs.
- Safely concatenate DataFrames while handling missing columns.

Functions:
    get_html_w_selenium(url): Fetch raw HTML from a URL using Selenium.
    get_player_hrefs(letters): Collect player hrefs by first-letter index.
    get_player_metadata(soup): Extract player metadata from profile page.
    safe_concat(df, new_df): Safely concatenate two DataFrames with missing cols.
    grab_gamelogs(href_list): Scrape and process gamelogs for multiple players.

Constants:
    POS_LIST (list): Supported positions for scraping gamelogs (QB, RB, WR, TE).
    DATE_CUTOFF (date): Earliest date for pulling gamelogs
"""

POS_LIST = ['QB', 'RB', 'WR', 'TE']

import pandas as pd
DATE_CUTOFF = pd.to_datetime("1966-06-01", format="%Y-%m-%d")

# import numpy as np
import bs4
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import json


#### Pro Football Reference scraping utility functions


def get_html_w_selenium(url):
    """
    Fetch the raw HTML of a given URL using Selenium with Firefox.

    - Uses Firefox with headless mode and disabled images, CSS, and Flash for faster loading.
    - Opens the given URL, waits briefly, retrieves page source, then closes the browser.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        str: Raw HTML content of the webpage.
    """

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
    """
    Scrape player profile links from Pro-Football-Reference based on first-letter directories.

    - Iterates over a list of starting letters.
    - Collects player hrefs from the site and strips `.htm` endings.

    Args:
        letters (list[str]): List of single-character strings (A-Z) representing player directories.

    Returns:
        list[str]: A list of player profile hrefs without `.htm` suffix.
    """
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
        """
        Extract player metadata from a BeautifulSoup-parsed profile page.

        - Finds player name, position, and college.
        - Raises descriptive errors if name or position cannot be found.
        - College may be missing, in which case it's returned as None.

        Args:
            soup (bs4.BeautifulSoup): Parsed HTML of a player profile page.

        Returns:
            dict: Dictionary containing:
                - 'player_name' (str): Player's name.
                - 'player_position' (str): Player's position (QB, RB, WR, etc.).
                - 'player_college' (str|None): Player's college, or None if unavailable.
        """

        soup_p = soup.find("div", {"id": "meta"})

        try:
            player_name = soup_p.find("h1").text.strip()
        except:
            player_name = None

        try:
            player_position = soup_p.find("strong", string="Position").next_sibling.strip(": ").strip()
        except:
            player_position = None

        try:
            player_college = soup_p.find("strong", string="College").find_next("a").text.strip()
        except:
            player_college = None

        return {'player_name': player_name, 'player_position': player_position, 'player_college': player_college}


def safe_concat(df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """
    Safely concatenate two DataFrames.

    - Ensures missing values are filled with None instead of NaN.
    - Adds new columns if they exist in `new_df` but not in `df`.

    Args:
        df (pd.DataFrame): Base DataFrame.
        new_df (pd.DataFrame): DataFrame to append.

    Returns:
        pd.DataFrame: Combined DataFrame with consistent None-filled columns.
    """
    if df.shape[0] > 0:
        df = pd.concat([df, new_df], ignore_index=True)
    else:
        df = new_df
    return df.where(pd.notnull(df), None)



def pull_gamelogs(href_list):
    """
    Scrape game logs for players from Pro-Football-Reference.

    - Loads column names for each position (QB, RB, WR, TE) from a JSON file.
    - Iterates over player hrefs, scrapes metadata, and retrieves gamelog tables.
    - Cleans column names (handles multi-index, symbols, unnamed headers).
    - Adds metadata fields (player name, position, college).
    - Appends data into position-specific DataFrames.

    Args:
        href_list (list[str]): List of player hrefs (paths on pro-football-reference.com).

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            (qb_df, rb_df, wr_df, te_df) — DataFrames containing gamelogs for each position.
    """
    with open('utility_scripts/gamelog_col_names.json', 'r') as file:
        col_names = json.load(file)
        qb_cols = col_names['QB_columns']
        rb_cols = col_names['RB_columns']
        wr_cols = col_names['WR_columns']
        te_cols = col_names['TE_columns']

    qb_pdf = pd.DataFrame(columns=qb_cols)
    rb_pdf = pd.DataFrame(columns=rb_cols)
    wr_pdf = pd.DataFrame(columns=wr_cols)
    te_pdf = pd.DataFrame(columns=te_cols)
    

    COUNTER=0
    for href in href_list:
        COUNTER+=1
        if COUNTER % 50 == 0:
            print(f"Iteration: {COUNTER}")

        url_s = 'https://www.pro-football-reference.com' + href + '/gamelog/'

        html_raw = get_html_w_selenium(url_s)
        soup = bs4.BeautifulSoup(html_raw, 'html.parser')

        meta_info = get_player_metadata(soup)
        
        if meta_info["player_position"] not in POS_LIST:
            continue
        else:
            df = pd.read_html(url_s)[0]
            df = pd.DataFrame(df)

            #######Fix double-lined column names
            cols = df.columns
            col_names = []
            for i in range(len(cols)):
                ##fix col formatting
                col_1 = re.sub(r"[ ./]", "_", str(cols[i][0]))
                col_1 = re.sub(r"[%]", "_per", col_1)

                col_2 = re.sub(r"[ ./]", "_", str(cols[i][1]))
                col_2 = re.sub(r"[%]", "_per", col_2)
                if col_1.startswith('Unnamed') :
                    ## label home/away col with name
                    if col_2.startswith('Unnamed') :
                        col_names.append('AT')
                    else :
                        col_names.append(col_2)
                else :
                    col_names.append( col_1 + '_' + col_2)

            

            df = df.set_axis(col_names, axis=1)

            df = df[df["Rk"] != "Rk"]
            df = df[~(pd.isna(df["Rk"]))]

            df["Date"] = pd.to_datetime(df["Date"])
            df = df[df["Date"] >= DATE_CUTOFF]

            df["AT"] = df["AT"].apply(lambda x: 1 if x == "@" else 0)
            df["GS"] = df["GS"].apply(lambda x: 1 if x == "*" else 0)

            df["Player_Name"] = meta_info["player_name"]
            # print(meta_info["player_name"])
            df["Player_Position"] = meta_info["player_position"]
            df["Player_College"] = meta_info["player_college"]
            # print(df)

            if COUNTER % 50 == 0:
                print(f"Player: {meta_info["player_name"]}")

            if (meta_info["player_position"] == 'QB') & (df.shape[0] > 0):
                qb_pdf = safe_concat(qb_pdf, df)
                
            elif (meta_info["player_position"] == 'RB') & (df.shape[0] > 0):
                rb_pdf = safe_concat(rb_pdf, df)

            elif (meta_info["player_position"] == 'WR') & (df.shape[0] > 0):
                wr_pdf = safe_concat(wr_pdf, df)

            elif (meta_info["player_position"] == 'TE')  & (df.shape[0] > 0):
                te_pdf = safe_concat(te_pdf, df)
            else: 
                print("nothing appended...")
                continue


    return qb_pdf, rb_pdf, wr_pdf, te_pdf

# def find_active_hrefs()