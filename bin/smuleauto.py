#!/bin/env python

import click
import glob
import os
import logging
import tabulate
import sys
import re

from smule_song import SmuleSong, SmuleDB
from api        import Api
from scanner    import Scanner

@click.group()
@click.option('--browser',   type=click.Choice(['firefox', 'chromes']),
        default='firefox', help='Browser to connect to site')
@click.option('--data-dir',  default='./data',
        help='Directory to keep database')
@click.option('--limit',     default=10000)
@click.option('--logfile',   default='smule.log')
@click.option('--remote',    default='',
        help='URL for remote Selenium to connect to site')
@click.option('--song-dir',  default='/mnt/d/SMULE',
        help='Directory to save music files')
@click.pass_context
def cli(ctx, **options):
  ctx.ensure_object(dict)
  for key, value in options.items():
    ctx.obj[key] = value
  if os.getenv("SENTRY"):
    import sentry_sdk
    sentry_sdk.init(
      dsn="https://b99e54bca4c14e46b798083842e28369@o4505377394786304.ingest.sentry.io/4505377399832576",
      traces_sample_rate=1.0
    )
  if os.getenv("PDB"):
    import pdb; pdb.set_trace()

@cli.command()
@click.pass_obj
def fix_db_date(obj):
  """Fix DB data that was in date only format"""

  db_conn = SmuleDB('', obj['data_dir']).conn
  res     = db_conn.execute('select id,created,updated_at from performances')
  for rec in res.all():
    changes = []
    if len(rec[1]) == 10:
      changes.append(f"created = '{rec[1]} 00:00:00.000000'")
    if rec[2] and len(rec[2]) == 10:
      changes.append(f"updated_at = '{rec[2]} 00:00:00.000000'")
    if len(changes) > 0:
      changes = ", ".join(changes)
      sql = f"update performances set {changes} where id={rec[0]}"
      db_conn.execute(sql)

@cli.command()
@click.argument('user')
@click.pass_obj
def fix_media_missing(obj, user):
  """Check if any media (m4u) files are missing (reference is db)

  USER: the main recorded user
  """

  db_conn = SmuleDB(user, obj['data_dir']).conn
  query   = f"select sid from performances where record_by like '%{user}%' and deleted is null"
  result  = db_conn.execute(query)
  db_sids = [rec[0] for rec in result.all()]

  gpath   = obj['song_dir'] + "/store/????/*.m4a"
  fi_sids = [os.path.basename(file).split('.')[0] for file in glob.glob(gpath)]

  missing_sids = list(set(db_sids) - set(fi_sids))
  print("\n".join(missing_sids))
  _logger.info("%d records, %d files missed", len(db_sids), len(missing_sids))

@cli.command()
@click.pass_obj
def fix_media_error(obj, **options):
  """Check if any media (m4u) files have error (using ffmpeg)"""

  ccount   = 0
  song_dir = obj['song_dir']
  sfiles   = glob.glob(song_dir + "/STORE/????/*.m4a")

  with click.progressbar(sfiles, label='Check tags') as bar:
    for dfile in bar:
      if SmuleSong.has_error(dfile):
        _logger.error("Error detected in %s", dfile)
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

  db_conn = SmuleDB(user, obj['data_dir']).conn
  stmt    = select(Performance).where(text(f'record_by like "%{user}%"')) \
                               .where(text(filter)) \
                               .limit(obj['limit'])
  result  =  db_conn.execute(stmt)
  with click.progressbar(result.all(), label='Fix tags') as bar:
    for row in bar:
      song = SmuleSong(row[0])
      song.update_mp4tag()

@cli.command()
@click.argument('user')
@click.argument('filters', nargs=-1)
@click.option('--with-collabs', is_flag=True, help='Collect my joiners')
@click.pass_obj
def collect_songs(obj, user, filters, **options):
  """Collect songs joined by USER"""
  print('user:', user)
  print('filters:', filters)
  for key, value in options.items():
    print('K', key, ':', value)
  for key, value in obj.items():
    print('C', key, ':', value)

from sqlalchemy.orm import Session

@cli.command()
@click.argument('old_name')
@click.argument('new_name')
@click.option('--audit', is_flag=True, help='Audit change only')
@click.pass_obj
def move_singer(obj, old_name, new_name, **options):
  """Rename a singer from old name to new name.

  Singer often changes display name.  This is tracked in DB, so we need to run
  this operation to rename all in song resources (db and mp4 tags)
  """
  if options['audit']:
    name_chk = new_name
  else:
    name_chk = old_name
  
  db      = SmuleDB('', obj['data_dir'])
  stmt    = select(Performance).where(text(f'record_by like "%{name_chk}%"'))
  isaudit = options['audit']
  with Session(db.engine) as session:
    result = session.execute(stmt)
    count  = 0
    with click.progressbar(result.all(), label='Rename singer') as bar:
      for row in bar:
          doupdate = False
          asong    = SmuleSong(row[0])
          if isaudit:
            doupdate = True
          elif asong.move_song(old_name, new_name):
            doupdate = True
          if not doupdate:
            continue
          asong.update_mp4tag()
          session.commit()
          count += 1
    print(f"{count} records updated")

@cli.command()
@click.argument('user')
@click.argument('filters', nargs=-1)
@click.option('--tags', default='', help='Tags to match')
@click.option('--record', default='', help='Record to match')
@click.pass_obj
def to_open(obj, user, filters, **options):
  """Show list of potential songs to open
  
  List the candidates for open from the matching filter.
  Filters is the list of SQL's into into DB.
  
  \b* Song which has not been opened
  \b* Was a favorites
  \b* Sorted by date
  """

  topen   = {}
  db_conn = SmuleDB(user, obj['data_dir']).conn
  stmt    = select(Performance.stitle).where(text(f'record_by = "{user}"'))
  stmt    = stmt.group_by(Performance.stitle)
  opened  = [rec[0] for rec in db_conn.execute(stmt)]

  stmt    = select(Performance.stitle)
  for filter in filters:
    stmt = stmt.where(text(filter))
  stmt       = stmt.group_by(Performance.stitle)
  candidates = [rec[0] for rec in db_conn.execute(stmt)]

  to_open    = list(set(candidates) - set(opened))

  query      = db_conn.session.query(Performance.stitle, 
                  func.max(Performance.created).label('created'),
                  SongInfo.author, SongInfo.singer, SongInfo.tags) \
                  .filter(Performance.song_info_id == SongInfo.id) \
                  .where(Performance.stitle.in_(to_open)) \
                  .group_by(Performance.stitle) \
                  .order_by('created')
  if (tags := options['tags']):
    query = query.filter(or_(
        SongInfo.author.like(f'%{tags}%'),
        SongInfo.singer.like(f'%{tags}%'),
        SongInfo.tags.like(f'%{tags}%')))
  print(tabulate.tabulate(query.all(),
              headers=['Title', 'Date', 'Author', 'Perf', 'Tags']))

@cli.command()
@click.option('--table', is_flag=True, help='Generate MD table')
@click.pass_obj
def clean_lyrics(obj, **options):
  """Clean lyrics from lyric site to put into docs"""

  # Have to wait for reading all before starting to output
  buffer = [l for l in sys.stdin]

  # Some separation of output to input stream
  print("\n".join(['==========']*3))
  out_table = options['table']
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
  SmuleDB(user, obj['data_dir']).add_favorites(favset)

@cli.command()
@click.pass_obj
@click.argument('user')
@click.argument('count', type=click.INT)
@click.argument('singers', nargs=-1)
@click.option('--top', type=click.INT, help='Top n joiners')
@click.option('--days', default=90, help='Look back n days only')
@click.option('--exclude', type=click.STRING, help='List of users to exclude')
@click.option('--pause', default=5, help='Time to wait between songs')
def like_singers(obj, user, count, singers, **options):
  """Liking some songs on listed singers"""

  db   = SmuleDB(user, obj['data_dir'])
  days = options['days']
  if (top := options['top']):
    _logger.info(repr({"top":top}))
    singers  = list(singers) + \
        db.top_partners(top, exclude=options['exclude'], days=days)

  _logger.debug(repr({"count": len(singers), "singers": singers}))
  
  allsets = {}
  for asinger in singers:
    perfset = Api.get_performances(asinger, limit=count, days=days)
    allsets[asinger] = perfset

  starred  = Scanner(user, db).like_set(allsets, count,
      exclude=options['exclude'], pause=options['pause'])
  counters = {}
  for song in starred:
    for singer in song['record_by'].split(','):
      counters[singer] = counters[singer]+1 if singer in counters else 1
    
  scounters = sorted(counters.items(), key=lambda x:x[1])
  table = [list(e) for e in scounters]
  print(tabulate.tabulate(table, headers=['Singer', 'Count']))

import json5 as CJS
import json as JS
import os

@cli.command()
@click.pass_obj
@click.argument('args', nargs=-1)
def set_vc_args(obj, args):
  cf_file = '.vscode/launch.json'
  with open(cf_file) as fid:
    config = CJS.load(fid)

  config['configurations'][0]['args'] = list(args)
  config['configurations'][0]['cwd']  = os.getcwd()
  print(JS.dumps(config, indent=4))

  with open(cf_file, 'w') as fod:
    print(JS.dumps(config, indent=4), file=fod)

import datetime as DT
from dateutil import parser

@cli.command()
@click.pass_obj
@click.argument('user')
@click.argument('mode', default='following')
def show_follows(obj, user, mode):
  """Show the activities for following list"""

  conn   = SmuleDB(user, obj['data_dir']).conn
  sql    = f"select name from singers where {mode} = 1"
  folset = {r[0] for r in conn.execute(sql).all()}

  sql = f"""
    select record_by, count(*) as count, max(created) as created,
      sum(isfav+oldfav) as favs from performances
      where record_by like '%{user}%'
      group by record_by order by created desc
      """
  counters = {}
  for r in conn.execute(sql).all():
    record_by = [i for i in r[0].split(',') if i in folset]
    for singer in record_by:
      favs = r[3] if r[3] else 0
      if singer not in counters:
        date = DT.datetime.now() - parser.parse(r[2])
        counters[singer] = {"count": r[1], "favs": favs, "days": date.days}
      else:
        counters[singer]['count'] += r[1]
        counters[singer]['favs']  += favs

  table = [[singer, r['count'], r['favs'], r['days']] \
      for singer, r in counters.items()]
  print(tabulate.tabulate(table, headers=['Singer', 'Songs', 'Favs', 'Days' ]))

@cli.command()
@click.pass_obj
@click.argument('user')
@click.argument('count', default=10)
@click.option('--mine-only', is_flag=True, help='Unfavs from my joins only')
def unfavs_old(obj, user, count = 10, **options):
  """Unfavs oldest favs to keep list under 500 and leave space for adding
     new entries"""
  
  db     = SmuleDB(user, obj['data_dir'])
  favset = Api.get_favs(user)
  result = Scanner(user, db) \
      .unfavs_old(favset, count, mine_only=options['mine_only'])
  db.add_new_songs(result, isfav = True)

@cli.command()
@click.pass_obj
def check_joiners(obj):
  """Check for all names of joiners (when they change)"""
  db_conn = SmuleDB('', obj['data_dir']).conn
  sql = """
    select record_by, record_by_ids, count(*) from performances group by record_by_ids
      order by created"""
  umap  = {}
  for r in db_conn.execute(text(sql)).all():
    if not r[0] or not r[1]:
      continue
    record_by     = r[0].split(',')
    record_by_ids = r[1].split(',')
    for singer, rid in zip(record_by, record_by_ids):
      if rid not in umap:
        umap[rid] = set()
      umap[rid].add(singer)
  umap = [(rid, singers) for rid, singers in umap.items() if len(singers) > 1]
  print(tabulate.tabulate(([rid, list(singers)[1:], list(singers)[0]] \
      for rid, singers in umap), headers=['SID', 'Earlier', 'Latest']))

################################################################################
if __name__ == '__main__':
  _logger = logging.getLogger(__name__)
  logging.basicConfig(level=logging.INFO,
          format='%(levelname)3.3s %(asctime)s %(module)s:%(lineno)03d %(message)s',
          datefmt='%m/%d/%Y %H:%M:%S')
  logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
  cli()

#module SmuleAuto
#  class Main < Thor
#    class_option :browser,  type: :string, default: 'firefox',
#                            desc: 'Browser to use (firefox|chrome)'
#    class_option :data_dir, type: :string, default: './data',
#                            desc: 'Data directory to keep database'
#    class_option :days,     type: :numeric, default: 7,
#                            desc: 'Days to look back'
#    class_option :force,    type: :boolean
#    class_option :limit,    type: :numeric, desc: 'Max # of songs to process',
#                            default: 10_000
#    class_option :logfile,  type: :string
#    class_option :open,     type: :boolean,
#                            default: `uname`.chomp == 'Darwin'
#    class_option :remote,   type: :string, desc: 'Remote URL for selenium'
#    class_option :skip_auth, type: :boolean,
#                             desc: 'Login account from browser (not anonymous)'
#    class_option :song_dir, type: :string, default: '/mnt/d/SMULE',
#                            desc: 'Data directory to keep songs (m4a)'
#    class_option :verbose,  type: :boolean
#
#    no_commands do
#      def _get_users(users, agroup)
#        result = []
#        bar = TTY::ProgressBar.new("Users [#{users.size}] [:bar] :percent",
#                                   total: users.size)
#        users.each do |user|
#          res = HTTP.follow.get("https://www.smule.com/#{user}").to_s
#          res = Nokogiri::HTML(res).css('script')[0].to_s.split("\n")
#                        .find { |l| l =~ /Profile: {/ }
#          if res
#            res = res.sub(/^\s*Profile:\s*/, '').sub(/,\s*$/, '')
#            res = JSON.parse(res)['user']
#            result << {
#              account_id: res['account_id'],
#              name: user,
#              avatar: res['pic_url'],
#            }
#          else
#            Plog.warn("No info found for #{user}")
#          end
#          bar.advance
#        end
#        Plog.dump_info(agroup: agroup, size: result.size)
#        result
#      end
#    end
#
#    desc 'scan_follows user', 'Scan the follower/following list'
#    def scan_follows(user)
#      cli_wrap do
#        api     = Api.new
#        db      = SmuleDB.instance(user)
#        joiners = db.content.group(:record_by).all
#                    .map { |r| r[:record_by].sub(/(^#{user},|,#{user}$)/, '') }
#                    .uniq.sort
#        knowns   = Singer.all.map { |r| r[:name] }.sort
#        unknowns = joiners - knowns
#
#        unknown_set = _get_users(unknowns, :unknown)
#
#        fset = %w[following followers].map do |agroup|
#          api.get_user_group(user, agroup)
#        end
#        SmuleDB.instance(user)
#               .set_follows(fset[0], fset[1], unknown_set)
#        true
#      end
#    end
#
#    desc 'get_user_group(user, agroup)', 'get_user_group'
#    def get_user_group(user, agroup)
#      cli_wrap do
#        api = Api.new
#        api.get_user_group(user, agroup).to_yaml
#      end
#    end
#
#    desc 'play user', 'Play songs from user'
#    option :download, type: :string, desc: 'Dir to download music to'
#    long_desc <<~LONGDESC
#            Start a CLI player to play songs from user.  Player support various command to
#            control the song and how to play.
#      #{'      '}
#            Player keep the play state on the file splayer.state to allow it to resume where
#            it left off from the previous run.
#    LONGDESC
#    def play(user)
#      cli_wrap do
#        require 'smule_auto/smule_player'
#
#        _tdir_check
#        SmulePlayer.new(user, options).play_all
#      end
#    end
#
#    option :verify,  type: :boolean
#    option :open,    type: :boolean, desc: 'Opening mp4 after download'
#    def watch_mp4(dir, user, csong_file: 'cursong.yml')
#      cli_wrap do
#        woptions = writable_options
#        unless (value = woptions[:logfile]).nil?
#          woptions[:logger] = PLogger.new(value)
#        end
#        FirefoxWatch.new(user, dir, csong_file, woptions).start
#        sleep
#      end
#    end
#  end
#end
#
#SmuleAuto::Main.start(ARGV) if __FILE__ == $PROGRAM_NAME
