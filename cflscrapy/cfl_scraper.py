import time
import requests
import re

import numpy as np

from bs4 import BeautifulSoup
from tqdm import tqdm


def soup_setup(url):

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    return soup


def get_links(start, end):
    soups = [soup_setup(
        f'https://www.cfl.ca/schedule/{i}/') for i in range(start, end+1) if i != 2020]
    game_links = []
    for i in soups:
        one_season = i.findAll('div', {'class': 'action'})
        for j in one_season:
            # print(j.contents[1])
            one_game = j.contents[1]['data-url']
            game_links.append(one_game)

    return game_links


def get_pbp(link):
    game_id = link[25:29]
    game = requests.get(
        f"https://www.cfl.ca/wp-content/themes/cfl.ca/inc/admin-ajax.php?action=gametracker&scoreboardTemplate=1&eventId={game_id}&active_tab=playbyplay&template=1").json()

    game_date = game['scoreboard']['startDate'].split('T')[0]
    team0 = game['playbyplay']['teams'][0]
    team1 = game['playbyplay']['teams'][1]
    game_id = f"{game['scoreboard']['startDate'].split('T')[0].replace('-','')}_{team0['abbreviation']}_{team1['abbreviation']}"
    pbp = game['playbyplay']['plays']

    for i in pbp:
        i['game_date'] = game_date
        i['game_id'] = game_id
        i['posteam'] = f"{team0['location']} {team0['nickname']}" if i['startPossession'][
            'teamId'] == team0['teamId'] else f"{team1['location']} {team1['nickname']}"
        i['defteam'] = f"{team0['location']} {team0['nickname']}" if i['startPossession'][
            'teamId'] == team1['teamId'] else f"{team1['location']} {team1['nickname']}"

        if i['field_position_start']:
            if i['field_position_start'][0] == i['posteam'][0]:
                i['yard_line_100'] = int(i['field_position_start'][1:])
            else:
                i['yard_line_100'] = 110 - int(i['field_position_start'][1:])

        if 'No Play' in i['playText']:
            i['aborted_play'] = 1

        else:
            if i['playType']['name'] == 'Rush':
                rusher = re.findall('[A-Z]\.\s.+\sRun', i['playText'])
                if rusher:
                    i['rusher'] = rusher[0].replace(' Run', '')

                    i['rush_yards'] = int(re.findall(
                        '-?\d+\syds', i['playText'])[0].replace(' yds', ''))

                    i['rush_td'] = 1 if 'Touchdown' in i['playText'] else 0

                    i['rush_attempt'] = 1

            elif i['playType']['name'] == 'Pass':
                if 'Incomplete' in i['playText']:
                    i['pass_attempt'] = 1
                    i['passer'] = re.findall(
                        '[A-Z]\.\s.+\sIncomplete', i['playText'])[0].replace(' Incomplete', '')
                    i['pass_yds'] = 0
                    receiver = re.findall(
                        'for\s[A-Z]\.\s.+\sat', i['playText'])
                    if receiver:
                        i['receiver'] = receiver[0].replace(
                            'for ', '').replace(' at', '')
                elif 'Complete' in i['playText']:
                    i['pass_attempt'] = 1
                    i['passer'] = re.findall(
                        '[A-Z]\.\s.+\sComplete', i['playText'])[0].replace(' Complete', '')
                    i['pass_yds'] = int(re.findall(
                        '-?\d+\syds', i['playText'])[0].replace(' yds', ''))
                    yac = re.findall('-?\d+\sYAC', i['playText'])
                    i['yac'] = int(yac[0].replace(
                        ' YAC', '')) if yac else np.nan
                    i['receiver'] = re.findall(
                        'to\s[A-Z]\.\s.+,\scaught', i['playText'])[0].replace('to ', '').replace(', caught', '')
                    i['pass_td'] = 1 if 'Touchdown' in i['playText'] else 0
                elif 'Intercept' in i['playText']:
                    i['pass_attempt'] = 1
                    i['passer'] = re.findall(
                        '[A-Z]\.\s.+\sIntercepted', i['playText'])[0].replace(' Intercepted', '')
                    i['pass_yds'] = 0
                    i['interception'] = 1

            elif i['playType']['name'] == 'Kickoff':
                returner = re.findall('by\s[A-Z]\.\s.+\sfrom', i['playText'])
                if returner:
                    i['kick_returner'] = returner[0].replace(
                        'by ', '').replace(' from', '')

                    i['kick_return_yds'] = int(re.findall(
                        '-?\d+\syds', i['playText'])[1].replace(' yds', ''))

                    i['kick_return_td'] = 1 if 'Touchdown' in i['playText'] else 0

            elif i['playType']['name'] == 'Punt':
                returner = re.findall('by\s[A-Z]\.\s.+\sfrom', i['playText'])
                if returner:
                    i['punt_returner'] = returner[0].replace(
                        'by ', '').replace(' from', '')

                    i['punt_return_yds'] = int(re.findall(
                        '-?\d+\syds', i['playText'])[1].replace(' yds', ''))

                    i['punt_return_td'] = 1 if 'Touchdown' in i['playText'] else 0

            i['fumble'] = 1 if 'Fumble forced' in i['playText'] else 0
            i['fumble_lost'] = 1 if (i['fumble'] == 1) & (
                'Lost' in i['playText']) else 0

    return pbp


def get_all_pbp(start, end):
    links = get_links(start, end)

    all_pbp = []
    for i in tqdm(links):
        time.sleep(0.5)
        try:
            all_pbp.extend(get_pbp(i))
        except:
            print(f"Error scraping {i}")
            break

    return all_pbp
