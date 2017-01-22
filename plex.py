#from PMS import *
#from PMS.Objects import *
#from PMS.Shortcuts import *
import os 
from xml.dom.minidom import parseString
import codecs

#from texttime  import prettyduration
#from textbytes  import prettysize

import urllib, urllib2, base64
from unidecode import unidecode

base_url = "http://localhost:32400"

def get_subtitle(_title, year=None ):
    api_url = 'http://api.opensubtitles.org/xml-rpc'

def mk_dir(d):
    os.system("mkdir -p \"" + d + "\"")

def get_xml(path):
    raw = urllib.urlopen(path)  
    xml = parseString(str(raw.read()))
    return xml

def get_video_summary(x):
    info = ""
    info += x.getAttribute("title")  + ", " + x.getAttribute("year") + "\n"
    #_info += _attr("tagline") + "\n"
    info += "IMDB : " + x.getAttribute("rating") + "\n"
    info +=  x.getAttribute("summary")
    return info        

def convert_to_ascii(st):    
    return st.encode("ascii", "ignore").translate(None, "?:")   
    
def dirname_from_title(x):
    if x.getAttribute("year") in x.getAttribute("title"):
	return x.getAttribute("title")
    else:
	return "%s (%d)" %(convert_to_ascii(x.getAttribute("title")), int(x.getAttribute("year")))

def get_video_info(v):
    filename = v.getElementsByTagName("Part")[0].getAttribute("file")
    summary = get_video_summary(v)
    return [filename, summary,  v.getAttribute("thumb")]                    

def get_dir(path, _type):
    sections = get_xml(path + "/library/sections")
    _dir = filter( lambda d : d.getAttribute("type") == _type, sections.getElementsByTagName("Directory"))
    return "%s/library/sections/%d/all" %(path, int(_dir[0].getAttribute("key")))


def get_music(path, src, dst = None):
    xml = get_xml(get_dir(path, "artist"))
    if dst != None : mk_dir(dst) 
    for artist in (a for a in xml.getElementsByTagName("Directory") if a.getAttribute("type") == "artist") :
	artist_name = artist.getAttribute("title") #encode("ascii", "ignore")
        artist_dir = unidecode(os.path.join(dst, artist_name))
        artist_thumb = path + artist.getAttribute("thumb")
        artist_thumb_file = os.path.join(artist_dir, "Artist.jpg")
        artist_info = "%s/n%s" %(artist.getAttribute("title"), artist.getAttribute("summary"))
        albums = get_xml(path + artist.getAttribute("key")).getElementsByTagName("Directory")
        for album in ( s for s in albums if s.getAttribute("type") == "album"):
	    album_dir = unidecode(os.path.join(artist_dir, album.getAttribute("title")))
            album_art = path + album.getAttribute("thumb")
            album_art_file = os.path.join(album_dir, "Album.jpg")
            tracks =  get_xml(base_url + album.getAttribute("key")).getElementsByTagName("Track")
            for track in ( tr for tr in tracks if src in tr.getElementsByTagName("Part")[0].getAttribute("file")):
		print "%s:: %s: %s " %(artist_name,  album.getAttribute("title"), track.getAttribute("title"))
		if dst != None : mk_dir(album_dir)  
                file = track.getElementsByTagName("Part")[0].getAttribute("file")
                track_name = "%s - %s - %s%s" %( track.getAttribute("index"), artist_name,
                                           track.getAttribute("title"), os.path.splitext(file)[1] )
                track_file = unidecode(os.path.join(album_dir, track_name)) #.encode("ascii", "ignore")
                print track_file
                if dst != None : 
                    if (not os.path.exists(artist_thumb_file)):
                        urllib.urlretrieve(artist_thumb, artist_thumb_file)
                    if (not os.path.exists(album_art_file)):
                        urllib.urlretrieve(album_art, album_art_file)
                    #os.system("touch \"%s\"" %(track_file))    
		    os.system("touch \"%s\"" %(os.path.basename(file)))    
                    #os.system("mv -v \"%s\" \"%s\"" %(file, track_file))
                        
                        
          
def tvshows(path, src_dir, dst_dir = None):
    xml = get_xml(get_dir(path, "show"))  
    if dst_dir != None : 
      mk_dir(dst_dir)  
    for show in xml.getElementsByTagName("Directory") :
        show_title = show.getAttribute("title").replace(" (%s)" %show.getAttribute("year"), "")
        show_thumb = base_url + show.getAttribute("thumb")
        show_info = "%s, %s\n%s" %(show_title, show.getAttribute("year"), show.getAttribute("summary"))
        seasons = get_xml(base_url + show.getAttribute("key")).getElementsByTagName("Directory")
        
	if dst_dir != None :
	  dst_series_dir = os.path.join(dst_dir, dirname_from_title(show))
	  dst_series_info_file = os.path.join(dst_series_dir, convert_to_ascii(show_title).replace(" ", ".") + ".info")
	  dst_series_poster_file = os.path.join(dst_series_dir, "poster.jpg")
	  
        
        for season in (s for s in seasons if s.getAttribute("type") == "season"):
            season_indx = season.getAttribute("index") 
            season_poster = base_url + season.getAttribute("thumb")
            episodes =  get_xml(base_url + season.getAttribute("key")).getElementsByTagName("Video")
            
            if dst_dir != None :
	      dst_season_dir = os.path.join(dst_series_dir, season.getAttribute("title"))
	      dst_season_poster_file = os.path.join(dst_season_dir, (convert_to_ascii(show_title) + "."+ season.getAttribute("title")).replace(" ", ".") +".jpg")
       
            for ep in (e for e in episodes if src_dir in e.getElementsByTagName("Part")[0].getAttribute("file")) :
                src_filename = ep.getElementsByTagName("Part")[0].getAttribute("file")
                if not "Episode" in ep.getAttribute("title") : 
		  dst_filename = "%s S%02dE%02d %s" %(show_title, int(season_indx), int(ep.getAttribute("index")), ep.getAttribute("title"))
		  dst_filename = convert_to_ascii(dst_filename) + os.path.splitext(src_filename)[1]
                else:
		  dst_filename = os.path.basename(src_filename)
		#dst_filename = dst_filename.replace(", ", "").replace(". ", "").replace(" ", ".").replace(" ", ".").replace("..", ".")
		
                #print os.path.join(dst_season_dir, ep_name)
                ep_summary = get_video_summary(ep)
                ep_thumb =  ep.getAttribute("thumb")
                ep_info = "\n\nSeason %s Episode %d\n" %(season_indx, int(ep.getAttribute("index"))) 
                ep_info += ep_summary
                """
                if dst_dir != None : 
                    mk_dir(dst_season_dir) 
                    if (not os.path.exists(dst_series_info_file)):                    
                        with codecs.open(dst_series_info_file,  'w', encoding="utf8") as f:
                            f.write(show_info)  
                    else:
                       with codecs.open(dst_series_info_file,  'a', encoding="utf8") as f:
                            f.write(ep_info)                                
                    if (not os.path.exists(dst_series_poster_file)):
                        urllib.urlretrieve(show_thumb, dst_series_poster_file)
                    if (not os.path.exists(dst_season_poster_file)):
                        urllib.urlretrieve(season_poster, dst_season_poster_file)
                    #os.system("mv -v \"%s\" \"%s\"" %(src_filename, os.path.join(dst_season_dir, ep_name)))
                    print "mv -v \"%s\" \"%s\"" %(src_filename, os.path.join(dst_season_dir, dst_filename))
                """
                print(dst_filename)	
    
            
def get_movies(path, src, dst = None, simulate = True):
    xml = get_xml(get_dir(path, "movie"))  
    if dst != None : mk_dir(dst)  
    videos = xml.getElementsByTagName("Video")    
    for each in videos :
        media = each.getElementsByTagName("Media")[0]
        file = media.getElementsByTagName("Part")[0].getAttribute("file")
        if (src in str(file) ) :
            movie_info = get_video_info(each)                    
            for tag in each.getElementsByTagName("Genre"):
                movie_info +=  tag.getAttribute("tag") + ", "
            movie_info = movie_info[:-2]
            #print  movie_info      
            
            dir = str(os.path.join(dst, dirname_from_title(each)))
            if not os.path.exists(dir):
            	if dst != None : mk_dir(dir)    
            	urllib.urlretrieve(base_url + each.getAttribute("thumb"), dir + "/poster.jpg")
            	with codecs.open(os.path.join(dir, "movie.info"),  'w', encoding="utf8") as f:
                	f.write(movie_info)
            	base = os.path.split(file)[1]
            	sub = os.path.join(dir, os.path.splitext(base)[0] + ".en.srt");
            	_file = os.path.join(dir, base)
            	if (simulate == True) :
		  print "mv -v \"" + file + "\" \"" +  _file + "\""
		  os.system("periscope -l en \"" + _file + "\" --quiet")
            	else :
		  os.system("mv -v \"" + file + "\" \"" +  dir + "\"")
		  os.system("mv -v \"" + _dir + "/*.srt\"" + " \"" + _sub + "\"")
#todo get from plex                       

Movies = "/library/sections/1/all"
Series = "/library/sections/2/all"
Music = "/library/sections/11/all"


#src="/media/mintzaf/FAZTERDAT/Videos/Movies/Syfy"
#src="/home/mintzaf/Videos/TV"
#src="/media/mintzaf/FAZTERDAT/Music"
#dst=os.path.join(os.getenv("HOME"), "Plex/Music")
#dst="/media/mintzaf/FAZTERDAT/Videos/TV Shows"
#src = "/mnt/ntfs/MULTIBOOT/Download/Tv"
#dst = "/mnt/ntfs/MULTIBOOT/Download/Tv/New"
#src="/home/mintzaf/Videos/Movies"
#dst="/media/mintzaf/Elements/Media/Movies"
#tvshows(base_url, src, dst)

src="/mnt/ntfs/MULTIBOOT/Media/Downloads/Movies"
dst="/home/fact/Videos"
get_movies(base_url, srd)

#src=""
#dst="/home/mintzaf/Torrent/Music"
#get_music(base_url, src, dst)


        
