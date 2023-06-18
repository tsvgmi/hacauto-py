import logging
import time
from sqlalchemy import insert, values

from site_connect import SiteConnect
from smule_page   import SmulePage
from smule_model  import *

_logger = logging.getLogger(__name__)

class Scanner:
  def __init__(self, user, db, options = {}):
    self.user    = user
    self.db      = db
    self.options = options

    self.connector = SiteConnect('smule', self.options)
    self.spage     = SmulePage(self.connector.driver)

    time.sleep(1)
    _logger.debug(options)
    
  def like_set(self, song_set, count):
    stars = []
    for singer, slist in song_set.items():
      scount = count
      _logger.info(f"Liking {scount} songs from set for {singer}")
      for sinfo in slist:
        href = sinfo['href']
        if sinfo['href'].endswith('/ensembles'):
          continue
        if self.user in sinfo['record_by']:
          continue

        sql = f"select sid, user from loves where sid='{sinfo['sid']}' and user='{self.user}'"
        if self.db.conn.execute(text(sql)).first():
          continue

        if (exclude := self.options['exclude']):
          if exclude in sinfo['record_by']:
            continue

        if self.spage.like_song(sinfo['href']):
          _logger.info(f"Marking {sinfo['stitle']} ({sinfo['record_by']})")
          stars.append(sinfo)
          if (pause := self.options['pause']):
            time.sleep(1)
            self.spage.toggle_play(doplay=True)
            time.sleep(pause)

        sql = f"insert into loves (sid, user) values('{sinfo['sid']}', '{self.user}')"
        _logger.info(sql)
        self.db.conn.execute(text(sql))

        scount -= 1
        if scount <= 0:
          break
    return stars
#
#  def set_unfavs(songs, marking: true)
#    songs.each do |asong|
#      @spage.goto(asong[:href])
#      @spage.toggle_song_favorite(fav: false)
#      @spage.add_song_tag(['#thvfavs_%y'], asong) if marking
#      Plog.dump_info(msg: 'Unfav', stitle: asong[:stitle],
#                     record_by: asong[:record_by])
#    end
#  end
#
#  def unfavs_old(count, result)
#    if @options[:mine_only]
#      result = result.select do |sinfo|
#        sinfo[:record_by].start_with?(@user)
#      end
#    end
#    new_size = [result.size - count, 0].max
#    set_unfavs(result[new_size..])
#    result[0..new_size - 1]
#  end
#end
