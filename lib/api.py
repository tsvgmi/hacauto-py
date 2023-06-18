import click
import datetime as DT
import json as JS
import logging
import pytz
from dateutil import parser

from core       import get_page_curl, to_stitle
from smule_song import SmuleSong

_logger = logging.getLogger(__name__)

class Api:
  def _extract_info(info):
    owner     = info['owner']
    record_by = [owner['handle']]
    for rinfo in info['other_performers']:
      record_by.append(rinfo['handle'])

    record_by_ids = [info['owner']['account_id']]
    if info['duet']:
        record_by_ids.append(info.get('duet', {})['account_id'])
    record_by_ids = [str(v) for v in record_by_ids]
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
    _logger.info(f"Collecting {len(result)} favorites from user {user}")
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
        
        result = None
        try:
          result = JS.loads(output)
        except JS.JSONDecodeError:
          _logger.error("JSON decode error. Ignore")
          _logger.error(output)
          next

        slist  = result['list']
        _logger.debug("Getting %d entries", len(slist))
        for info in slist:
          allset.append(Api._extract_info(info))
          bar.update(1)
          if parser.parse(info['created_at']) <= first_day:
            _logger.debug(f"Created less than {first_day}")
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

  def get_performances(user, limit=500, days=90):
    result = Api.get_songs(f"https://www.smule.com/{user}/performances/json",
                           limit, days)
    _logger.info(f"Collecting {len(result)}/{limit} songs from user {user} in last {days} days")
    return result

##!/usr/bin/env ruby
## frozen_string_literal: true
#
##---------------------------------------------------------------------------
## File:        api.rb
## Date:        2023-04-22 16:40:23 -0700
## $Id$
##---------------------------------------------------------------------------
##++
#
#module SmuleAuto
#  # Docs for Api
#  class Api
#    include HtmlRes
#
#    def initialize(options = {})
#      @options = options
#    end
#
#    def _extract_info(info)
#      owner     = info['owner']
#      record_by = [owner['handle']]
#      info['other_performers'].each do |rinfo|
#        record_by << rinfo['handle']
#      end
#      record_by_ids = [info.dig(*%w[owner account_id]),
#                       info.dig(*%w[duet account_id]),].compact.join(',')
#      stats = info['stats']
#      {
#        sid: info['key'],
#        title: info['title'],
#        stitle: to_stitle(info['title']),
#        href: info['web_url'],
#        message: info['message'],
#        created: Time.parse(info['created_at']),
#        avatar: info['cover_url'],
#        listens: stats['total_listens'],
#        loves: stats['total_loves'],
#        gifts: stats['total_gifts'],
#        record_by: SmuleSong.record_by_map(record_by).join(','),
#        record_by_ids: record_by_ids,
#        latlong: "#{owner['price']},#{owner['discount']}",
#      }
#    end
#
#    def get_songs(url, options)
#      allset    = []
#      offset    = 0
#      limit     = (options[:limit] || 10_000).to_i
#      first_day = Time.now - (options[:days] || 7).to_i * 24 * 3600
#      bar       = nil
#      unless options[:quiet]
#        bar = TTY::ProgressBar.new('Checking songs [:bar] :percent',
#                                   total: limit)
#      end
#      catch(:done) do
#        loop do
#          ourl = "#{url}?order=created&offset=#{offset}"
#          bar.log("url: #{ourl}") if bar && Plog.debug?
#          output = get_page_curl(ourl, raw: true)
#          if output == 'Forbidden'
#            sleep 2
#            next
#          end
#          begin
#            result = JSON.parse(output)
#          rescue JSON::ParserError => e
#            Plog.error(e)
#            break
#          end
#          slist = result['list']
#          slist.each do |info|
#            allset << _extract_info(info)
#            if Time.parse(info['created_at']) <= first_day
#              bar&.log("Created less than #{first_day}")
#              throw :done
#            end
#            throw :done if allset.size >= limit
#          end
#          offset = result['next_offset']
#          throw :done if offset < 0
#          bar&.advance(slist.size)
#        end
#      end
#      bar&.finish
#      allset
#    end
#
#    def get_favs(user)
#      Plog.info("Getting favorites for #{user}")
#      options = { limit: 500, days: 365 * 10 }
#      return get_songs("https://www.smule.com/#{user}/favorites/json", options)
#    end
#
#    def get_user_group(user, agroup)
#      result = []
#      offset = 0
#      url    = "https://www.smule.com/#{user}/#{agroup}/json?offset=#{offset}&limit=25"
#      loop do
#        begin
#          data = get_pagecurl(url, json: true)['list']
#        rescue JSON::ParserError => e
#          Plog.error(e)
#          break
#        end
#        break if data.size <= 0
#
#        offset += 25
#        Plog.dump(agroup: agroup, offset: offset)
#        result += data.map do |r|
#          {
#            name: r['handle'],
#            avatar: r['pic_url'],
#            account_id: r['account_id'],
#          }
#        end
#      end
#      Plog.dump_info(agroup: agroup, size: result.size)
#      result
#    end
#  end
#end
