#!/usr/bin/env python

import sys
import datetime
import billboard
import inflect
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from fuzzywuzzy import fuzz
from pymongo import MongoClient
from spotipy.oauth2 import SpotifyClientCredentials

def strCompareBi(str1, str2):
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
    
    for query in queries:
        # Search the spot
        qresult = spotify.search(q=query[2], limit=10, type='track')
        
        # See if we got any direct hits
        for i in range(0, len(qresult['tracks']['items'])):
            qTitle = qresult['tracks']['items'][i]['name']
            
            # Sometimes artist order is broken, so look at every artist Spotify gives us
            for qArtist in qresult['tracks']['items'][i]['artists']:
                if (strCompareBi(query[0].upper(), qTitle.upper()) 
                and strCompareBi(query[1].upper(), qArtist["name"].upper())):
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


# Login to Spotify
client_credentials_manager = SpotifyClientCredentials("8dbabb05a80a4cecb98335f427df2f38", "e6654e608cae485bb66231acbe7682d4")
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Open databases
dbclient = MongoClient()
songsdb = dbclient["songs"]

# Start tearin up BIATCH
songcursor = songsdb["songs"].find()

for track in songcursor:
    if(track["spotify"] == "@EMPTY"):
        lookupSong(spotify, track["title"], track["artist"])












