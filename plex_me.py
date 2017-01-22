#!/usr/bin/python
import os 
from xml.dom.minidom import parseString
import requests
import codecs
import shutil
from unidecode import unidecode

PLEX_BASE_URL = ""
PLEX_TOKEN = ""

__verbose__ = 1

class Plex_Section:
    url = ""
    src_dir = ""
    dst_dir = ""
    
def get_plex_url(plex_url, path_to_page, token):
    return "%s/%s?X-Plex-Token=%s" %(plex_url, path_to_page,token)

def mk_dir(d):
    os.system("mkdir -p \"%s\""%(d))

def retrieve_image(url, fname):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
      r.raw.decode_content = True 
      with open(fname, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    else :
      print "Something went wrong"


def get_xml(url):
    r = requests.get(url)
    xml = parseString(str(r.text))
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
    
def dirname_from_title(title, year):
    if year in title:
        return title
    else:
        return "%s (%d)" %(convert_to_ascii(title), int(year))

def get_video_info(v):
    filename = v.getElementsByTagName("Part")[0].getAttribute("file")
    summary = get_video_summary(v)
    return [filename, summary,  v.getAttribute("thumb")]                    

# todo section title
def get_plex_section_url(path, plex_type, section_title = None):
    sections_url = get_plex_url(path, "library/sections", PLEX_TOKEN)
    if __verbose__ > 0 : print sections_url
    sections = get_xml(sections_url)
    _dir = filter( lambda d : d.getAttribute("type") == plex_type, sections.getElementsByTagName("Directory"))
    section_url = get_plex_url(path, "library/sections/%d/all" %(int(_dir[0].getAttribute("key"))), PLEX_TOKEN)
    if __verbose__ > 0 : print section_url
    return section_url

# WIP
def get_music(path, src, dst = None):
    xml = get_xml(get_plex_section_url(path, "artist"))
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
            tracks =  get_xml(PLEX_BASE_URL + album.getAttribute("key")).getElementsByTagName("Track")
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
                        

class Plex_Episode(object):
  def __init__ (self, episode, season_indx):
      self.fname = get_episode_filename(episode)
      self.title = episode.getAttribute("title")
      self.index = episode.getAttribute("index")
      #print "%s %s"%(self.title, self.fname)
      #print "episode-%s %s"%(self.index, self.title)
      self.info = self.get_summary(episode, season_indx)
      
  global  get_episode_filename
  def get_episode_filename(episode):
      return episode.getElementsByTagName("Part")[0].getAttribute("file")
    
  def get_summary(self, episode, season_indx):
      info = "%s\n" % (self.title)
      info += "Season %s Episode %s\n" %(season_indx, self.index)
      info += "IMDB : %s\n" % (episode.getAttribute("rating"))
      info += "%s\n\n" % (episode.getAttribute("summary"))      
      return info   
  
  
class Plex_Season(object):
   def __init__(self, season, src):
      self.index = season.getAttribute("index")
      self.title = season.getAttribute("title")
      self.poster_url = get_plex_url(PLEX_BASE_URL, season.getAttribute("thumb")[1:], PLEX_TOKEN)
      #print "Season %s"%(self.index)
      self.episodes = []
            
      for ep in self.get_episodes(season):
         if (src in get_episode_filename(ep)):
            self.episodes.append(Plex_Episode(ep, self.index))
         
   def get_episodes(self, season):
      seasons_url = get_plex_url(PLEX_BASE_URL, season.getAttribute("key")[1:], PLEX_TOKEN)
      return get_xml(seasons_url).getElementsByTagName("Video")

class Plex_Shows(object):
    def __init__(self, show, src):
      self.title =  show.getAttribute("title")
      self.year = show.getAttribute("year")
      #print "%s, %s"%(self.title, self.year)
      self.info = self.get_show_info(show)
      self.poster_url = get_plex_url(PLEX_BASE_URL, show.getAttribute("thumb")[1:], PLEX_TOKEN)
      self.seasons = []
      p_seasons = self.get_seasons(show)
      
      for s in (s for s in p_seasons if s.getAttribute("type") == "season"):
          self.seasons.append(Plex_Season(s, src)) 
          
    def get_show_info(self, show):
      info = "%s, %s\n%s\n" %(self.title, self.year, show.getAttribute("summary"))
      return info
      
    def get_seasons(self, show):
      seasons_url = get_plex_url(PLEX_BASE_URL, show.getAttribute("key")[1:], PLEX_TOKEN)
      return get_xml(seasons_url).getElementsByTagName("Directory")
 
def get_tvshows(path, auth_token, src_dir, dst_dir = None, simulate = True):
    global PLEX_BASE_URL
    global PLEX_TOKEN
    PLEX_BASE_URL = path
    PLEX_TOKEN = auth_token
    xml = get_xml(get_plex_section_url(path, "show"))  
    if dst_dir != None :  mk_dir(dst_dir)
    P_Shows = xml.getElementsByTagName("Directory")
    shows = []
    
    # Parse shows
    for show in P_Shows:
      _show = Plex_Shows(show, src_dir)
      #prunning
      _show.seasons = [ _s for _s in _show.seasons if len(_s.episodes) > 1 ]
      if len(_show.seasons): shows.append(_show)
    
    # 
    for sh in shows:
      if dst_dir != None :
          dst_series_dir = os.path.join(dst_dir, dirname_from_title(sh.title, sh.year))
          dst_series_info_file = os.path.join(dst_series_dir, convert_to_ascii(sh.title).replace(" ", ".") + ".info")
          dst_series_poster_file = os.path.join(dst_series_dir, "poster.jpg")
          mk_dir(dst_series_dir)
          if (not os.path.exists(dst_series_info_file)):                    
              with codecs.open(dst_series_info_file,  'w', encoding="utf8") as f:
                 f.write(sh.info)  
          if (not os.path.exists(dst_series_poster_file)):
              retrieve_image(sh.poster_url, dst_series_poster_file)
                    
      print sh.info
      for se in sh.seasons:
          print se.title
          if dst_dir != None :
             dst_season_dir = os.path.join(dst_series_dir, se.title)
             dst_season_poster_file = os.path.join(dst_season_dir, (convert_to_ascii(sh.title)) + "." + se.title + ".jpg")
          for ep in se.episodes:
              dst_filename = "%s S%02dE%02d %s" %(sh.title, int(se.index), int(ep.index), ep.title)
	      dst_filename = convert_to_ascii(dst_filename) + os.path.splitext(ep.fname)[1]
              print dst_filename
              if dst_dir != None : 
                    mk_dir(dst_season_dir) 
                    with codecs.open(dst_series_info_file,  'a', encoding="utf8") as f:
                        f.write(ep.info)                                
                    if (not os.path.exists(dst_season_poster_file)):
                        retrieve_image(se.poster_url, dst_season_poster_file)
                    dst_file_path = os.path.join(dst_season_dir, dst_filename)    
                    if simulate == True :
                        if __verbose__ > 0 : "%s -> %s" %(ep.fname, dst_file_path)
                        os.system("touch \"%s\"" %(dst_file_path))
                    else :
                        os.system("mv -v \"%s\" \"%s\"" %(ep.fname, dst_file_path))             
      
    
class Plex_Movie(object):
    def __init__(self, p_Video, src_dir):
      self.fname = ""
      file_name = self.get_file_name(p_Video)
      if src_dir in file_name:
          if __verbose__ > 1 : print file_name
          self.fname = file_name
          self.title = p_Video.getAttribute("title")
          self.year = p_Video.getAttribute("year")
          self.info = self.get_summary(p_Video)
          self.thumb_url = self.get_thumb_url(p_Video)

    def get_file_name(self, p_Video):
      return  p_Video.getElementsByTagName("Media")[0].getElementsByTagName("Part")[0].getAttribute("file")

    def get_summary(self, P_Video):
      info = "%s, %s\n" % (self.title, self.year)
      info += "\n%s\n" % (P_Video.getAttribute("tagline"))
      info += "%s\n\n" % (P_Video.getAttribute("summary"))
      info += "IMDB : %s\n" % (P_Video.getAttribute("rating"))
      info += "Genre : "
      if __verbose__ > 0: print "%s %s"%(self.title, self.year)
      for tag in P_Video.getElementsByTagName("Genre"):
          info += "%s, "%(tag.getAttribute("tag"))
      info = info[:-2] # strip last comma
      if __verbose__ > 1: print info   
      return info 
    
    def get_thumb_url(self, P_Video):
      thumb = get_plex_url(PLEX_BASE_URL, P_Video.getAttribute("thumb")[1:], PLEX_TOKEN)
      if __verbose__ > 1 : print thumb
      return thumb
	  
# subtitle support
# os.system("periscope -l en \"" + _file + "\" --quiet")     
def get_movies(path, auth_token, src, dst = None, simulate = True):
    global PLEX_BASE_URL
    global PLEX_TOKEN
    PLEX_BASE_URL = path 
    PLEX_TOKEN = auth_token
    xml = get_xml(get_plex_section_url(path, "movie"))
    if dst != None : mk_dir(dst)  
    videos = xml.getElementsByTagName("Video")
    for p_Video in videos :
        m = Plex_Movie(p_Video, src)
        if m.fname :
           dir_name = "%s (%d)" %(convert_to_ascii(m.title), int(m.year))
           if dst != None : 
             dst_dir = os.path.join(dst, dir_name)
             if os.path.exists(dst_dir):
               print "Destination already exits"
             else:
	       mk_dir(dst_dir)
               retrieve_image(m.thumb_url, os.path.join(dst_dir, "poster.jpg"))
               dst_fname =  os.path.join(dst_dir, os.path.split(m.fname)[1])
               with codecs.open(os.path.join(dst_dir, "movie.info"),  'w', encoding="utf8") as f:
                 f.write(m.info)
               if simulate == True:
                 if __verbose__ > 1 : "%s -> %s" %(m.fname, dst_fname)
                 os.system("touch \"%s\"" %(dst_fname))
               else :
		 #print "mv -v \"%s\" \"%s\"" %(m.fname, dst_fname) 
		 os.system("mv -v \"%s\" \"%s\"" %(m.fname, dst_fname) )                 



        
