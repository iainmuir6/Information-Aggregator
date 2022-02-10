#!/usr/bin/env python
# coding: utf-8

# # Information Aggregator

# #### Author: Iain Muir, iam9ez@virginia.edu  
# *Date: January 20th, 2021  
# Project: Information Aggregator Application — powered by Datapane*

# ## Table of Contents

# In[1]:
# TODO - TOC...


# ## 0. Import Libraries and Secrets

# Importing Standard Libraries...

# In[2]:

from constants import ROOT, API_LOGOS, ESPN_SPORTS, SPORT_LOGOS
from plotly.subplots import make_subplots
import robin_stocks.robinhood as r
import plotly.graph_objects as go
from itertools import zip_longest
from IPython import get_ipython
from datetime import timedelta
from bs4 import BeautifulSoup
from functools import partial
import plotly.express as px
import datapane as dp
import altair as alt
import pandas as pd
import numpy as np
import webbrowser
import datetime
import requests
import time
import json
import math
import csv


# Importing Modules...

# In[3]:

from finnhub import quote, candles, candlestick, name_search, big_number, profile, news
from espn import format_news, news, parse_team, format_scores, scores, group_sport
from nyt import top_stories, semantics, format_article, format_sections
from cnn_money import cnn_big_numbers, format_modules, group_modules
from fivethirtyeight import active_teams, make_button, plot_elo
from covid import county_choropleth, plot_state, altair_line
from robinhood import ticker_toggle, make_header
from spotify import get_spotify_embed


# Checking Datapane version...

# In[4]:


# version = get_ipython().getoutput('datapane --version')


# In[5]:


# assert version[0].split()[2] == '0.13.2'


# In[6]:


# get_ipython().system('datapane login --token=55010cebc170ecfbeddb82838c360776bf36f6be')


# Open and Unpack Secrets File...

# In[7]:


with open('secrets.json') as s:
    secrets = json.loads(s.read())


# In[8]:


# Datapane
DATAPANE_KEY = secrets['datapane']
    
# Finnhub
FINNHUB_KEY = secrets['finnhub']

# Robinhood
ROBIN_USERNAME, ROBIN_PASSWORD = secrets['robinhood'].values()

# New York Times
NYT_KEY,  NYT_SECRET, NYT_ID = secrets['nyt'].values()

# Spotify
SPOTIFY_KEY, SPOTIFY_ID = secrets['spotify'].values()


# In[9]:


AUTH_URL = 'https://accounts.spotify.com/api/token'
auth_response = requests.post(
    AUTH_URL, 
    {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_ID,
        'client_secret': SPOTIFY_KEY
    }
)
auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']


# ## 1. Build Report Compenents

# In[10]:


TODAY = datetime.date.today()


# ### 1.1 Header

# In[11]:


datapane, nyt, espn, spotify, _538, lichess = API_LOGOS.values()


# In[12]:


header_logo = dp.HTML(
    """
    <html>
        <style type='text/css'>
            .images {
                display:flex;
                justify-content:center;
                align-items:center;
            }
            .images img {
                margin-left:5px;
                margin-right:5px;
            }
        </style>
        
        <center>
            <div class='images'>
                <img src='""" + datapane + """' width="75"/>
                <img src='""" + nyt + """' width="100"/>
                <img src='""" + espn + """' width="75"/>
                <img src='""" + spotify + """' width="75"/>
                <img src='""" + _538 + """' width="75"/>
                <img src='""" + lichess + """' width="75"/>
            </div>
        </center>
    </html>
    """
)


# In[13]:


header_text = dp.HTML(
    """
    <html>
        <style type='text/css'>
            @keyframes rotate {
                0%   {color: #EEE;}
                25%  {color: #EC4899;}
                50%  {color: #8B5CF6;}
                100% {color: #EF4444;}
            }
            h1 {
                color:#eee;
                animation-name: rotate;
                animation-duration: 4s;
                animation-iteration-count: infinite;
            }
        </style>
        <center>
            <h1>Morning Scoop</h1>
            <i>""" + TODAY.strftime('%A %B %d, %Y') + """<i>
        </center>
    </html>
    """
)


# In[14]:


header_description = dp.Text("""
Welcome to the Morning Scoop! This project is aimed to aggregate and display an eclectic and wide-ranging mix of information, data, and visualizations. Information sources include The New York Times, ESPN, FiveThirtyEight, and many more. Enjoy!

This report is powered by Datapane.

""".strip())


# ### 1.2 Main Selector

# In[15]:


datetime.date.today()


# #### 1.2.1 Sports Results and Analytics

# In[16]:


espn_games = list(map(scores, ESPN_SPORTS.items()))


# In[17]:


espn_groups = list(map(group_sport, ESPN_SPORTS.keys(), espn_games))
espn_groups = list(filter(None, espn_groups))


# In[18]:


# TODO Toggle Results and Upcoming
# TODO Sports Highlights and Game Breakdown
# TODO Group --> HTML Table (condensed...)


# #### 1.2.2 Top U.S. News

# In[19]:


articles = top_stories(NYT_KEY)


# In[20]:


articles = articles.loc[articles['item_type'] != 'Promo']
articles = articles.loc[articles['multimedia'].str.len() == 1]
articles['multimedia'] = articles['multimedia'].str[0].str['url']
articles['subsection'] = articles['subsection'].replace('', 'miscellaneous')


# In[21]:


grouped_articles = articles.groupby(
    'subsection',
    axis=0
)


# In[22]:


ordered_groups = grouped_articles.size().sort_values(ascending=False)


# In[23]:


article_sections = list(map(
    partial(format_sections, grouped_articles), ordered_groups.index
))


# In[24]:


# TODO Article Links


# #### 1.2.3 Stock Market

# ##### FAANG and ETF Prices and Candlestick

# In[25]:


COLUMNS = 5
TICKERS = [
    'SPY', 'QQQ', 'XLF', 'IWM', 'BND',
    'FB', 'AAPL', 'AMZN', 'NFLX', 'GOOG',
]


# In[26]:


big_numbers = []
figures = []

for i, t in enumerate(TICKERS):
    close, delta, delta_pct, high, low, open_, p_close, _ = quote(FINNHUB_KEY, t)
    df = candles(FINNHUB_KEY, t)
    
    bn = dp.BigNumber(
        heading=t,
        value=f"${round(close, 2)}",
        change=f"{round(delta_pct, 2)}%",
        is_upward_change=True if delta_pct > 0 else False
    )
    big_numbers.append(bn)
    
    figure = candlestick(df, t)
    figures.append(figure)


# In[27]:


ticker_groups = list(zip_longest(*(iter(big_numbers),) * COLUMNS, fillvalue=''))
ticker_groups = [
    dp.Group(columns=COLUMNS, *g) for g in ticker_groups
]


# ##### Scrape CNN Market

# In[28]:


cnn = 'https://money.cnn.com/data/markets'
with requests.get(cnn) as page:
    soup = BeautifulSoup(page.content, 'html.parser')


# In[29]:


modules = soup.find_all('div', class_='module')
key_stats = soup.find('ul', class_='module-body wsod key-stats')


# In[30]:


pairs = list(map(format_modules, modules))
pairs = list(filter(None, pairs))
pairs = list(sum(pairs, ()))


# In[31]:


headers = pairs[::2]
modules = pairs[1::2]


# In[32]:


module_groups = list(map(group_modules, headers, modules))


# ##### Free Stock Search

# In[33]:


# sp500_figures = free_stock_search(FINNHUB_KEY)


# #### 1.2.4 Portfolio Performance

# Authenticate

# In[34]:


# r.login(
#     username=ROBIN_USERNAME,
#     password=ROBIN_PASSWORD,
#     expiresIn=30,
#     by_sms=True,
#     scope='r'
# )


# Display Holdings

# In[35]:


equity_tickers =  ['AAPL', 'MSFT', 'GOOG']
etf_tickers = ['MTUM', 'USO', 'USMV']
crypto_tickers = ['BTC']
tickers = equity_tickers + etf_tickers + crypto_tickers


# In[36]:


portfolio_toggles = list(
    map(
        lambda t, l: ticker_toggle(FINNHUB_KEY, t, l) if len(t) != 0 else None, 
        [equity_tickers, etf_tickers, crypto_tickers],
        ['Equity', 'ETF', 'Crypto']
    )
)
portfolio_toggles = list(filter(None, portfolio_toggles))


# Overall Portfolio

# In[37]:


# Get Portfolio Value


# In[38]:


value = 47.11
delta_pct = 1.2 
portfolio_value = dp.BigNumber(
    heading="Overall Portfolio",
    value=f"${round(value, 2)}",
    change=f"{round(delta_pct, 2)}%",
    is_upward_change=True if delta_pct > 0 else False
)


# Portfolio Candlesticks

# In[39]:


portfolio_candles = list(map(
    partial(candles, FINNHUB_KEY), tickers
))
portfolio_figures = list(map(
    candlestick, portfolio_candles, tickers
))


# #### 1.2.5 Data Exploration and Visualization

# ##### Five Thirty Eight

# In[40]:


NBA_ELO = 'https://projects.fivethirtyeight.com/nba-model/nba_elo.csv'
NFL_ELO = 'https://projects.fivethirtyeight.com/nfl-api/nfl_elo.csv'
MLB_ELO = 'https://projects.fivethirtyeight.com/mlb-api/mlb_elo.csv'
ELO_LINKS = [
    NBA_ELO, NFL_ELO, MLB_ELO
]


# In[41]:


YEAR = 2021
NCAA = f'https://projects.fivethirtyeight.com/march-madness-api/{YEAR}/fivethirtyeight_ncaa_forecasts.csv'
POLLS = 'https://github.com/fivethirtyeight/data/tree/master/polls'


# In[42]:


_538_figures = list(map(
    plot_elo, ELO_LINKS
))


# In[43]:


# TODO Clean and Style Graphs
    # Restyle Color
# TODO Header Blocks --> Intro ELO and By Sport
# Incorporate March Madness and ~Polls~


# ##### Spotify

# In[44]:


TOP50 = '37i9dQZEVXbLRQDuF5jeBp'
MIX1 = '37i9dQZF1E35bNzojVbMHG'
MIX2 = '37i9dQZF1E38sJU7OsGSQi'
MIX3 = '37i9dQZF1E37xnKwvD1GJE'

PLAYLISTS = [
    TOP50, MIX1, MIX2, MIX3
]


# In[45]:


HEADERS = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}


# In[46]:


playlists_html = list(map(get_spotify_embed, PLAYLISTS))


# In[47]:


# TODO Correct Embedding...


# ##### Lichess

# In[48]:


# TODO Top Player Matches


# ##### COVID

# In[49]:


COVID_KEY = '2ec6fd90dd9f4d99a3f73a03ee4945b4'


# In[50]:


geo_link = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
with requests.get(geo_link) as r:
    geo_json = r.json()


# In[51]:


counties = f'https://api.covidactnow.org/v2/counties.json?apiKey={COVID_KEY}'


# In[52]:


with requests.get(counties) as r:
    counties = pd.DataFrame(r.json())


# In[53]:


counties['cases'] = counties.actuals.str['cases']
counties['case_ratio'] = counties.cases / counties.population
counties['deaths'] = counties.actuals.str['deaths']
counties['death_ratio'] = counties.deaths / counties.population
counties['vaccine_ratio'] = counties.metrics.str['vaccinationsCompletedRatio']


# In[54]:


covid_fig = county_choropleth(
    counties, geo_json
)


# In[55]:


states = f'https://api.covidactnow.org/v2/states.timeseries.json?apiKey={COVID_KEY}'


# In[56]:


with requests.get(states) as r:
    states = pd.DataFrame(r.json())


# In[57]:

covid_figures = list(map(
    plot_state, states.state, states.actualsTimeseries
))


# ##### Data Exploration Compilation

# In[58]:


_538_group = dp.Toggle(
    dp.Select(
        *_538_figures
    ),
    label = 'Five Thirty Eight'
)
lichess_group = dp.Toggle(
    dp.Text("Lichess", label='A'),
    label = 'Lichess'
)
spotify_group = dp.Toggle(
    dp.Group(
        *playlists_html,
        columns=4
    ),
    label = 'Spotify'
)
covid_group = dp.Toggle(
    dp.Plot(
        covid_fig
    ),
    dp.Divider(),
    dp.Select(
        *covid_figures
    ),
    label = 'COVID'
)


# In[59]:


data_groups = [
    covid_group,
    _538_group
#     spotify_group,
#     lichess_group,
]


# #### 1.2.5 Compiled Selector

# In[60]:


sports = dp.Group(
    dp.Select(
        *espn_groups,
        type=dp.SelectType.DROPDOWN
    ),
    label='Sports: Results and Analysis',
)
news = dp.Group(
    dp.Select(*article_sections),
    label='Top World News'
)
market = dp.Group(
    *ticker_groups,
    dp.Divider(),
    dp.Select(
        *figures
    ),
    dp.Divider(),
    *module_groups[:2],
    dp.Group(
        *module_groups[2:],
        columns=4
    ),
#     dp.Select(
#         *sp500_figures
#     ),
    label='Stock Market'
)
portfolio = dp.Group(
    portfolio_value,
    dp.Divider(),
    *portfolio_toggles,
    dp.Divider(),
    dp.Select(
        *portfolio_figures
    ),
    label='Robinhood Portfolio'
)
data = dp.Group(
    *data_groups,
    label='Data Exploration'
)


# In[61]:


main_select = dp.Select(
    blocks=[
        sports, news, market, portfolio, data
    ],
    type=dp.SelectType.TABS
)


# ### 1.3 Credits

# In[62]:


credits = dp.Text("Report built by Iain Muir.")


# ## 2. Datapane Report

# In[63]:


report = dp.Report(
    header_logo,
    header_text,
    header_description,
    dp.Divider(),
    main_select,
    dp.Divider(),
    credits
)


# In[64]:


try:
    report.upload(
        name='Information Aggregator',
        open=False
    )
except requests.exceptions.HTTPError:
    time.sleep(5)
    print('Trying again...')
    report.upload(
        name='Information Aggregator',
        open=False
    )


# In[65]:


report.save(
    path=f'{ROOT}/Output/Information-Aggregator_Old.html'
)


# In[66]:


webbrowser.open(
    report.web_url
)

