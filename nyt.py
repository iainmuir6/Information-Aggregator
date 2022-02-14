#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

from itertools import zip_longest
import datapane as dp
import pandas as pd
import datetime
import requests
import json


def top_stories(api_key):
    """
    :param api_key

    The possible section value are: arts, automobiles, books, business, fashion, food, health, home, insider, magazine,
    movies, nyregion, obituaries, opinion, politics, realestate, science, sports, sundayreview, technology, theater,
    t-magazine, travel, upshot, us, and world.

    https://api.nytimes.com/svc/topstories/v2/{section}.json?api-key={yourkey}
    http://api.nytimes.com/svc/semantic/v2/concept/name/<concept_type>/<specific_concept>.json(?optional_parameters)&api-key=your-API-key

    :return:
    """

    # Query Top Stories
    section = 'world'
    api_link = f"https://api.nytimes.com/svc/topstories/v2/{section}.json?api-key={api_key}"
    with requests.get(api_link) as r:
        resp = json.loads(
            r.content.decode('utf-8')
        )['results']
    a = pd.DataFrame(resp)

    return a


def semantics(company, api_key):
    """

    :param company
    :param api_key
    :return:
    """

    # Company Specific News
    api_link = f"http://api.nytimes.com/svc/semantic/v2/concept/name/nytd_org/{company}.json?fields=all&api-key={api_key}"
    with requests.get(api_link) as r:
        resp = json.loads(r.content.decode('utf-8'))
    articles = pd.DataFrame(resp)
    print('NYT:', articles.columns)

    return articles


def format_article(article, source='NYT'):
    """

    :param article
    :param source
    :return:
    """

    if source == 'NYT':
        section, _, title, abstract, url, _, byline, _, _, _, date, _, _, _, _, _, _, img, _ = article
        date = datetime.datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%y %I:%M:%S %p')
    else:
        _, byline, _, img, date, _, source, _, title, _, url, _, _, abstract, _, _ = article
        date = datetime.datetime.strptime(str(date)[:-6], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%y %I:%M:%S %p')

    media = dp.HTML(f"""
        <img src="{img}" width="200"/>
    """.strip())
    html = dp.HTML(
        """
        <html>
            <style type='text/css'>
                h4 {
                    text-align:left;
                }
                a {
                    text-decoration:none;
                    color:#000000;
                }
                p {
                    text-align:left;
                    font-size:14px;
                    color=#000000;
                }
                .info span {
                    font-size:12px;
                    color=#808080;
                }
            </style>
            
            <h4><a href='""" + url + """' target="_blank">""" + title + """</a></h4>
            <p class='info'>
                <span><i>""" + byline + '<br>' + date + """</i></span><br><br>
                """ + abstract + """
            </p>
        </html>
        """.strip()
    )

    return dp.Group(
        media,
        html,
        columns=2
    )


def format_sections(groups, subsection):
    """

    :param groups
    :param subsection
    :return:
    """

    group = groups.get_group(subsection)
    articles = group.apply(
        format_article,
        axis=1
    )
    subsection = subsection.title()

    cols = 2
    empty = dp.Text('.')

    groups = list(zip_longest(*(iter(articles),) * cols, fillvalue=empty))
    article_groups = [
        dp.Group(columns=cols, *g) for g in groups
    ]
    article_group = dp.Group(
        *article_groups,
        label=subsection
    )

    return article_group
