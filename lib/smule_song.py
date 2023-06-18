import datetime as DT
import logging
import os
import subprocess as SP
import tempfile as TF
import re
import click
import time

from core import get_page_curl

_logger = logging.getLogger(__name__)

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
    _logger.debug(f"Changing {cur_record} to {new_record}")
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

class SmuleDB:
  def __init__(self, user, data_dir):
    self.user    = user
    self.engine  = create_engine(f"sqlite:///{dbfile}")
    self.conn    = self.engine.connect()
    self.session = Session(self.engine)

  def top_partners(self, limit, exclude=None, days=90):
    odate   = (DT.datetime.now() - DT.timedelta(days=days)).strftime('%Y-%m-%d')
    if exclude:
      exclude = exclude.split(',')
      filter = [f"record_by not like '%{u}%'" for u in exclude]
      filter = " and ".join(filter)
      filter = f"and ({filter})"
    else:
      filter = ''
    query = f"""
      select record_by, count(*) as count, sum(loves) as loves,
        sum(listens) as listens, sum(stars) as stars,
        sum(isfav)+sum(oldfav) as favs
      from performances where record_by != '{self.user}' and
        created > '{odate}' {filter}
      group by record_by order by listens desc
      """
    _logger.info(query)

    rank   = {}
    filter = f",?{self.user},?"
    for r in self.conn.execute(query):
      key = re.sub(filter, '', r['record_by'])
      if key not in rank:
        rank[key] = {'count': 0, 'loves': 0, 'listens': 0,
                     'favs': 0, 'stars': 0}
      rank[key]['count']   += r['count']
      rank[key]['loves']   += r['loves']
      rank[key]['listens'] += r['listens']
      rank[key]['stars']   += r['stars']
      if r['favs']:
        rank[key]['favs']    += r['favs']
    
    for _singer, sinfo in rank.items():
      score = sinfo['count'] + sinfo['favs']*10 + sinfo['loves']*0.2 + \
              sinfo['listens']/20.0 + sinfo['stars']*0.1
      sinfo['score'] = score
    
    srank        = sorted(rank.items(), key=lambda x:x[1]['score'], reverse=True)
    top_partners = [item[0] for item in srank[0:limit]]
    _logger.info(" ".join(top_partners))
    return top_partners

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

