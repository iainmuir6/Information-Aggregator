"""
Iain Muir, iam9ez@virginia.edu

Scrapes personalized sports highlights data from theScore.com and deploys a Streamlit dashboard

STRUCTURE:
    Loop of inputs (no loop for personal use)
        Loop of leagues
            Loop of games

TODO
    • Generate Data Source Once
        • Highlights and YouTube
    • Unfiltered Highlights
    • Asynchronous

"""

# Modules for scraping
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
# import time

# Other
from constants import INDICES, LOGOS, CODES, RESPONSE
import streamlit as st
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


def print_exception():
    """
    exc_type --> error class (ex. <class 'ZeroDivisionError'>)
    exc_obj --> error description (ex. division by zero)
    tb --> error traceback (ex. <traceback object at 0x1031e7b08>)
        tb.tb_lineno --> line number of the error
    """
    exc_type, exc_obj, tb = sys.exc_info()
    print(str(exc_obj).capitalize(), "on line", tb.tb_lineno)
    print("     |->  " + str(exc_type))
    print("     |->  " + str(tb))


def get_nfl_week():
    """
    Scrapes the duration of the current NFL regular season from Wikipedia in order to calculate the current week

    TODO Adjust for playoffs

    :return Current week in the NFL
    """

    url = "https://en.wikipedia.org/wiki/" + str(year) + "_NFL_season"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    duration = soup.find("table", class_='infobox vevent').tbody.find("td").text
    start = datetime.strptime(duration[duration.find("(") + 1: duration.find(")")], "%Y-%m-%d")
    end = datetime.strptime(duration[duration.rfind("(") + 1: duration.rfind(")")], "%Y-%m-%d")

    return 1 + ((date - start).days // 7) if date < end else 17 + ((date - end).days // 7)


def loop_data(rows):
    """
    :argument rows – DataFrame of favorite sports teams/leagues
    :argument today_date

    Initial Loop: loop through each person in inputs (only one call for personal use)

    • Creates list of leagues and teams given the input data

    :return no return value
    """

    if rows[0] != '7/21/2020 11:08:49' and rows[1] != "iam9ez@virginia.edu":
        return None, None

    leagues = np.array(rows[2].split(","))
    indices_arr = np.array(list(map(lambda x: INDICES[x.strip()], leagues)))
    teams = np.array(list(map(lambda x: rows[x].split(","), indices_arr)))

    df = pd.DataFrame(columns=['league', 'tm1', 'score1', 'score2', 'tm2', 'gameLink', 'logo1', 'logo2'])
    league_data = list(map(lambda x, y: loop_leagues(x.strip(), y), leagues, teams))

    for l in league_data:
        if isinstance(l, list):
            temp = pd.DataFrame(l,
                                columns=['league', 'tm1', 'score1', 'score2', 'tm2', 'gameLink', 'logo1', 'logo2'])
        else:
            temp = pd.DataFrame([[l, None, None, None, None, None, None, None]],
                                columns=['league', 'tm1', 'score1', 'score2', 'tm2', 'gameLink', 'logo1', 'logo2'])

        df = df.append(temp)

    return df


def loop_leagues(league, teams_list):
    """
    :argument league – specific sports league (full name, ex. "Champions League)
    :argument teams_list – list of favorite teams within the league

    Secondary Loop: loop through each of their favorite sports leagues

    • Scrapes all games on the given date for the specific league
    • Checks if any favorite teams played on this date

    :return None – breaks "loop" if no favorite teams played (condition == False)
    """

    sport_shortened = CODES[league]
    url = "https://www.thescore.com/" + sport_shortened + "/events/" + \
          ("conference/All%20Conferences/date/" + str(date.date()) if sport_shortened == 'ncaab' else
           "date/" + str(year) + "-" + str(get_nfl_week()) if sport_shortened == 'nfl' else
           "date/" + str(date.date()))

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    all_games = soup.find_all("div", class_="col-xs-12 col-md-6")
    teams_list = np.array(list(map(lambda x: x.strip(), teams_list)))

    if sport_shortened == 'ncaab':
        all_teams = [team.text for team in soup.find_all('div', class_='EventCard__teamName--JweK5')]
        lst = [ele in teams_list for ele in all_teams]
        condition = bool(any(lst))
    else:
        lst = [ele in str(soup) for ele in teams_list]
        condition = bool(any(lst))

    if not condition:
        return league

    games = list(map(lambda x: loop_games(x, teams_list, league), all_games))
    return games


def loop_games(game_html, team_list, league):
    """
    :argument game_html – HTML / soup of individual games played that day
    :argument team_list – list of favorite teams within the league
    :argument league –

    Third/Final Loop: loop through each game played on that date

    • Scrape the following data for each game and deploy to dashboard in Markdown format
        teams (tm1, tm2)
        scores (scores[0].text, scores[1].text)
        logos (logo1, logo2)

    :return None – breaks "loop" after markdown statements to avoid repeat
    """

    teams = game_html.find_all("div", class_="EventCard__teamColumn--17asJ")
    tm1, tm2 = teams[0].text, teams[1].text

    if tm1 in team_list or tm2 in team_list:
        scores = game_html.find_all("div", class_="EventCard__scoreColumn--2JZbq")
        team_logos = game_html.find_all("div", class_="EventCard__teamLogo--3D7cf")
        logo1, logo2 = team_logos[0].span.img["src"], team_logos[1].span.img["src"]
        score1, score2 = scores[0].text, scores[1].text

        try:
            link = "https://www.thescore.com" + game_html.span.span.a["href"]
        except TypeError:
            link = "https://www.thescore.com" + game_html.span.a["href"]

        if tm1 == "Juventus":
            logo1 = "https://upload.wikimedia.org/wikipedia/en/8/84/Juventus_IF_logo.svg"
        elif tm2 == "Juventus":
            logo2 = "https://upload.wikimedia.org/wikipedia/en/8/84/Juventus_IF_logo.svg"
        if tm1 == "WSH Football Team":
            tm1 = "WSH Football"
        elif tm2 == "WSH Football Team":
            tm2 = "WSH Football"

        game_data = [league, tm1, score1, score2, tm2, link, logo1, logo2]
        return game_data

    else:
        return [None, None, None, None, None, None, None, None]


def display(data):
    """
    :argument data
    """

    youtube_df = pd.DataFrame(youtube_data(), columns=['tm1', 'tm2', 'date', 'img', 'link'])
    print(youtube_df)

    no_highlights = "<center> "
    for sport in CODES.keys():
        games = data.query('league == "' + sport + '"')
        if len(games.values) == 0:
            no_highlights += '<img src="' + LOGOS[CODES[sport]] + '" width="40"/>                               '
            continue
        else:
            st.markdown("<h3 style='text-align: center;'> " + sport + "</h1>",
                        unsafe_allow_html=True)
            counter = 0
            col1, col2 = st.beta_columns(2)

            for g in games.sort_values(by='score1', ascending=False).values:
                counter += 1
                col = col1 if counter % 2 != 0 else col2
                try:
                    league_, tm1, score1, score2, tm2, link, logo1, logo2 = g
                except ValueError:
                    tm1, score1, score2, tm2, link, logo1, logo2 = g

                try:
                    lst = [tm1.split()[1].title(), tm2.split()[1].title()]
                except IndexError:
                    lst = []

                try:
                    score1, score2 = str(int(score1)), str(int(score2))
                except ValueError:
                    score1, score2 = '', ''

                font_size = '14'
                if len(tm1 + tm2 + score1 + score2) > 30:
                    font_size = '13'

                col.markdown("<p style='font-size:" + font_size + "px;text-align:center;'> <img src='" + logo1 +
                             "' height='40' /> <b>" + tm1 + "</b> " + score1 + " <a href='" + link + "'> -</a> "
                             + score2 + " <b>" + tm2 + "</b> <img src='" + logo2 + "' height='40' /> </p>",
                             unsafe_allow_html=True)
                if sport == 'NBA' or sport == 'NHL':
                    try:
                        # ---- OPTION 1 -----
                        # col.video(list(youtube_df.query('tm1 in @lst')['link'])[0])

                        # ---- OPTION 2 -----
                        link = list(youtube_df.query('tm1 in @lst')['link'])[0]
                        col.markdown(
                            '<iframe width="342" height="257" src="' + link + '" '
                            'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
                            'gyroscope; picture-in-picture" allowfullscreen></iframe>',
                            unsafe_allow_html=True
                        )

                        # ---- OPTION 3 -----
                        # link = list(youtube_df.query('tm1 in @lst')['link'])[0]
                        # YouTube(link).streams.filter(
                        #     res='720p', file_extension='mp4').first().download(filename='highlight_vid')
                        # st.video('highlight_vid.mp4')
                        # os.remove('highlight_vid.mp4')

                    except IndexError:
                        continue

    st.subheader("No highlights:")
    st.markdown(no_highlights + "</center>", unsafe_allow_html=True)


def build_client():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_key = 'AIzaSyDRywzvTHTBs4j6cSOMFo0uWr9zn7W7bh4'
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "/Users/iainmuir/PycharmProjects/Desktop/streamlitApp/sportsHighlights/client_secrets.json"
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


def run():
    """

    TODO Better Method for Determining Year
    """
    global date, year

    date = datetime.today() - timedelta(days=1)
    year = date.year if date.month > 3 else date.year - 1

    st.markdown("<center><img src='https://i.postimg.cc/WbYzfHvd/morningscoop.jpg' alt='Image' width='200'></center>",
                unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Morning Scoop</h1>", unsafe_allow_html=True)
    date_container = st.beta_container()

    with st.beta_expander('Advanced Settings'):
        settings1, settings2 = st.beta_columns(2)
        input_ = settings1.date_input("Enter Date:",
                                      min_value=datetime.today() - timedelta(days=365),
                                      max_value=datetime.today() - timedelta(days=1))
        if input_ != datetime.today().date():
            date = datetime.combine(input_, datetime.min.time())

    date_container.markdown("<h3 style='text-align: center;'> Highlights from: " +
                            date.date().strftime('%B %d, %Y') + "</h1>", unsafe_allow_html=True)

    # col1, col2 = st.beta_columns(2)
    # custom = col1.checkbox('Enter Custom Date')
    # if custom:
    #     input_ = col2.date_input("Enter Date:",
    #                              min_value=datetime.today() - timedelta(days=365),
    #                              max_value=datetime.today() - timedelta(days=1))
    #     date = datetime.combine(input_, datetime.min.time())
    #     # TODO Date Container

    if not os.path.exists('sportsHighlights/data_src/highlights_' + str(date.date()) + '.csv'):
        d = loop_data(RESPONSE.values[0]).dropna().set_index('league')
        d.to_csv('sportsHighlights/data_src/highlights_' + str(date.date()) + '.csv')
        # h = pd.DataFrame.from_dict(h, orient='index', columns=['league', 'any'])
    else:
        d = pd.read_csv('sportsHighlights/data_src/highlights_' + str(date.date()) + '.csv')

    if d is not None:
        display(d)
    else:
        print('Data passed incorrectly')
        exit(code=0)


if __name__ == '__main__':
    run()
