import time
import atexit
from site_connect import SiteConnect
from smule_page   import SmulePage

class Scanner:
  def __init__(self, user, options = {}):
    self.user      = user
    self.options   = options
    self.connector = SiteConnect('smule', self.options)
    self.spage     = SmulePage(self.connector.driver)
    time.sleep(1)
    atexit.register(self.connector.close)
    
#  def like_set(song_set, count)
#    stars = []
#    song_set.each do |sinfo|
#      href = sinfo[:href]
#      next if href =~ /ensembles$/
#      next if sinfo[:record_by].include?(@user)
#      next if Love.first(sid: sinfo[:sid], user: @user)
#
#      next if @options[:exclude]&.find { |r| sinfo[:record_by] =~ /#{r}/ }
#
#      begin
#        if @spage.like_song(sinfo[:href])
#          Plog.info("Marking #{sinfo[:stitle]} (#{sinfo[:record_by]})")
#          stars << sinfo
#          if @options[:pause]
#            sleep(1)
#            @spage.toggle_play(doplay: true)
#            sleep(@options[:pause])
#          end
#          count -= 1
#          break if count <= 0
#        end
#        Love.insert(sid: sinfo[:sid], user: @user, updated_at: Time.now)
#      rescue StandardError => e
#        Plog.error(e)
#      end
#    end
#    stars
#  end
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
