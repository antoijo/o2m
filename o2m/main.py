import logging, subprocess, os, spotipy, json

from mopidyapi import MopidyAPI
from src import util
from src.o2mtomopidy import O2mToMopidy
from src.spotifyhandler import SpotifyHandler
from time import sleep

from flask import Flask, request, session, redirect
from flask_session import Session
from flask_cors import CORS

"""
    TODO :
        * Logs : séparer les logs par ensemble de fonctionnalités (database, websockets, spotify etc...)
        * Timestamps sur les boxs
    Pas très clean de mettre les fonction de callback aux évènements dans le main 
    Mais on a besoin de l'instance de mopidyApi et la fonction callback à besoin de l'instance o2mHandler pour lancer les recos...

    Piste : Ajouter encore une classe mère pour remplacer le main?
"""

START_BOLD = "\033[1m"
END_BOLD = "\033[0m"

if __name__ == "__main__":

#CONFS AND CONSTS

    #Launch Connectors and modules
    o2mConf = util.get_config_file("o2m.conf")  # o2m
    #mopidyConf = util.get_config_file("mopidy.conf")  # mopidy
    mopidyConf = ""
    def create_api():
        #FLASK INIT
        api = Flask(__name__)
        CORS(api)
        api.config['SECRET_KEY'] = os.urandom(64)
        api.config['SESSION_TYPE'] = 'filesystem'
        api.config['SESSION_FILE_DIR'] = './.flask_session/'
        Session(api)
        return api

    api=create_api()
    api.app_context().push()

    while True:
        strer = 1
        try:
            #mopidy = MopidyAPI(host='mopidy', port=6680)
            mopidy = MopidyAPI(host=o2mConf["o2m"]["host_mopidy"], port=o2mConf["o2m"]["port_mopidy"])
            #mopidy = MopidyAPI(host='51.15.205.150', port='6680')
            #mopidy = MopidyAPI()
            o2mHandler = O2mToMopidy(mopidy, o2mConf, mopidyConf, logging)
            strer = 0
        except Exception as err_value:
            strer = 1
            print (err_value)

        if strer != 0:
            sleep(10)  # wait for 10 seconds before trying to fetch the data again
        else:
            break

    
#API DEF AND LISTENER (to be move in a dedicated part)
    #API BOX ACTION (mode : toogle, add, remove) AND SHOW
    def api_box_action(uid='',option_type='',mode='toogle'):
        if uid!='':
            box = o2mHandler.dbHandler.get_box_by_uid(uid)
        if option_type!='':
            box = o2mHandler.dbHandler.get_box_by_option_type(option_type)
        #print (f"ACTIVE TAGS : {o2mHandler.activeboxs}")
        
        #Active Toogle  Add     Remove
        #yes     Remove  Not     Remove  
        #no      Add     Add     Not
        
        if box != None:
            action = 'No'
            #PRESENT
            if box in o2mHandler.activeboxs: 
                if mode == 'toogle' or mode == 'remove': action = 'remove'
            #ABSENT
            else:
                if mode == 'toogle' or mode == 'add': action = 'add'

            if action == 'remove':
                try: 
                    removedBox = next((x for x in o2mHandler.activeboxs if x.uid == box.uid), None)
                    print(f"removed box {removedBox}")
                    o2mHandler.activeboxs.remove(box)
                    o2mHandler.box_action_remove(box,removedBox)
                    return "TAG removed"
                except Exception as val_e: 
                    print(f"Erreur : {val_e}")
                    return(val_e)

            if action == 'add':
                try:
                    o2mHandler.activeboxs.append(box)  #adding box to list
                    print(f"added box {box}") 
                    o2mHandler.box_action(box)
                    #box.add_count()  # Incrémente le compteur de contacts pour ce box
                    return "TAG added"
                except Exception as val_e: 
                    print(f"Erreur : {val_e}")
                    return(val_e)
            
            if action == 'No':
                return ("No action")
                
        else: return "no TAG"

    @api.route('/api/box')
    def api_box():
        uid = request.args.get('uid')
        mode = request.args.get('mode')
        option_type = request.args.get('option_type')
        if uid==None: uid=''
        if option_type==None: option_type=''
        if mode==None: mode='toogle'
        return api_box_action(uid,option_type,mode)

    #Return list of favorite boxes
    @api.route('/api/box_favorites')
    def api_box_favorites():
        boxes = o2mHandler.dbHandler.get_boxes_pinned()
        #boxes = json.dumps(boxes)
        return (boxes)

    #API box checking if activated or not
    @api.route('/api/box_activated')
    def api_box_activated():
        uid = request.args.get('uid')
        box = o2mHandler.dbHandler.get_box_by_uid(uid)
        if box != None:
            if box in o2mHandler.activeboxs: return("1")
            else: return("0")

    #API Opening Level
    #Get the value
    @api.route('/api/dl')
    def api_dl():
        if o2mHandler.discover_level != None:
            return str(o2mHandler.discover_level)
        else:
            return "No Opening Level"

    #Activate and apply a new value
    @api.route('/api/dl_on')
    def api_dl_on():
        dl = request.args.get('dl')
        if dl != None:
            o2mHandler.discover_level = int(dl)
            o2mHandler.discover_level_on = True

            #Should we relaunch when dl is changed?
            state = o2mHandler.mopidyHandler.playback.get_state()
            relaunch = False
            if state == "stopped": relaunch = True
            else:
                for box in o2mHandler.activeboxs:
                    if "auto" in box.data: relaunch = True
                    elif "m3u" in box.data:
                        contents = o2mHandler.mopidyHandler.playlists.lookup(box.data) 
                        for track in contents.tracks:
                            if "auto" in track.uri: relaunch = True
            if relaunch == True:
                #relaunching with the actual boxes
                if len(o2mHandler.activeboxs)>0:
                    o2mHandler.starting_mode(True,True)
                #relaunching with default_box if exists
                elif o2mHandler.default_box != None:
                    o2mHandler.starting_mode(True,True,o2mHandler.default_box)
            return "New dl"
        else:
            return "No new dl"
    
    #API TRACK STATUS
    #Get the value from tlid or uri in list
    @api.route('/api/track_status')
    def api_track_status():
        uri = request.args.get('uri')
        try: 
            stat = o2mHandler.dbHandler.get_stat_by_uri(uri)
            option_type = str(stat.option_type)
            read_end = float(stat.read_end)
            status = option_type + " - " + str(int(round(read_end,1)*10))
        except Exception as val_e:
            status = 'new'
        return status

        #tlid = int(request.args.get('tlid'))
        #tracks = o2mHandler.mopidyHandler.tracklist.filter({'tlid':[tlid]})
        #tracks = o2mHandler.mopidyHandler.tracklist.slice(tlid,tlid+1)
        '''if tracks != None:
            print (tracks)
            uri = tracks[0].track['uri']
            stat = o2mHandler.dbHandler.get_stat_by_uri(uri)
            return stat['option_type']
        else:
            return "no track"'''

    #RESTART
    @api.route('/api/toogle_play')
    def api_toogle_play():
        o2mHandler.play_or_resume()
        return ("play !")
    
    @api.route('/api/reset_o2m')
    def api_reset_o2m():
        o2mHandler.starting_mode(True,True)
        return ("reset")

    @api.route('/api/restart_o2m')
    def api_restart_o2m():
        p = subprocess.run("start_o2m.sh", shell=True, check=True)
        return ("reset")

    @api.route('/api/restart_mopidy')
    def api_restart_mopidy():
        p = subprocess.run("start_mopidy.sh", shell=True, check=True)
        return ("reset")

    #SPOTIPY
    if o2mHandler.spotifyHandler.spotipy_config:
        @api.route('/api/spotipy_check')
        def api_spotipy_check():
            cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=o2mHandler.spotifyHandler.cache_path)        
            auth_manager = spotipy.oauth2.SpotifyOAuth(scope=o2mHandler.spotifyHandler.scope,cache_handler=cache_handler,show_dialog=True)
            if not auth_manager.validate_token(cache_handler.get_cached_token()):
                return ("spotipy_init")
            else:
                return ("spotipy_out")

        @api.route('/api/spotipy_init')
        def api_spotipy_init():
            cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=o2mHandler.spotifyHandler.cache_path)        
            auth_manager = spotipy.oauth2.SpotifyOAuth(scope=o2mHandler.spotifyHandler.scope,cache_handler=cache_handler,show_dialog=True)

            if request.args.get("code"):
                # Step 2. Being redirected from Spotify auth page
                auth_manager.get_access_token(request.args.get("code"))
                o2mHandler.spotifyHandler.sp = spotipy.Spotify(auth_manager=auth_manager)
                return redirect('/api/spotipy_init')

            if not auth_manager.validate_token(cache_handler.get_cached_token()):
                # Step 1. Display sign in link when no token
                auth_url = auth_manager.get_authorize_url()
                return f'<h2><a href="{auth_url}">Sign in</a></h2>'

            # Step 3. Signed in, display data
            o2mHandler.spotifyHandler.sp = spotipy.Spotify(auth_manager=auth_manager)
            return f'<h2>Hi {o2mHandler.spotifyHandler.sp.me()["display_name"]}, ' \
            f'<small><a href="/api/spotipy_out">[sign out]<a/></small></h2>' \

        @api.route('/api/spotipy_out')
        def api_spotipy_out():
            #Delete cache file
            if os.path.exists(o2mHandler.spotifyHandler.cache_path):
                os.remove(o2mHandler.spotifyHandler.cache_path)
                print("File deleted successfully.")
            else:
                print("File does not exist.")
            return redirect('/api/spotipy_init')
    
    #MOPIDY LISTENERS
        # Fonction called when track started
        @mopidy.on_event("track_playback_started")
        #@mopidy.audio.AudioListener.state_changed("PAUSED","PLAYING",None)
        def track_started_event(event):
            track = event.tl_track.track
            print (event)

            #Quick and dirty volume Management
            # Podcast : seek previous position
            if ("podcast+" in track.uri and ("#" in track.uri or "episode" in track.uri) ) or ("youtube:video:" in track.uri) or ("yt:" in track.uri):
                stat_uri = o2mHandler.dbHandler.get_stat_by_uri(track.uri)
                if (stat_uri):
                    #if (o2mHandler.dbHandler.get_pos_stat(track.uri) > 0) and (o2mHandler.dbHandler.get_pos_stat(track.uri)/track.length < 0.9) :
                    if (stat_uri.read_position > 0) and (stat_uri.read_end < 0.9) :
                        o2mHandler.mopidyHandler.playback.seek(max(stat_uri.read_position - 10, 0))
                    #skip advertising on sismique
                    elif "9851446c-d9b9-47a2-99a9-26d0a4968cc3" in track.uri: o2mHandler.mopidyHandler.playback.seek(63000)
                elif "9851446c-d9b9-47a2-99a9-26d0a4968cc3" in track.uri:  o2mHandler.mopidyHandler.playback.seek(63000)
            if "radiofrance-podcast.net" in track.uri :
                volume = o2mHandler.mopidyHandler.mixer.get_volume()*1.5
                if volume > 100: volume = 100
                o2mHandler.mopidyHandler.mixer.set_volume(int(volume))

        # Fonction called when tracked skipped OR completly finished
        #@mopidy.audio.AudioListener.state_changed("PLAYING","PAUSED",None)
        #@mopidy.audio.AudioListener.reached_end_of_stream()   

        def track_ended_event(event):
            #Datas
            track = event.tl_track.track
            
            #Box = active_box in memory linked to this uri. Pb if track in many boxes
            active_box = o2mHandler.get_active_box_by_uri(track.uri)
            option_type = 'new_mopidy'
            library_link = ''
            data = ''
            position = event.time_position
            
            #Update Dynamic datas linked to Box object and stats (LIBRARY_LINK, etc)
            if active_box:
                if active_box.data != '': data = active_box.data

                if active_box.option_type != 'new':
                    if hasattr(active_box, "option_types") and hasattr(active_box, "tlids"):
                        try: option_type = active_box.option_types[active_box.tlids.index(event.tl_track.tlid)]
                        except Exception as val_e: print(f"Error end_track : {val_e}")
                    if hasattr(active_box, "library_link") and hasattr(active_box, "tlids"):
                        try: library_link = active_box.library_link[active_box.tlids.index(event.tl_track.tlid)]
                        except Exception as val_e: print(f"Erreur : {val_e}")
                    #Try / except here to check if dynamic playlist computing is not in competition with first playback finishing...
                    if library_link == '': 
                        #library_link = active_box.data
                        #Playlist exctraction : search correspondancy Playlists between my Mopidy Playlists X Active_Box Data 
                        playlist = o2mHandler.mopidyHandler.playlists.lookup(active_box.data)
                        data = active_box.data.split("\n")
                        data = [x for x in data if not x.startswith('#')]
                        data = [x for x in data if not x.startswith('\r')]
                        #Loop on lines containing the playlist uris
                        for content in data:
                            #Taking the first one. Pb if manies ?
                            if 'spotify:playlist' in content: 
                                library_link = content
                                break
                    print(f"Library Link : {library_link}")

            if event.event == "track_playback_ended":
                #Quick and dirty volume Management
                if "radiofrance-podcast.net" in track.uri or "9851446c-d9b9-47a2-99a9-26d0a4968cc3" in track.uri :
                    print (f"Set Volume : {o2mHandler.current_volume}")
                    #o2mHandler.mopidyHandler.mixer.set_volume(o2mHandler.current_volume)
                    o2mHandler.mopidyHandler.mixer.set_volume(int(o2mHandler.mopidyHandler.mixer.get_volume()*0.67))

                # Recommandations added at each ended and nottrack (only spotify:track now)
                if "track" in track.uri and position / track.length > 0.9:
                    print (f"Ending with option_type {option_type}")
                    if option_type != 'new': 
                        #int(round(discover_level * 0.25))
                        #Pb with this library_link calc
                        library_link="o2m:reco_after_track"
                        try: o2mHandler.add_reco_after_track_read(track.uri,library_link,data)
                        except Exception as val_e:
                            print(f"Erreur : {val_e}")
                            o2mHandler.spotifyHandler.init_token_sp()
                            o2mHandler.add_reco_after_track_read(track.uri,library_link,data)
                    if option_type != 'hidden' and option_type != 'trash' : 
                        print ("Adding raw stats")
                        o2mHandler.update_stat_raw(track.uri)

            # Podcast
            '''if ("podcast+" in track.uri and ("#" in track.uri or "episode" in track.uri) ) or ("youtube:video:" in track.uri) or ("yt:" in track.uri):

                #URI harmonization if max_results used : pb to update track.uri
                if "?max_results=" in track.uri: 
                    uri1 = track.uri.split("?max_results=")
                    if "#" in uri1[1]: 
                        uri2 = uri1[1].split("#")
                        track_uri = str(uri1[0]) + "#" + str(uri2[1])
                    else : track_uri = str(uri1[0])
                if o2mHandler.dbHandler.stat_exists(track.uri):
                    stat = o2mHandler.dbHandler.get_stat_by_uri(track.uri)
                    #If last stat read position is greater than actual: do not update
                    #if position < stat.read_position: position = stat.read_position
                    print(f"Event : {position} / stat : {stat.read_position}")
                # If directly in box data (not m3u) : behaviour to ckeck
                if (position / track.length > 0.7): 
                    active_box = o2mHandler.dbHandler.get_box_by_data(track.uri)  # To check !!! Récupère le active_box correspondant à la chaine
                    if active_box != None:
                        if active_box.box_type == "podcasts:channel":
                            active_box.option_last_unread = (track.track_no)  # actualise le numéro du dernier podcast écouté
                            active_box.update()
                            active_box.save()
            '''
                            
            print(f"\n{event.event} song : {track.name} with option_type {option_type} and library_link {library_link}")

            # Update stats 
            if (event.event == "track_playback_ended") or ("podcast+" in track.uri and ("#" or "episode") in track.uri) or ("youtube:video:" in track.uri) or ("yt:" in track.uri):
                
                try: 
                    o2mHandler.update_stat_track(track,position,option_type,library_link)
                except Exception as val_e: 
                    print(f"Erreur : {val_e}")
                    o2mHandler.spotifyHandler.init_token_sp() #pb of expired token to resolve
                    o2mHandler.update_stat_track(track,position,option_type,library_link)
                
            if "tunein" in track.uri:
                if option_type != 'hidden': o2mHandler.update_stat_raw(track.uri)

            # Tracklist filling when empty
            tracklist_length = mopidy.tracklist.get_length()
            tracklist_index = mopidy.tracklist.index()
            if tracklist_index != None and tracklist_length != 0:
                index = tracklist_index + 1
                tracks_left_count = (
                    tracklist_length - index
                )  # Nombre de chansons restante dans la tracklist
                if tracks_left_count < 1:
                    o2mHandler.update_tracks()  # si besoin on ajoute des chansons à la tracklist avec de la reco

        @mopidy.on_event("track_playback_ended")
        def event_track_playback_ended(event):
            track_ended_event(event)

        @mopidy.on_event("track_playback_paused")
        def event_track_playback_paused(event):
            track_ended_event(event)

    # Fonction called when status change ie : stop but impossible to catch track before
    """@mopidy.on_event('playback_state_changed')
    def event_print(event):
        #possibility of track catching ?
        if event.new_state == 'stopped': print (f"Stop : {o2mHandler.mopidyHandler.playback.get_current_track()}")"""


#MAIN LOOP
    # Infinite loop for API listener
    try:
        api.run(host='0.0.0.0', port=6681)
    except Exception as ex:
        print(f"Erreur : {ex}")
        o2mHandler.spotifyHandler.init_token_sp()
        api.run(host='0.0.0.0', port=6681)

# Code pour créer manuellement des boxs en bdd
# if __name__ == "__main__":
#     mydb = DatabaseHandler()
#     box = mydb.get_box_by_uid('AB34A324')
#     box.description = 'Spotify Artist : Creedence'
#     box.save()
#     # box = Box.create('AB34A324')
#     #     uid='AB34A324',
#     #     box_type = 'spotify:artist',
#     #     data = 'spotify:artist:3IYUhFvPQItj6xySrBmZkd',
#     #     descrition = 'Spotify Artist : Creedence')
#     print(box)