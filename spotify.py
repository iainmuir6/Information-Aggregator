#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

import datapane as dp


def get_spotify_embed(id_):
    """

    :param id_
    :return:
    """

    return dp.HTML(
        f"""
            <iframe src="https://open.spotify.com/embed/playlist/{id_}" 
            width="300" height="380" frameborder="0" allowtransparency="true"></iframe>
        """.strip()
    )
