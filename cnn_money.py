#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

from functools import partial
import datapane as dp


def cnn_big_numbers(module_header, tick_info):
    """

    :param module_header
    :param tick_info
    :return:
    """
    try:
        ticker, num1, num2 = tick_info
    except ValueError:
        ticker, num1 = tick_info
        num2 = None

    if module_header in ['Gainers', 'Losers']:
        return dp.BigNumber(
            heading=ticker,
            value='-',
            change=num1,
            is_upward_change=True if num1[0] != '-' else False
        )
    elif module_header == 'Currencies':
        return dp.BigNumber(
            heading=ticker,
            value=num1
        )
    else:
        return dp.BigNumber(
            heading=ticker,
            value=num1,
            change=num2,
            is_upward_change=True if num2[0] != '-' else False
        )


def format_modules(module):
    """

    :param module
    :return:
    """

    module_header = module.find('a', class_='module-header')

    if module_header is None:
        return None
    else:
        module_header = module_header.text.strip()

    if module_header == 'World Markets': return None
    if module_header == 'Fear & Greed Index': return None
    if module_header in ['Top Investing Stories', 'Bitcoin (XBT)']: return None

    items = module.ul.find_all('li')
    text = [
               list(filter(lambda i: i != '', item.text.split('\n'))) for item in items
           ][:5]

    bn = list(map(partial(cnn_big_numbers, module_header), text))
    return module_header, bn


def group_modules(header, module):
    """

    :param header
    :param module
    :return:
    """

    html = dp.HTML(
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
    group = dp.Group(
        *module,
        columns=5 if header in ['Key Stats', 'Most Popular Stocks'] else 1
    )
    return dp.Group(
        html,
        group
    )
