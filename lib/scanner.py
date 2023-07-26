import logging
import time
from sqlalchemy import insert, values

from site_connect import SiteConnect
from smule_page   import SmulePage
from smule_model  import *

_logger = logging.getLogger(__name__)

class Scanner:
  def __init__(self, user, db):
    self.user      = user
    self.db        = db
    self.connector = SiteConnect('smule')
    self.spage     = SmulePage(self.connector.driver)
    time.sleep(1)
    
  def like_set(self, song_set, count, exclude=None, pause=0):
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

        if exclude and (exclude in sinfo['record_by']):
          continue

        if self.spage.like_song(sinfo['href']):
          _logger.info(f"Marking {sinfo['stitle']} ({sinfo['record_by']})")
          stars.append(sinfo)
          if pause > 0:
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

  def unfavs_old(self, songs, count, mine_only=False):
    if mine_only:
      songs = [song for song in songs if song['record_by'].startswith(self.user)]

    new_size = max(len(songs) - count, 0)

    # Mark the end of list
    for asong in songs[new_size:-1]:
      self.spage.goto(asong['href'])
      self.spage.toggle_song_favorite(fav = False)
      if marking:
        self.spage.add_song_tag(['#thvfavs_%y'], asong)
      _logger.info(repr({"msg": 'Unfav', "stitle": asong['stitle'],
                         "record_by": asong['record_by']}))

    return songs[0:new_size]

