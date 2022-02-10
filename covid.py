#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

import plotly.express as px
import datapane as dp
import altair as alt
import pandas as pd


def county_choropleth(data, geo_json):
    """

    :param data:
    :param geo_json:
    :return:
    """

    colorscale = [
        "#f7fbff", "#ebf3fb", "#deebf7", "#d2e3f3", "#c6dbef", "#b3d2e9",
        "#9ecae1", "#85bcdb", "#6baed6", "#57a0ce", "#4292c6", "#3082be",
        "#2171b5","#1361a9", "#08519c", "#0b4083", "#08306b"
    ]

    covid_fig = px.choropleth(
        data,
        geojson=geo_json,
        locations='fips',
        color='case_ratio',
        color_continuous_scale=colorscale,
        hover_data=['county', 'cases', 'population'],
        scope="usa"
    )
    covid_fig.update_layout(
        title={
            'text': f"<b>COVID Cases per Capita by State</b>",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )

    return covid_fig


def plot_state(state, data):
    """

    :param state
    :param data
    :return:
    """

    df = pd.DataFrame(data)
    df = df.fillna(0)

    # CASES
    cases = altair_line(
        df,
        alt.X('date:T', axis=alt.Axis(format='%b %Y')),
        "cases",
        "Date",
        "Cases",
        f"{state} Cases over Time",
    )

    # DEATHS
    deaths = altair_line(
        df,
        alt.X('date:T', axis=alt.Axis(format='%b %Y')),
        "deaths",
        "Date",
        "Deaths",
        f"{state} Deaths over Time",
    )

    # VACCINES
    vaccines = altair_line(
        df,
        alt.X('date:T', axis=alt.Axis(format='%b %Y')),
        "vaccinesAdministered",
        "Date",
        "Vaccines",
        f"{state} Vaccines over Time",
    )

    return dp.Group(
        dp.Plot(cases),
        dp.Plot(deaths),
        dp.Plot(vaccines),
        label=state
    )


def altair_line(data, x, y, x_axis, y_axis, title, color1='darkgreen', color2='white'):
    """

    :param data:
    :param x:
    :param y:
    :param x_axis:
    :param y_axis:
    :param title:
    :param color1:
    :param color2:
    :return:
    """

    fig = alt.Chart(
        data,
        height=400,
        width=400
    ).mark_area(
        line={'color': color1},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color=color2, offset=0),
                   alt.GradientStop(color=color1, offset=1)])
    ).encode(
        x=x,
        y=y
    )
    fig.title = title
    fig.encoding.x.title = x_axis
    fig.encoding.y.title = y_axis

    return fig
