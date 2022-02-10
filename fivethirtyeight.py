#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project: 538 Data - https://data.fivethirtyeight.com/
"""

import plotly.graph_objects as go
from constants import ESPN_SPORTS
import datapane as dp
import pandas as pd
import numpy as np
import requests
import csv


def active_teams(team):
    """

    :param team
    :return:
    """
    return team['team']['abbreviation'], f"#{team['team']['color']}"


def make_button(i, team, total, c):
    """

    :param i
    :param team
    :param total
    :param c
    :return:
    """

    #     args = [False] * total
    #     args[i] = True

    colors = ['#D3D3D3'] * total
    colors[i] = c[i]

    return dict(
        label=f'{team}',
        method="restyle",
        args=[{
            #             'visible': args,
            'colors': colors
        }]
    )


def plot_elo(elo_link):
    """

    :param elo_link
    :return:
    """

    # Parse Sport
    sport = elo_link[
            elo_link.rfind('/') + 1: elo_link.rfind('_')
            ].upper()
    code = ESPN_SPORTS[sport]

    # Retrieve Data
    with requests.Session() as s:
        resp = s.get(elo_link)
        content = resp.content.decode('utf-8')

        cr = csv.reader(
            content.splitlines(),
            delimiter=','
        )
    cr = list(cr)

    cols = cr[0]
    df = pd.DataFrame(
        cr[1:],
        columns=cols
    )
    df = df.replace('', None)
    df['elo1_post'] = pd.to_numeric(df['elo1_post'])
    df['elo2_post'] = pd.to_numeric(df['elo2_post'])

    elo_df1 = df[['date', 'team1', 'elo1_post']].dropna(axis=0)
    elo_df1.columns = ['date', 'team', 'elo']
    elo_df2 = df[['date', 'team2', 'elo2_post']].dropna(axis=0)
    elo_df2.columns = ['date', 'team', 'elo']
    elo = pd.concat(
        [elo_df1, elo_df2]
    ).sort_values(by='date')

    # Filter Active Teams
    t = f'http://site.api.espn.com/apis/site/v2/sports/{code}/teams'
    with requests.get(t) as resp:
        teams = resp.json()['sports'][0]['leagues'][0]['teams']

    info = np.array(list(map(active_teams, teams))).flatten().tolist()
    teams = info[::2]
    colors = info[1::2]
    d = dict(zip(teams, colors))

    elo = elo.loc[
        elo['team'].isin(teams)
    ]

    fig = go.Figure()

    buttons = list()
    for i, team in enumerate(teams):
        fig.add_trace(
            go.Scatter(
                x=elo['date'][elo['team'] == team],
                y=elo['elo'][elo['team'] == team],
                mode='lines',
                name=team,
                line=dict(
                    color=d[team]
                ),
                visible=True
            )
        )
        buttons.append(
            make_button(i, team, len(teams), colors)
        )

    # Add Dropdown
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                type="dropdown",
                buttons=buttons,
                x=0,
                y=1.1,
                xanchor='left',
                yanchor='bottom'
            )
        ],
        title={
            'text': f"<b>{sport} ELO over Time</b>",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="<b>Date</b>",
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        xaxis_tickformatstops = [
            dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
            dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
            dict(dtickrange=[60000, 3600000], value="%H:%M m"),
            dict(dtickrange=[3600000, 86400000], value="%H:%M h"),
            dict(dtickrange=[86400000, 604800000], value="%e. %b d"),
            dict(dtickrange=[604800000, "M1"], value="%e. %b w"),
            dict(dtickrange=["M1", "M12"], value="%b '%y M"),
            dict(dtickrange=["M12", None], value="%Y Y")
        ],
        yaxis_title="<b>ELO</b>"
    )

    fig.update_xaxes(
        tickformat="%Y"
    )

    return dp.Plot(
        fig,
        label=sport
    )
