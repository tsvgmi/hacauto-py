import datetime as DT
import json as JS
import logging
import os
import requests
import subprocess as SP
import tempfile as TF

from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

def get_parsed_page(url, ofile=None, json=False, raw=False):
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"
  }
  _logger.debug('Request from %s', url)
  resp = requests.get(url, headers=headers)
  if ofile:
    with open(ofile, 'wb') as f:
      f.write(resp.content)
    _logger.debug('Written to %s', ofile)
    return

  if json:
    return JS.loads(resp.content)
  if raw:
    return resp.content
  return BeautifulSoup(resp.content, 'html.parser')

class SmuleSong:
  def __init__(self, sinfo):
    self.info     = sinfo;
    self.surl     = f"https://www.smule.com#{sinfo.href}"
    self.location = SmuleSong.stored_location(sinfo.sid)
    self.lyrics   = None
    if (not self.info.created):
      self.info.created = DT.datetime.now()

  def update_mp4tag(self):
    if os.path.isfile(self.location):
      href    = f"https://www.smule.com{self.info.href}"
      date    = self.info.created.strftime('%Y-%m-%d')
      album   = self.info.created.strftime('Smule-%Y.%m')
      artist  = self.info.record_by.replace(',', ', ')
      release = self.info.created.isoformat()
      comment = f"{date} - {href}"
      title   = self.info.title

    command = f"atomicparsley {self.location}"
    lcfile  = 'logs/' + os.path.basename(self.info.avatar)
    get_parsed_page(self.info.avatar, ofile=lcfile)

    if os.path.isfile(lcfile) and \
      SP.run(f"file {lcfile}", capture_output=True, shell=True) \
            .stdout.decode().rfind('JPEG') > 0:
      command += f" --artwork REMOVE_ALL --artwork {lcfile}"
    
    command += f" --title '{title}' --artist '{artist}' --album '{album}'"
    command += f" --year '{release}'"
    command += f" --comment '{comment}'"

    l_flag = ''
    if self.lyrics:
      tmpf = TF.NamedTemporaryFile(suffix='.txt', delete=False)
      puts(self.lyrics, file=tmpf)
      tmpf.close
      l_flag = f" --lyricsFile {tmpf.name}"
    _logger.debug(command)
    SP.run(command, shell=True, capture_output=True)

  def move_song(self, old_name, new_name):
    cur_record = self.info.record_by
    new_record = cur_record.replace(old_name, new_name)
    if new_record == cur_record:
        _logger.info('No change in data')
        return False
    self.info.record_by = new_record
    _logger.info(f"Changing {cur_record} to {new_record}")
    return True

  song_dir = "/mnt/d/SMULE"

  # Class methods
  def stored_location(sid):
    newdir   = ''.join([f[0:2] for f in sid.split('_')])
    location = SmuleSong.song_dir + '/STORE/' + f"{newdir}/{sid}.m4a"
    os.makedirs(os.path.dirname(location), exist_ok=True)
    return location

  def has_error(file):
    command = f'ffmpeg -i {file} -f null -  2>&1 | grep error'
    try:
      SP.run(command, shell=True, check=True)
    except SP.CalledProcessError:
      return False
    return True

######################################################################
from smule_model import *

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

class DbConn:
  def __init__(self, obj):
    self.obj     = obj
    data_dir     = obj['data_dir']
    conn_str     = f"sqlite:///{data_dir}/smule.db"
    self.engine  = create_engine(conn_str)
    self.conn    = self.engine.connect()
    self.session = Session(self.engine)

  def select(self, query):
    return self.conn.execute(text(query))

  def execute(self, stmt):
    return self.session.execute(stmt)

  def commit(self):
    return self.session.commit()

