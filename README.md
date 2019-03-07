# chartbot
A script that generates Spotify playlists from Billboard charts

---

## What's it do
Chartbot generates Spotify playlists from Billboard charts. Just give it a chart and a date, and twenty seconds later you'll find a shiny new playlist on your account.

Since Billboard and Spotify don't list songs under the same name, Chartbot has to do some guessing. If Chartbot can't find a song, it'll tell you before it makes the playlist. If Chartbot doesn't find a song that is available on Spotify, please open an issue about it.

## How do I use it
1. Go to the [Spotify developer page](https://developer.spotify.com/dashboard/applications) and register a new application.
2. Copy `config_example.py` to `config.py`and fill in your app's ID and secret.
3. Run `./chartbot.py` from a terminal and follow the prompts. 

Chartbot tries its best to cache your login information. If you don't want to enter your username on every launch, you can pop that in the config.py file as well.

I haven't tried running Chartbot on Windows, but I imagine it'll work. Drop me a line if you try it.

## Dependencies
Grab these with pip. Latest version should be fine.

* billboard.py
* spotipy
* fuzzywuzzy
* inflect
