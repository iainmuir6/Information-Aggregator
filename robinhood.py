#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

import robin_stocks.robinhood as r
from finnhub import big_number
from functools import partial
import datapane as dp
import pandas as pd


def authenticate_(username, password):
    """

    :param username:
    :param password:
    :return:
    """

    r.authentication.login(
        username=username,
        password=password,
        expiresIn=30,
        scope='r'
    )
    return r


def load_portfolio(client):
    """

    :return:
    """

    # ----- Build Holdings -----
    equities = client.account.build_holdings()
    equities = pd.DataFrame(equities).T
    equities = equities.reset_index()

    stock = equities.loc[equities['type'] == 'stock']
    stock_tickers = stock['index'].tolist()
    etf = equities.loc[equities['type'] == 'etp']
    etf_tickers = etf['index'].tolist()

    crypto = client.crypto.get_crypto_positions()
    crypto = {
        curr['currency']['code']: curr for curr in crypto if float(curr['quantity']) != 0.0
    }
    crypto_tickers = list(crypto.keys())
    crypto = pd.DataFrame(crypto).T
    crypto = crypto.reset_index()

    # ----- Portfolio Value -----
    portfolio = client.profiles.load_portfolio_profile()

    return [stock_tickers, etf_tickers, crypto_tickers], [stock, etf, crypto], portfolio


def get_scroll_objects(row):
    """

    :param row
    :return:
    """
    current, p_close, symbol = row
    delta = float(current) / float(p_close) - 1
    delta = f'<span class="{"up" if delta >= 0 else "down"}">{round(delta * 100, 2)}%</span>'

    return f"""
        <a href="#"><b>{symbol}</b>&nbsp;<span class="price">${round(float(current), 2)}</span>&nbsp;{delta}</a>&nbsp;&nbsp;
    """.strip()


def ticker_toggle(key, tickers, label):
    """

    :param key
    :param tickers
    :param label
    :return:
    """

    bn = list(map(
        partial(big_number, key), tickers
    ))
    return dp.Toggle(
        dp.Group(
            *bn,
            columns=4
        ),
        label=label
    )


def make_header(header):
    """

    """

    return dp.HTML(
        """
        <html>
            <style type='text/css'>
                @keyframes cycle {
                    0%   {color: #89CFF0;}
                    25%  {color: #6495ED;}
                    50%  {color: #0096FF;}
                    100% {color: #0047AB;}
                }
                p {
                    text-align: center;
                }
                #container {
                    background: #ADD8E6;
                    padding: 5px 5px 5px 5px;
                    animation-name: cycle;
                    animation-duration: 4s;
                    animation-iteration-count: infinite;
                }
            </style>
            
            <div id="container">
                <p> 
                    <b>""" + header + """</b>
                </p>
            </div>
        </html>
        """
    )
