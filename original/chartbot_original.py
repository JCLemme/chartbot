import sys
import datetime
import config

import billboard

import inflect

import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util

from fuzzywuzzy import fuzz

def compareData(str1, str2):
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

def findSong(spotify, trackInfo, guess):
    trackResult = spotify.search(q=trackInfo[2], limit=10, type='track')
    
    for i in range(0, len(trackResult['tracks']['items'])):
        songFound = trackResult['tracks']['items'][i]['name']
        
        artistFound = trackResult['tracks']['items'][i]['artists'][0]['name']
        
        print("  found \"%s\" by %s" %(songFound, artistFound))
        
        if(guess):
            songScore = fuzz.ratio(trackInfo[0].upper(), songFound.upper())
            artistScore = fuzz.ratio(trackInfo[1].upper(), artistFound.upper())
            if(songScore > 60 and artistScore > 60):
                print("  Using above (fuzzy score %d, %d)" %(songScore, artistScore))
                return trackResult['tracks']['items'][i]['id']
        else:
            if(compareData(trackInfo[0].upper(), songFound.upper()) 
            and compareData(trackInfo[1].upper(), artistFound.upper())):
                print("  Using above")
                return trackResult['tracks']['items'][i]['id']
        
    return 0
    

# All the charts we're gonna support
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
inputDate = raw_input("Enter the latest week you want chart info for [This week]: ")
if(inputDate != ""): srcDate = inputDate

srcRange = 1
inputRange = input("Enter the previous weeks you want to include [1]: ")
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
    songSearch = chartTrack.title
    songSearch = songSearch.replace('&', 'and')
    
    artistSearch = chartTrack.artist
    
    print('looking for track \"%s\" by %s' % (songSearch, artistSearch))
    
    searchCombos = []
    searchCombos.append([songSearch, artistSearch, songSearch + ' ' + artistSearch.split(' ', 1)[0]])
    if(len(artistSearch.split(' ', 1)) > 1):
        searchCombos.append([songSearch, artistSearch, songSearch + ' ' + artistSearch.split(' ', 1)[0] + ' ' + artistSearch.split(' ', 1)[1]])
    
    found = False
    
    for combo in searchCombos:
        foundID = findSong(spotify, combo, False)
        
        if(foundID != 0):
            tracksToAdd.append(foundID)
            found = True
            break;
            
    if(found == False):
        for combo in searchCombos:
            foundID = findSong(spotify, combo, True)
            
            if(foundID != 0):
                tracksToAdd.append(foundID)
                found = True
                break;
            
    if(found == False):
        tracksRejected.append(chartTrack)
        
    print(" ")
    
print('Found ' + str(len(tracksToAdd)) + ' of ' + str(len(tracksToFind)) + ' tracks.')
print('Not found:')

for t in tracksRejected:
    print(t)

print(' ')

# Add tracks to the playlist
newPlaylist = spotify.user_playlist_create(srcUser, name=srcPlaylist, public=False)
spotify.user_playlist_add_tracks(srcUser, newPlaylist['id'], tracksToAdd)

print('Made new playlist \"%s\"' % srcPlaylist)





