#!/usr/bin/env python

import sys
import datetime
import config
import billboard
import inflect
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyClientCredentials

def inputYesNo(prompt):
    result = False
    
    answer = raw_input(prompt + " [y/n] ")
    acceptedYes = ["Y", "YE", "YES"]
    
    if(answer.upper() in acceptedYes): result = True
    
    return result;
    
def stringCompareWithin(str1, str2):
    if(len(str1) > len(str2)):
        if str2 not in str1:
            return 0
        else:
            return 1
    else:
        if str1 not in str2:
            return 0
        else:
            return 1

def lookupSong(spotify, title, artist):
    # Spotify doesn't like ampersands
    queryTitle = title
    queryTitle = queryTitle.replace('&', 'and')
    queryArtist = artist
    
    print("Querying track \"" + queryTitle + "\" by artist \"" + queryArtist + "\"")
    
    # Return structure
    found = {"id": "", "titleScore": -1, "artistScore": -1}
    
    # List what searches we're gonna try - start with only the first word of the artist's name
    queries = []
    queries.append([queryTitle, queryArtist, queryTitle + ' ' + queryArtist.split(' ', 1)[0]])
    
    # If the artist name is longer than one word, use two - this avoids searching for "The"
    if(len(queryArtist.split(' ', 1)) > 1):
        queries.append([queryTitle, queryArtist, queryTitle + ' ' + queryArtist.split(' ', 1)[0] + ' ' + queryArtist.split(' ', 1)[1]])
    
    # Also append one version without replaced ampersands, on the off chance the title includes one (looking at you Sir Sly)    
    queries.append([title, queryArtist, title + ' ' + queryArtist.split(' ', 1)[0]])
    
    for query in queries:
        # Search the spot
        qresult = spotify.search(q=query[2], limit=10, type='track')
        
        # See if we got any direct hits
        for i in range(0, len(qresult['tracks']['items'])):
            qTitle = qresult['tracks']['items'][i]['name']
            
            # Sometimes artist order is broken, so look at every artist Spotify gives us
            for qArtist in qresult['tracks']['items'][i]['artists']:
                if (stringCompareWithin(query[0].upper(), qTitle.upper()) 
                and stringCompareWithin(query[1].upper(), qArtist["name"].upper())):
                    print("  Found direct match (title \"" + qTitle + "\", artist \"" + qArtist["name"] + "\")")
                    found["id"] = qresult['tracks']['items'][i]['id']
                    return found
                  
    # If we got here, there were no complete matches, so do a fuzzy lookup  
    highTitle = 0
    highArtist = 0
        
    for query in queries:
        # Search the spot
        qresult = spotify.search(q=query[2], limit=10, type='track')
        
        # Fuzzi
        for i in range(0, len(qresult['tracks']['items'])):
            qTitle = qresult['tracks']['items'][i]['name']
            
            # Sometimes artist order is broken, so look at every artist Spotify gives us
            for qArtist in qresult['tracks']['items'][i]['artists']:
                scoreTitle =  fuzz.ratio(query[0].upper(), qTitle.upper())
                if(scoreTitle > highTitle): highTitle = scoreTitle
                
                scoreArtist = fuzz.ratio(query[1].upper(), qArtist["name"].upper())
                if(scoreArtist > highArtist): highArtist = scoreArtist
                
                if(scoreTitle > 60 and scoreArtist > 60):
                    print("  Found fuzzy match (title \"" + qTitle + "\", artist \"" + qArtist["name"] + "\", thresh 60:60)")
                    found["id"] = qresult['tracks']['items'][i]['id']
                    found["titleScore"] = scoreTitle
                    found["artistScore"] = scoreArtist
                    return found
                    
    # If we're here, then there were no good matches and we should reflect that
    print("  Did not find track (score " + str(highTitle) + ":" + str(highArtist) + ")")
    for pmatch in qresult['tracks']['items']:
        print("    Possible match: \"" + pmatch["name"] + "\" by \"" + pmatch["artists"][0]["name"] + "\"")

    found["titleScore"] = highTitle
    found["artistScore"] = highArtist
    return found



# All the charts we're gonna support (listed in order of display name, chart URL, short name)
chartsData = []
chartsData.append(['Hot 100', 'hot-100', 'Hot 100'])
chartsData.append(['Billboard 200', 'billboard-200', 'Bill 200'])
chartsData.append(['Mainstream Top 40', 'pop-songs', 'Pop'])
chartsData.append(['Adult Contemporary', 'adult-contemporary', 'Adult Cntmp'])
chartsData.append(['Adult Top 40', 'adult-pop-songs', 'Adult Pop'])
chartsData.append(['Hot Country Songs', 'country-songs', 'Country'])
chartsData.append(['Hot Rock Songs', 'rock-songs', 'Rock'])
chartsData.append(['Alternative Songs', 'alternative-songs', 'Alt'])
chartsData.append(['Triple-A', 'triple-a', 'Tri-A'])
chartsData.append(['Mainstream Rock', 'hot-mainstream-rock-tracks', 'Main Rock'])
chartsData.append(['Hot R&B/Hip-Hop Songs', 'r-b-hip-hop-songs', 'Hip-Hop'])
chartsData.append(['Hot R&B Songs', 'r-and-b-songs', 'R&B'])
chartsData.append(['Hot Rap Songs', 'rap-song', 'Rap'])
chartsData.append(['Adult R&B', 'hot-adult-r-and-b-airplay', 'Adult R&B'])
chartsData.append(['Hot Dance/Electronic Songs', 'dance-electronic-songs', 'EDM'])

print("   _____  _                   _    ____          _   ")
print("  / ____|| |                 | |  |  _ \        | |  ")
print(" | |     | |__    __ _  _ __ | |_ | |_) |  ___  | |_ ")
print(" | |     | '_ \  / _` || '__|| __||  _ <  / _ \ | __|")
print(" | |____ | | | || (_| || |   | |_ | |_) || (_) || |_ ")
print("  \_____||_| |_| \__,_||_|    \__||____/  \___/  \__|")
print(" ")

srcUser = config.username

if(srcUser == ""):
    srcUser = raw_input("Enter your Spotify username: ")
    
print("Now logging you in. Follow the instructions below...")
                                                 
spotToken = util.prompt_for_user_token(srcUser, 'playlist-modify-private playlist-read-private',
                                       client_id=config.client_id,
                                       client_secret=config.client_secret,
                                       redirect_uri='https://example.com/callback/')
        
print("")
print("Available charts:")

for l in range(0, len(chartsData)):
    print(str(l) + ": " + chartsData[l][0])
    
srcChart = ""
selection = 0;

while(srcChart == ""):
    inputSelection = raw_input("Selection [Hot 100]: ")
    if(inputSelection == ""):
        srcChart = chartsData[0][1]
    else:
        selection = int(inputSelection)
        if(selection >= 0 and selection < len(chartsData)):
            srcChart = chartsData[selection][1]

print("")

srcDate = datetime.datetime.now().strftime("%Y-%m-%d")
inputDate = raw_input("Enter the latest week you want chart info for (in YYYY-MM-DD format) [This week]: ")
if(inputDate != ""): srcDate = inputDate

srcRange = 1
inputRange = raw_input("Enter the previous weeks you want to include [1]: ")
if(inputRange != ""): srcRange = inputRange

srcPlaylist = "ChartBot: " + chartsData[selection][2] + " for " + srcDate
inputPlaylist = raw_input("Enter the name for the new playlist [" + srcPlaylist + "]: ")
if(inputPlaylist != ""): srcPlaylist = inputPlaylist

# Get master chart data
print("")
print("Fetching chart data...")

chart = billboard.ChartData(srcChart, srcDate)
tracksToFind = []

for c in chart:
    tracksToFind.append(c)
    
for w in range(0, srcRange-1):
    chart = billboard.ChartData(srcChart, chart.previousDate)
    
    for c in chart:
        # O god forgive me
        found = 0
        
        for ck in tracksToFind:
            if(c.title == ck.title and c.artist == ck.artist):
                found = 1
    
        if(found == 0):
            tracksToFind.append(c)
        
        found = 0

print('Tracks to be added:')

for t in tracksToFind:
    print("  "),
    print(t)
    
print('Total: %d tracks' % len(tracksToFind))

# Login to Spotify

print(' ')

spotify = spotipy.Spotify(auth=spotToken)

tracksToAdd = []
tracksRejected = []

# Loop through each track and get the Spotify ID
for chartTrack in tracksToFind:
    found = lookupSong(spotify, chartTrack.title, chartTrack.artist)
    
    if(found["id"] != ""):
        tracksToAdd.append(found["id"])
    else:
        tracksRejected.append(chartTrack)
        
    print(" ")
    
print('Found ' + str(len(tracksToAdd)) + ' of ' + str(len(tracksToFind)) + ' tracks.')

if(len(tracksRejected) > 0):
    print('Not found:')

    for t in tracksRejected:
        print(t)

print(' ')

# Add tracks to the playlist
if(inputYesNo("Build this playlist?")):
    newPlaylist = spotify.user_playlist_create(srcUser, name=srcPlaylist, public=False)
    spotify.user_playlist_add_tracks(srcUser, newPlaylist['id'], tracksToAdd)

    print('Made new playlist \"%s\"' % srcPlaylist)














