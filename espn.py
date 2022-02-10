#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

from errors import ErrorHandler, get_error_info
from itertools import zip_longest
from constants import SPORT_LOGOS
from datetime import timedelta
import datapane as dp
import pandas as pd
import datetime
import requests
import json
import math


# ------------------- ESPN NEWS --------------------
def format_news(article):
    """

    :param article:
    :return:
    """

    img, desc, pub, _, _, links, _, categories, headline, byline = article
    pub = datetime.datetime.strptime(pub, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y %I:%M%p')
    byline = f'<p font-size="11">{byline}</p>' if isinstance(byline, str) else ''

    return f"""
        <html>
            <h2>
                <a href="{links['web']['href']}">{headline}</a>
            </h2>
            {byline}
            <p font-size="10" color="gray">
                {pub}
            </p>
        </html>
    """


def news(sport):
    """

    :param sport:
    :return:
    """

    api_link = f"http://site.api.espn.com/apis/site/v2/sports/{sport}/news"
    with requests.get(api_link) as r:
        resp = json.loads(
            r.content.decode('utf-8')
        )['articles']
    articles = pd.DataFrame(resp)

    html = articles.apply(
        format_news,
        axis=1
    )

    return html


# ----------- ESPN STATS/LEADERS/YOUTUBE -----------
def format_stats(stats):
    """

    :param stats:
    :return:
    """
    stat, home, away = stats
    home = int(home) if isinstance(home, float) and ".0" in str(home) else home
    away = int(away) if isinstance(away, float) and ".0" in str(away) else away

    return f"""
        <div class='stat'><b>{stat}</b></div>
        <div class='value_{'high' if home > away else 'even' if home == away else 'low'}'>{home}</div>
        <div class='value_{'high' if away > home else 'even' if home == away else 'low'}'>{away}></div>
    """.strip()


def format_leaders(leaders):
    """

    :param leaders:
    :return:
    """
    stat, home_value, home_player, home_headshot, away_value, away_player, away_headshot = leaders
    # Cast non-floats to integer
    home = int(home_value) if isinstance(home_value, float) and ".0" in str(home_value) else home_value
    away = int(away_value) if isinstance(away_value, float) and ".0" in str(away_value) else away_value
    # Round "true" floats
    home = round(home, 2) if isinstance(home, float) else home
    away = round(away, 2) if isinstance(away, float) else away

    return f"""
        <div class='headshot'><img src="{home_headshot}" height="50"></img></div>
        <div class='player'>{home_player}</div>
        <div class='value_{'high' if home > away else 'even' if home == away else 'low'}'>{home}</div>
        <div class='stat'><b>{stat}</b></div>
        <div class='value_{'high' if away > home else 'even' if home == away else 'low'}'>{away}</div>
        <div class='player'>{away_player}</div>
        <div class='headshot'><img src="{away_headshot}" height="50"></img></div>
    """.strip()


# -------------- ESPN SCORES/SCHEDULE --------------
def parse_team(t):
    """

    :param t:
    :return:
    """
    global left

    team, score = t['team'], t['score']
    rank = t.get('curatedRank', None)
    stats = t.get('statistics', None)
    leaders = t.get('leaders', None)
    records = t.get('records', None)
    winner = t.get('winner', False)

    name, abbrev, display, short_display, color = list(team.values())[3:8]

    if not isinstance(short_display, str):
        short_display = display

    placeholder = 'https://freepikpsd.com/file/2019/10/placeholder-image-png-5-Transparent-Images.png'
    logo = team.get('logo', placeholder)

    rank = None if rank == '' else rank
    if rank is not None:
        rank = rank['current']
        rank = str(rank) if rank <= 25 else ''

    stats = None if stats == [] else stats
    if stats is not None:
        stats = pd.DataFrame(stats)[['abbreviation', 'displayValue']].loc[1:]
        stats.columns = ['Stat', short_display]

    if leaders is not None:
        leaders = [
            [
                lead['abbreviation'], lead['leaders'][0]['value'],
                lead['leaders'][0]['athlete']['fullName'], lead['leaders'][0]['athlete']['headshot']
            ] for lead in leaders
        ]
        leaders = pd.DataFrame(
            leaders, columns=['Stat', 'Value', 'Player', 'Headshot']
        )

    try:
        record = records[0]['summary']
    except (TypeError, KeyError):
        print(
            ErrorHandler("Missing Team Record; OK.", *get_error_info())
        )
        record = ''
    try:
        conf_record = records[3]['summary']
    except (TypeError, KeyError, IndexError):
        print(
            ErrorHandler("Missing Team Conference Record; OK.", *get_error_info())
        )
        conf_record = None

    info = """
            <div class="grid-item"> 
                <p class='info""" + ("_winner" if winner else "_loser") + """'>
                    <span>""" + (rank if rank is not None else "") + """</span>
                    <b>""" + short_display + """</b><br>
                    <span>""" + record + (f", {conf_record} CONF" if conf_record is not None else '') + """</span>
                </p>
            </div>
        """.strip()

    logo = """
            <div class="grid-item"> 
                <center>
                    <div class='image'>
                        <img src='""" + logo + """' height="50"/>
                    </div>
                </center>
            </div>
        """.strip()

    score = """
            <div class="grid-item"> 
                <p class='score""" + ("_winner" if winner else "_loser") + """'>
                    <b>""" + score + """</b>
                </p>
            </div>
        """.strip()

    if left:
        g = f"{info}\n{logo}\n{score}"
    else:
        g = f"{score}\n{logo}\n{info}"

    return g, stats, leaders


def format_scores(score):
    """

    :param score:
    :return:
    """
    # TODO Make an Iterable
    global left

    _, _, date, name, short_name, _, competitions, links, status = score
    link = links[0]['href']

    c = competitions[0]
    attendance = c.get('attendance', None)
    attendance = "{:,}".format(attendance) if attendance is not None else 'N/A'
    venue = c.get('venue', '')
    competitors = c['competitors']
    venue = f"{venue['fullName']} ({', '.join(venue['address'].values())})"

    results = list(map(parse_team, competitors))
    home, away = results

    game_stats = """
        <div class="grid-item7"> 
            <center>
                <a href='""" + link + """'>
                    <i>""" + venue + """ <br>  Attendance: """ + attendance + """</i>
                </a>
            </center>
        </div>
    """.strip()

    html = """
        <html>
            <style type='text/css'>
                .info_winner {
                    text-align:""" + ('right' if left else 'left') + """;
                    font-size:16px;
                    color:#000000;
                }
                .info_loser {
                    text-align:""" + ('right' if left else 'left') + """;
                    font-size:16px;
                    color:#808080;
                }
                .score_winner {
                    text-align:""" + ('left' if left else 'right') + """;
                    font-size:20px;
                    color:#000000;
                }
                .score_loser {
                    text-align:""" + ('left' if left else 'right') + """;
                    font-size:20px;
                    color:#808080;
                }
                .info_winner span {
                    font-size:12px;
                    color:#808080;
                }
                .info_loser span {
                    font-size:12px;
                    color:#808080;
                }
                .image {
                    display:flex;
                    justify-content:center;
                    align-items:center;
                }
                .images img {
                    margin-left:5px;
                    margin-right:5px;
                }
                a {
                    font-size:12px;
                    text-decoration:none;
                    color:#000000;
                }
                .grid-container {
                    display: grid;
                    grid-template-columns: auto auto auto;
                    border-top: 0px solid black;
                    border-left: 0px solid black;
                }
                .grid-container > div {
                    border-bottom: 0px;
                    border-right: 0px;
                }
                .grid-item7 {
                    grid-column-start: 1;
                    grid-column-end: 4
                }
            </style>
            <div class="grid-container">
                """ + home[0] + """
                """ + away[0] + """
                """ + game_stats + """
            </div>
        </html>
        """.strip()
    game = dp.HTML(html)

    blocks = list()

    home_team, away_team = name.split(' at ')

    stats_h, stats_a = home[1], away[1]
    if stats_h is not None and stats_a is not None:
        # TODO Actual Join...
        stats = stats_a
        stats[stats_h.columns[1]] = stats_h.iloc[:, 1]

        # stats = stats.apply(
        #     format_stats,
        #     axis=1
        # )
        # stats = """
        #     <html>
        #         <style type='text/css'>
        #             .header {
        #                 font-size:12px;
        #             }
        #             .stat {
        #                 font-size:12px;
        #             }
        #             .value_high {
        #                 font-size:12px;
        #                 font-weight:bold;
        #                 color:#023020;
        #             }
        #             .value_low {
        #                 font-size:12px;
        #             }
        #             .value_even {
        #                 font-size:12px;
        #             }
        #             .grid-container {
        #                 display: grid;
        #                 grid-template-columns: auto auto auto;
        #                 border-top: 0px solid black;
        #                 border-left: 0px solid black;
        #             }
        #             .grid-container > div {
        #                 border-bottom: 0px;
        #                 border-right: 0px;
        #             }
        #         </style>
        #         <div class="grid-container">
        #             <div class="header"><b>Stat</b></div>
        #             <div class="header"><b>""" + home_team.strip() + """</b></div>
        #             <div class="header"><b>""" + away_team.strip() + """</b></div>
        #             """ + "\n".join(stats) + """
        #         </div>
        #     </html>
        # """.strip()
        # print(stats)

        stats = dp.Table(
            stats
        )
        blocks.extend(
            [dp.Divider(), stats]
        )

    leaders_h, leaders_a = home[2], away[2]
    if leaders_h is not None and leaders_a is not None:
        leaders = leaders_h.merge(
            leaders_a,
            on='Stat'
        )
        leaders = leaders.apply(
            format_leaders,
            axis=1
        )
        html = """
            <html>
                <style type='text/css'>
                    .header {
                        font-size:16px;
                        text-align:center;
                        width: 50%;
                        padding: 20px;
                    }
                    .player {
                    	font-size:14px;
                        text-align:center;
                        width: 50%;
                        margin: auto;
                    }
                    .stat {
                        font-size:12px;
                        text-align:center;
                        width:50%;
                        margin:auto;
                        color:#808080;
                    }
                    .value_high {
                        font-size:16px;
                        font-weight:bold;
                        text-align:center;
                        width: 50%;
                        margin: auto;
                        color:#228B22;
                    }
                    .value_low {
                        font-size:16px;
                        font-weight:bold;
                        text-align:center;
                        width: 50%;
                        margin: auto;
                    }
                    .value_even {
                        font-size:16px;
                        font-weight:bold;
                        text-align:center;
                        width: 50%;
                        margin: auto;
                    }
                    .grid-container {
                        display: grid;
                        grid-template-columns: auto auto auto auto auto auto auto;
                    }
                </style>
                <div class="grid-container">
                    <div></div>
                    <div class="header"><b><u>""" + home_team.strip() + """</u></b></div>
                    <div></div>
                    <div class="header"><b></b></div>
                    <div></div>
                    <div class="header"><b><u>""" + away_team.strip() + """</u></b></div>
                    <div></div>
                    """ + "\n".join(leaders) + """
                </div>
            </html>
        """.strip()
        leaders = dp.HTML(html)

        blocks.extend(
            [dp.Divider(), leaders]
        )

    left = not left

    # return game
    return dp.Group(
        game,
        dp.Toggle(
            *blocks,
            label=f'Analysis: {short_name}'
        )
    )


def scores(s):
    """

    :param s: individual game result
    :return: sport-labeled dp.Group object

    # TODO Nested dp.Group (r=2, c=1): Inner Group and In-Depth Game Breakdown (stats/leaders/YouTube)
    """
    global left

    sport, code = s

    today = datetime.date.today()
    yesterday = (today - timedelta(days=1)).strftime('%Y%m%d')

    api_link = f"http://site.api.espn.com/apis/site/v2/sports/{code}/scoreboard?dates={yesterday}"

    with requests.get(api_link) as r:
        resp = json.loads(
            r.content.decode('utf-8')
        )['events']
    scoreboard = pd.DataFrame(resp)

    left = True
    games = list(scoreboard.apply(
        format_scores,
        axis=1
    ))

    return games


def group_sport(sport, games):
    """

    :param sport
    :param games
    :return
    """

    if len(games) == 0:
        return None

    game_group = dp.Group(
        *games,
        columns=2
    )

    logo = SPORT_LOGOS[sport]
    title = dp.HTML(f"""
    <html>
        <center>
            <img src={logo} width="75"/>
            <h1>{sport}</h1>
        </center>
    </html>
    """.strip())

    return dp.Group(
        title,
        dp.Divider(),
        game_group,
        label=sport
    )
