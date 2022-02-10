#!/usr/bin/env python

"""
    Author: Iain Muir, iam9ez@virginia.edu
    Date:
    Project:
"""

# Modules for scraping
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
# import time

# Other
import pandas as pd
import numpy as np
import sys

# YouTube
from google.auth.transport.requests import Request
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from pytube import YouTube
import pickle
import os


def build_client():
    """

    :return:
    """

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_key = 'AIzaSyBW3cmEgVnwWUeCoV0uDov_YrEoJvMiz84'
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "../InformationAggregator/client_secret.json"
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    credentials = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    client = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials, developerKey=api_key
    )

    return client


def youtube_data():
    """

    :return:
    """

    youtube = build_client()

    # TODO Dictionary for Playlists
    playlists = {
        'nba': 'PLlVlyGVtvuVkIjURb-twQc1lsE4rT1wfJ',
        # 'mlb': 'PLL-lmlkrmJalROhW3PQjrTD6pHX1R0Ub8',
        'nhl': 'PL1NbHSfosBuHInmjsLcBuqeSV256FqlOO'
    }

    # playlist_id = "PLlVlyGVtvuVkIjURb-twQc1lsE4rT1wfJ"
    data = []

    for sport, playlist_id in playlists.items():
        videos = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=200,
            playlistId=playlist_id
        ).execute()['items']

        for v in videos:
            title = v['snippet']['title']
            if title == 'Private video':
                continue

            index = {
                'nba': (title.rfind('|') + 2, -1),
                'nhl': (title.find('/') - 2, title.rfind('|'))
            }.get(sport, 'None')
            date_format = {
                'nba': '%B %d, %Y',
                'nhl': '%m/%d/%y'
            }.get(sport, 'None')

            date = datetime.today() - timedelta(days=1)
            vid_date = title[index[0]:index[1]].strip() + (title[-1] if sport == 'nba' else '')
            if datetime.strptime(vid_date, date_format).date() != date.date():
                # print(datetime.strptime(vid_date, date_format).date(), date.date())
                continue

            teams = title[:title.find('|') - 1].title().split()
            team1, team2 = teams[0], teams[2]
            id_ = v['contentDetails']['videoId']
            img = v['snippet']['thumbnails']['default']['url']
            # timestamp_ = v['snippet']['publishedAt']
            # description = v['snippet']['description']

            # url = 'https://www.youtube.com/watch?v=' + id_ + '&list=' + playlist_id
            url = 'https://www.youtube.com/embed/' + id_
            data.append([team1, team2, date, img, url])

    return data


def main():
    """

    :return:
    """
    youtube_data()


if __name__ == '__main__':
    main()