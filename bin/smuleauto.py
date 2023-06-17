#!/bin/env python

import click
import glob
import os
import logging
import tabulate
import sys
import re

from smule_song import SmuleSong, DbConn, SmuleDB, Api

@click.group()
@click.option('--browser',   type=click.Choice(['firefox', 'chromes']),
        default='firefox', help='Browser to connect to site')
@click.option('--data-dir',  default='./data',
        help='Directory to keep database')
@click.option('--limit',     default=10_000)
@click.option('--logfile',   default='smule.log')
@click.option('--remote',    default='',
        help='URL for remote Selenium to connect to site')
@click.option('--song-dir',  default='/mnt/d/SMULE',
        help='Directory to save music files')
@click.pass_context
def cli(ctx, **kwargs):
  ctx.ensure_object(dict)
  for key, value in kwargs.items():
    ctx.obj[key] = value

@cli.command()
@click.pass_obj
def fix_db_date(obj):
  """Fix DB data that was in date only format"""

  db  = DbConn('data/smule.db').conn
  res = db.execute('select id,created,updated_at from performances')
  for rec in res.all():
    changes = []
    if len(rec[1]) == 10:
      changes.append(f"created = '{rec[1]} 00:00:00.000000'")
    if rec[2] and len(rec[2]) == 10:
      changes.append(f"updated_at = '{rec[2]} 00:00:00.000000'")
    if len(changes) > 0:
      changes = ", ".join(changes)
      sql = f"update performances set {changes} where id={rec[0]}"
      db.execute(sql)

@cli.command()
@click.argument('user')
@click.pass_obj
def fix_media_missing(obj, user):
  """Check if any media (m4u) files are missing (reference is db)

  USER: the main recorded user
  """

  db_conn      = DbConn(obj)
  query        = f"select sid from performances where record_by like '%{user}%' and deleted is null"
  result       = db_conn.select(query)
  db_sids      = [rec[0] for rec in result.all()]

  gpath        = obj['song_dir'] + "/store/????/*.m4a"
  fi_sids      = [os.path.basename(file).split('.')[0] for
                  file in glob.glob(gpath)]

  missing_sids = list(set(db_sids) - set(fi_sids))
  print("\n".join(missing_sids))
  logging.info("%d records, %d files missed", len(db_sids), len(missing_sids))

@cli.command()
@click.pass_obj
def fix_media_error(obj, **kwargs):
  """Check if any media (m4u) files have error (using ffmpeg)"""

  ccount   = 0
  song_dir = obj['song_dir']
  sfiles   = glob.glob(song_dir + "/STORE/????/*.m4a")

  with click.progressbar(sfiles, label='Check tags') as bar:
    for dfile in bar:
      if SmuleSong.has_error(dfile):
        logging.error("Error detected in %s", dfile)
        ccount += 1
  print(ccount, "files detected")

from sqlalchemy import select, insert, func, or_
from smule_model import *

@cli.command()
@click.pass_obj
@click.argument('user')
@click.argument('filter')
def fix_mp3_tags(obj, user, filter):
  """Retag of selected songs"""

  db_conn = DbConn(obj)
  stmt    = select(Performance).where(text(f'record_by like "%{user}%"')) \
                               .where(text(filter)) \
                               .limit(obj['limit'])
  result =  db_conn.execute(stmt)
  with click.progressbar(result.all(), label='Fix tags') as bar:
    for row in bar:
      song = SmuleSong(row[0])
      song.update_mp4tag()

@cli.command()
@click.argument('user')
@click.argument('filters', nargs=-1)
@click.option('-c', '--with-collabs', is_flag=True, help='Collect my joiners')
@click.pass_obj
def collect_songs(obj, user, filters, **kwargs):
  """Collect songs joined by USER"""
  print('user:', user)
  print('filters:', filters)
  for key, value in kwargs.items():
    print('K', key, ':', value)
  for key, value in obj.items():
    print('C', key, ':', value)

@cli.command()
@click.argument('user')
@click.argument('old_name')
@click.argument('new_name')
@click.option('--audit', is_flag=True, help='Audit change only')
@click.pass_obj
def move_singer(obj, user, old_name, new_name, **kwargs):
  """Rename a singer from old name to new name.

  Singer often changes display name.  This is tracked in DB, so we need to run
  this operation to rename all in song resources (db and mp4 tags)
  """
  if kwargs['audit']:
    name_chk = new_name
  else:
    name_chk = old_name
  
  stmt = select(Performance) \
            .where(text(f'record_by like "%{user}%"')) \
            .where(text(f'record_by like "%{name_chk}%"'))
  print(stmt)
  db_conn = DbConn(obj)
  result  = db_conn.execute(stmt)
  isaudit = kwargs['audit']
  with click.progressbar(result.all(), label='Rename singer') as bar:
    for row in bar:
        print(row)
        asong = SmuleSong(row[0])
        if isaudit:
          asong.update_mp4tag()
        elif asong.move_song(old_name, new_name):
          asong.update_mp4tag()
  db_conn.commit()

@cli.command()
@click.argument('user')
@click.argument('filters', nargs=-1)
@click.option('--tags', default='', help='Tags to match')
@click.option('--record', default='', help='Record to match')
@click.pass_obj
def to_open(obj, user, filters, **kwargs):
  """Show list of potential songs to open
  
  List the candidates for open from the matching filter.
  Filters is the list of SQL's into into DB.
  
  \b* Song which has not been opened
  \b* Was a favorites
  \b* Sorted by date
  """

  topen   = {}
  db_conn = DbConn(obj)
  stmt    = select(Performance.stitle).where(text(f'record_by = "{user}"'))
  stmt    = stmt.group_by(Performance.stitle)
  opened  = [rec[0] for rec in db_conn.execute(stmt)]

  stmt    = select(Performance.stitle)
  for filter in filters:
    stmt = stmt.where(text(filter))
  stmt       = stmt.group_by(Performance.stitle)
  candidates = [rec[0] for rec in db_conn.execute(stmt)]

  to_open = list(set(candidates) - set(opened))

  query = db_conn.session.query(Performance.stitle, 
              func.max(Performance.created).label('created'),
              SongInfo.author, SongInfo.singer, SongInfo.tags) \
              .filter(Performance.song_info_id == SongInfo.id) \
              .where(Performance.stitle.in_(to_open)) \
              .group_by(Performance.stitle) \
              .order_by('created')
  tags = kwargs['tags']
  if tags:
    query = query.filter(or_(
        SongInfo.author.like(f'%{tags}%'),
        SongInfo.singer.like(f'%{tags}%'),
        SongInfo.tags.like(f'%{tags}%')))
  print(tabulate.tabulate(query.all(),
              headers=['Title', 'Date', 'Author', 'Perf', 'Tags']))

@cli.command()
@click.option('--table', is_flag=True, help='Generate MD table')
@click.pass_obj
def clean_lyrics(obj, **kwargs):
  """Clean lyrics from lyric site to put into docs"""

  # Have to wait for reading all before starting to output
  buffer = [l for l in sys.stdin]

  # Some separation of output to input stream
  print("\n".join(['==========']*3))
  out_table = kwargs['table']
  if out_table:
    print('| | Lyrics |')
    print('|-| ------ |')
  for l in buffer:
    l = re.sub('\[[^\]]+\]', '', l.rstrip())
    if out_table:
      l = f"| | {l.strip()} |"
    print(l)

@cli.command()
@click.argument('user')
@click.pass_obj
def scan_favs(obj, user):
  """Scan list of favorites for USER"""
  favset  = Api.get_favs(user)
  SmuleDB(user, data_dir="./data").add_favorites(favset)

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
          format='%(levelname)3.3s %(asctime)s %(module)s:%(lineno)03d %(message)s',
          datefmt='%m/%d/%Y %H:%M:%S')
  logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
  cli()
