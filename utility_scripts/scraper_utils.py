

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
    YEAR_CUTOFF (int): Year cutoff for player careers for pulling gamelogs
"""

POS_LIST = ['QB', 'RB', 'WR', 'TE']

import pandas as pd
# YEAR_CUTOFF = 1966
YEAR_CUTOFF = 1980

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
    Scrape player profile links and metadata from Pro-Football-Reference.

    For each letter provided, this function loads the corresponding
    player index page on Pro-Football-Reference, extracts player profile
    links (hrefs), names, positions, and active years, then filters results
    based on a predefined set of valid positions (POS_LIST) and a year cutoff (YEAR_CUTOFF).

    Parameters
    ----------
    letters : list[str]
        A list of single-character strings (typically A–Z),
        representing the first letter of player last names.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing one row per player-role combination, with columns:
        - 'href' (str): The player's profile link (without the ".htm" suffix).
        - 'player_name' (str): The player's full name.
        - 'player_position' (str): The player's position abbreviation (split into multiple rows if multi-position).
        - 'start_year' (int): The first year the player was active.
        - 'end_year' (int): The last year the player was active.
    """
    start = time.perf_counter()
    print("Gathering player hrefs...")
    all_player_links=[]
    name_list, roles_list, start_year_list, end_year_list = [],[],[],[]

    for alpha in letters:
        url_s =  'https://www.pro-football-reference.com/players/' + alpha + '/'

        html_raw = get_html_w_selenium(url_s)

        ##Parse html with bs4, grab player hrefs
        soup = bs4.BeautifulSoup(html_raw, 'html.parser')
        soup_p = soup.find("div", {"id": "div_players"})
        for a in soup_p.findAll('a', href=True):
            s = a['href']
            full_text = a.parent.get_text(" ", strip=True)
            # Example: "Kelly Saalfeld (C) 1980-1980"
            
            # Regex: captures name, positions (optional), and years
            match = re.search(r"^(.*?)\s*\((.*?)\)\s*(\d{4})-(\d{4})$", full_text)
            if not match:
                # Handle players with empty positions: "Lenny Sachs () 1920-1926"
                match = re.search(r"^(.*?)\s*\(\)\s*(\d{4})-(\d{4})$", full_text)
                if match:
                    name = match.group(1).strip()
                    roles = [None]
                    start_year, end_year = match.group(2), match.group(3)
                else:
                    continue
            else:
                name = match.group(1).strip()
                roles = match.group(2).split("-")  #.strip()
                start_year, end_year = match.group(3), match.group(4)
            
            #Check if there is any overlap between player position lists and POS_LIST
            if bool(set(roles) & set(POS_LIST)):
                for k in roles: #possible for WR & RB
                    all_player_links.append(re.sub('.htm', '', s))
                    name_list.append(name)
                    roles_list.append(k)
                    start_year_list.append(int(start_year))
                    end_year_list.append(int(end_year))
                    # print(full_text)
            else:
                pass

    href_pdf = pd.DataFrame({
        "href": all_player_links, 
        "player_name": name_list, 
        "player_position": roles_list, 
        "start_year":start_year_list, 
        "end_year":end_year_list,

    })

    href_pdf = href_pdf[href_pdf["player_position"].isin(POS_LIST)]

    href_pdf = href_pdf[href_pdf["end_year"]>=YEAR_CUTOFF]

    print("Completed gathering player hrefs...")
    end = time.perf_counter()
    print(f"Execution time: {(end - start)/60:.2f} mins")
    return href_pdf


def get_player_metadata(soup):
    """
    Extract player metadata from a BeautifulSoup-parsed HTML document.

    This function looks for the "meta" section of a player's page (inside a <div id="meta">)
    and attempts to extract key player information such as name, position, and college.  
    If any field is missing or cannot be parsed, the function will return None for that field.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        A BeautifulSoup object containing the parsed HTML of a player profile page.

    Returns
    -------
    dict
        A dictionary with the following keys:
        - 'player_name' (str or None): The player's full name.
        - 'player_position' (str or None): The player's position.
        - 'player_college' (str or None): The player's college.
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

def safe_concat(df: pd.DataFrame, new_df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Safely concatenate two pandas DataFrames while enforcing a consistent set of columns.

    Parameters
    ----------
    df : pd.DataFrame
        The existing DataFrame to append to. If empty, only `new_df` will be used.
    new_df : pd.DataFrame
        The new DataFrame to concatenate.
    cols : list
        The ordered list of column names to enforce in the final DataFrame.
        Missing columns will be added and filled with None.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing rows from both `df` and `new_df`, reindexed to `cols`.
        All missing values are replaced with Python None (instead of NaN).

    Notes
    -----
    - If `df` is empty, the function simply returns `new_df` with columns aligned to `cols`.
    - This function ensures that column order is consistent across concatenations.
    - Replacing NaN with None is useful when exporting to formats (e.g., JSON, databases)
      that do not handle NaN gracefully.
    """
    if df.shape[0] > 0:
        df = pd.concat([df.reindex(columns=cols), new_df.reindex(columns=cols)], ignore_index=True)
    else:
        df = new_df.reindex(columns=cols)
    return df.where(pd.notnull(df), None)



def pull_gamelogs(href_pdf: list[str]):
    """
    Scrape game logs for players from Pro-Football-Reference.

    - Loads column names for each position (QB, RB, WR, TE) from a JSON file.
    - Iterates over player hrefs, scrapes metadata, and retrieves gamelog tables.
    - Cleans column names (handles multi-index, symbols, unnamed headers).
    - Adds metadata fields (player name, position, college).
    - Appends data into position-specific DataFrames.

    Args:
        href_pdf pd.DataFrame
        A DataFrame containing one row per player-role combination, with columns:
        - 'href' (str): The player's profile link (without the ".htm" suffix).
        - 'name' (str): The player's full name.
        - 'role' (str): The player's position abbreviation (split into multiple rows if multi-position).
        - 'start_year' (int): The first year the player was active.
        - 'end_year' (int): The last year the player was active..

    Returns:
    dict
        A dictionary with the following keys:
        - 'QB_gamelogs' (pd.DataFrame): QB Gamelog Data.
        - 'RB_gamelogs' (pd.DataFrame): RB Gamelog Data.
        - 'WR_gamelogs' (pd.DataFrame): WR Gamelog Data.
        - 'TE_gamelogs' (pd.DataFrame): TE Gamelog Data.
        
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
    start = time.perf_counter()
    start_total = time.perf_counter()
    print("\n\nPulling player gamelogs...")
    for row in href_pdf.itertuples(index=False):
        COUNTER+=1
        if COUNTER % 500 == 0:
            print(f"Iteration: {COUNTER}")
            end = time.perf_counter()
            print(f"Execution time: {(end - start)/60:.2f} mins")
            start = time.perf_counter()

        url_s = 'https://www.pro-football-reference.com' + row.href + '/gamelog/'

        html_raw = get_html_w_selenium(url_s)
        soup = bs4.BeautifulSoup(html_raw, 'html.parser')

        meta_info = get_player_metadata(soup)
        
        # if meta_info["player_position"] not in POS_LIST:
        #     continue
        # else:
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
            if col_1.startswith('Unnamed'):
                ## label home/away col with name
                if col_2.startswith('Unnamed'):
                    col_names.append('AT')
                else:
                    col_names.append(col_2)
            else:
                col_names.append( col_1 + '_' + col_2)

        

        df = df.set_axis(col_names, axis=1)


        try:
            df = df[df["Rk"] != "Rk"]
            df = df[~(pd.isna(df["Rk"]))]
        except:
            print(f"skipped href: {row.href}")
            continue

        # df["Date"] = pd.to_datetime(df["Date"])
        # df = df[df["Date"] >= DATE_CUTOFF]

        df["AT"] = df["AT"].apply(lambda x: 1 if x == "@" else 0)
        df["GS"] = df["GS"].apply(lambda x: 1 if x == "*" else 0)

        df["href"] = row.href
        df["player_name"] = row.player_name
        df["player_position"] = row.player_position
        df["player_college"] = meta_info["player_college"]

        if (row.player_position == 'QB') & (df.shape[0] > 0):
            qb_pdf = safe_concat(qb_pdf, df, qb_cols)
            
        elif (row.player_position == 'RB') & (df.shape[0] > 0):
            rb_pdf = safe_concat(rb_pdf, df, rb_cols)

        elif (row.player_position == 'WR') & (df.shape[0] > 0):
            wr_pdf = safe_concat(wr_pdf, df, wr_cols)

        elif (row.player_position == 'TE')  & (df.shape[0] > 0):
            te_pdf = safe_concat(te_pdf, df, te_cols)
        else: 
            print("nothing appended...")
            continue

    print("Completed pulling player gamelogs...")
    end_total = time.perf_counter()
    print(f"Total Execution time: {(end_total - start_total)/3600:.2f} hours")

    return {"QB_gamelogs":qb_pdf, "RB_gamelogs":rb_pdf, "WR_gamelogs":wr_pdf, "TE_gamelogs":te_pdf}

# def find_active_hrefs()