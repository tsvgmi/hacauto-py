import datetime as DT
import json as JS
import logging
import os
import requests
import subprocess as SP
import tempfile as TF
import re
import pytz
import click
import time
import emoji

from dateutil import parser

from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

ACCENT_MAP = {
  '[áàảãạâấầẩẫậăắằẳẵặ]': 'a',
  '[ÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶ]': 'A',
  'đ': 'd',
  'Đ': 'D',
  '[éèẻẽẹêếềểễệ]': 'e',
  '[ÉÈẺẼẸÊẾỀỂỄỆ]': 'E',
  '[íìỉĩị]': 'i',
  '[ÍÌỈĨỊ]': 'I',
  '[óòỏõọôốồổỗộơớờởỡợ]': 'o',
  '[ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]': 'O',
  '[úùủũụưứừửữự]': 'u',
  '[ÚÙỦŨỤƯỨỪỬỮỰ]': 'U',
  '[ýỳỷỹỵ]': 'y',
  '[ÝỲỶỸỴ]': 'Y',
}

def clean_emoji(str):
  return re.sub(':[^:]+:', '', emoji.demojize(str))

def normalize_vnaccent(str):
  for ptn, rep in ACCENT_MAP.items():
    str = re.sub(ptn, rep, str)
  return str

def to_stitle(str):
  str    = clean_emoji(str)
  stitle = re.sub('\s+[-=(].*$', '', str).replace('"', '')
  stitle = normalize_vnaccent(stitle)
  stitle = re.sub('[^a-z0-9 ]', '', stitle.lower())
  stitle = re.sub('\s+', ' ', stitle)
  stitle.strip()

def compact(list):
  return [v for v in list if v]

def get_page_curl(url, ofile=None, json=False, raw=False):
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

  if raw:
    return resp.content
  if json:
    return JS.loads(resp.content)
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
    get_page_curl(self.info.avatar, ofile=lcfile)

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

  # Account to move songs to.  i.e. user close old account and open
  # new one and we want to associate with new account
  # Or user have multiple accounts, but we want to collapse to one
  ALTERNATE = {
    'Annygermany':      'Dang_Anh_Anh',
    'ChiHoang55':       'ChiMHoang',
    'CucNguyenthanhho': 'HongCuc85',
    'Eddy2020_':        'Mina_________',
    'MaiLoan06':        'MLOAN06',
    '_Huong':           '__HUONG',
    '_MaiLan_':         '__MaiLan__',
    '_NOEXIST_':        'Dang_Anh_Anh',
    '__MinaTrinh__':    'Mina_________',
    'HieuLe2014':       'CL_281',
    'Thanhnhi2020':     'ThanhNhi___',
  }

  def record_by_map(record_by):
    result = []
    for ri in record_by:
      result.append(SmuleSong.ALTERNATE[ri] \
          if ri in SmuleSong.ALTERNATE else ri)
    return result
    
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

from sqlalchemy import create_engine, text, select, exists
from sqlalchemy.orm import Session

class DbConn:
  def __init__(self, dbfile):
    conn_str     = f"sqlite:///{dbfile}"
    self.engine  = create_engine(conn_str)
    self.conn    = self.engine.connect()
    self.session = Session(self.engine)

  def select(self, query):
    return self.conn.execute(text(query))

  def execute(self, stmt):
    return self.session.execute(stmt)

  def commit(self):
    return self.session.commit()

class SmuleDB(DbConn):
  def __init__(self, user, data_dir):
    super().__init__(f"{data_dir}/smule.db")
    self.user    = user
    self.content = self.session.query(Performance) \
        .where(text(f"record_by like '%{user}%'"))

  def add_favorites(self, block):
    query = 'update performances set oldfav=1 where isfav=1'
    self.conn.execute(query)

    query = 'update performances set isfav = NULL'
    self.conn.execute(query)

    sids = [repr(r['sid']) for r in block]
    query = 'update performances set isfav=1 where sid in (' + \
            ','.join(sids) + ')'
    self.conn.execute(query)

  def add_new_songs(self, block, isfav = True):
    now = DT.datetime.now()

    # Favlist must be reset if specified
    if isfav:
      sql = f"update performances set isfav = NULL where isfav=1"
      self.conn.execute(sql)

    newsets, updsets = [], []

    for r in block:
      r['updated_at'] = now
      if isfav:
        r['isfav'] = 1
      r.pop('lyrics',   None)
      r.pop('pic_urls', None)
      r.pop('accounts', None)
      
      rec = self.session.query(Performance) \
        .where(Performance.sid==r['sid']).first()

      if rec:
        updset = {
          'listens':   r['listens'],
          'loves':     r['loves'],
          'record_by': r['record_by'], # In case user change login
          'isfav':     r['isfav'],
          'avatar':    r['avatar'],
          'message':   r['message'],
        }
        for cfield in ['orig_city', 'latlong', 'latlong_2']:
          if cfield in r:
            updset[cfield] = r[cfield]

        if 'parent_sid' in r and r['parent_sid'] != 'ensembles':
          updset['parent_sid'] = r['parent_sid']
        if updset['isfav']:
          updset['oldfav'] = updset['isfav']
        rec.update(updset)
        rec.save
        updsets.append(r)
      else:
        #begin
        Performance.insert(r)
        newsets.append(r)
        #rescue StandardError => e
          #p e
        #end
      
    return [newsets, updsets]
  
    pass

class Api:
  def _extract_info(info):
    owner     = info['owner']
    record_by = [owner['handle']]
    for rinfo in info['other_performers']:
      record_by.append(rinfo['handle'])

    record_by_ids = [info['owner']['account_id']]
    if info['duet']:
        record_by_ids.append(info.get('duet', {})['account_id'])
    record_by_ids = [str(v) for v in compact(record_by_ids)]
    record_by_ids = ",".join(record_by_ids)

    stats = info['stats']
    return {
      'sid':           info['key'],
      'title':         info['title'],
      'stitle':        to_stitle(info['title']),
      'href':          info['web_url'],
      'message':       info['message'],
      'created':       parser.parse(info['created_at']),
      'avatar':        info['cover_url'],
      'listens':       stats['total_listens'],
      'loves':         stats['total_loves'],
      'gifts':         stats['total_gifts'],
      'record_by':     ','.join(SmuleSong.record_by_map(record_by)),
      'record_by_ids': record_by_ids,
      'latlong':       f"{owner['price']},{owner['discount']}",
    }

  def get_favs(user):
    _logger.info(f"Getting favorites for {user}")
    result = Api.get_songs(f"https://www.smule.com/{user}/favorites/json",
        limit=500, days=365*10)
    _logger.info("Collecting %d favorites from user %s", len(result), user)
    return result

  def get_songs(url, limit=100, days=365):
    allset    = []
    offset    = 0
    utc       = pytz.UTC
    first_day = utc.localize(DT.datetime.now() - DT.timedelta(days=days))
    _logger.debug(f"Collecting songs after {first_day}")

    done   = False
    with click.progressbar(length=limit, label='Get performances') as bar:
      for value in bar:
        ourl = f"{url}?order=created&offset={offset}"
        _logger.debug(f"url: {ourl}")
        if (output := get_page_curl(ourl, raw = True)) == 'Forbidden':
          time.sleep(2)
          next
        
        try:
          result = JS.loads(output)
        except JSONDecodeError:
          _logger.error("JSON decode error. Ignore")
          _logger.error(output)
          next

        slist  = result['list']
        _logger.debug("Getting %d entries", len(slist))
        for info in slist:
          allset.append(Api._extract_info(info))
          bar.update(1)
          if parser.parse(info['created_at']) <= first_day:
            logger.debug(f"Created less than {first_day}")
            done = True
            break
          
        else:
          # Bug at smule?, it gives bad next offset, so I only use to
          # check sentinel but use my own offset
          if (sentinel := result['next_offset']) <= 0:
            done = True
            break
          offset += len(slist)
          continue
        break
      if done:
        bar.finish()

    return allset

