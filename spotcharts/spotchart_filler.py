#!/usr/bin/env python

import sys
import datetime
import billboard
import inflect
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
#from fuzzywuzzy import fuzz
from pymongo import MongoClient

def addChartToDB(chartdb, songsdb, chart):
    # Check to see if we've gotten this one already
    if(chartdb[chart.name].find_one({"date": chart.date}) != None):
        print("Already grabbed " + chart.name + " for " + chart.date)
    else:
        # Go song searching
        print("Grabbing " + chart.name + " for " + chart.date)
        chartsongs = []
        
        for song in chart.entries:          
            # Do we have the song already?
            songmatch = songsdb["songs"].find_one({"title": song.title, "artist": song.artist})

            if(songmatch != None):
                print("  Song \"" + song.title + "\" by \"" + song.artist + "\" is already in the database")
                songid = songmatch["_id"]
            else:
                print("  Creating song \"" + song.title + "\" by \"" + song.artist + "\"")
                songentry = {"title": song.title, "artist": song.artist, "spotify": "@EMPTY"}
                songsdb["songs"].insert(songentry)
                songid = songsdb["songs"].find_one({"title": song.title, "artist": song.artist})["_id"]
            
            chartsongs.append(songid)
        
        chartentry = {"date": chart.date, "list": chartsongs}
        chartdb[chart.name].insert(chartentry)
      
        print("  Grabbed " + chart.name + " for " + chart.date)

  
# Main is below

# Connect to the chart's database
dbcontrol = MongoClient()

chartdb = dbcontrol["charts"]
songsdb = dbcontrol["songs"]

# Load up the persistent entry
persistent = chartdb["persistent"].find_one({"chart": "hot-100"})

if(persistent == None):
    print("Creating persistent file for chart \"" + "hot-100" + "\".")
    newpers = {"chart": "hot-100", "date": "2019-01-24"}
    chartdb["persistent"].insert(newpers)
        

# Get all the chart info...
entry = billboard.ChartData('hot-100', chartdb["persistent"].find_one({"chart": "hot-100"})["date"], timeout=None)

while(entry.previousDate != None):
    addChartToDB(chartdb, songsdb, entry)
    chartdb["persistent"].update_one({"chart": "hot-100"}, {"$set": {"date": entry.date}}, upsert=False)
    entry = billboard.ChartData('hot-100', entry.previousDate)
  
# Clean up and close the database

