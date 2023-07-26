import logging
import datetime as DT

from sel_page import SelPage

_logger = logging.getLogger(__name__)

LOCATORS = {
  'sc_auto_play_off':   'div.sc-dsQDmV.bWqwJs',
  'sc_comment_close':   'div.sc-bSakgD.ccMbSJ',
  'sc_comment_open':    'div.sc-gILORG.iQzmBv',
  'sc_play_toggle':     'div.sc-bTmccw.fSDrYS svg path',
  'sc_song_menu':       'button.sc-gpxMCN.cGCDHp',
  'sc_heart':           'div.sc-gILORG.iQzmBv',

  'sc_favorite_toggle': 'li.sc-iLIByi.rLGZk',
  'sc_comment_text':    'div.sc-bPPhlf.bLuqb',
  'sc_play_time':       'span.sc-kDDrLX.bnygEQ',
  'sc_song_menu_text':  'span.sc-kDDrLX.XrXfW',
  'sc_song_note':       'p.sc-iJkHyd.etjGnv',
  'sc_oh_no':           'div.sc-gYMRRK.dJWJvi',

  'sc_finit':           '.sc-tQuYZ.bnsezK',
  'sc_followers':       '.sc-btIRyd.kdDvya',
  'sc_followings':      '.sc-kDDrLX.bigqPT',
  'sc_fentry':          'div.sc-knuRna.idgPUg',

  'sc_notification':    'div.sc-dvwKko.fircjK a',
}

class SmulePage(SelPage):
  def __init__(self, driver):
    super().__init__(driver)

  def like_song(self, href = None):
    if href:
      self.goto(href, wait=3)

    elem = LOCATORS['sc_heart']

    fill = self.sdriver.find_element(f"{elem} svg path").get_attribute('fill')
    if not fill:
      _logger.error(f"Like not found - {elem}")
      return False

    if fill == '#FD286E':
      _logger.error('Already liked')
      return False

    self._click_on('sc_heart', wtime=1)
    return True

  def _click_on(self, log_elem, index=0, wtime=2, expose=False):
    """Click an logical element on smule page"""

    if log_elem not in LOCATORS:
      _logger.error(f"{log_elem} not defined in Locators")
      return False
    
    elem = LOCATORS[log_elem]
    if not self.sdriver.click(elem, wtime=wtime, index=index, move=True):
      _logger.error(f"Error clicking {log_elem} => {elem}")
      if not expose:
        return False

      if not self.sdriver.click(elem, index=index, move=True):
        _logger.error(f"Error clicking {elem}")
        return False

    if wtime > 0:
      self.refresh()
    return True

  def toggle_play(self, doplay=True, href=None):
    """ Play or pause song"""
    self.refresh()
    limit = 5
    paths = 0

    _logger.debug(repr({"doplay": doplay}))
    while limit > 0:
      paths = self.sdriver \
          .find_element(LOCATORS['sc_play_toggle'], index=-1)
      pathsize = len(paths)
      if pathsize > 0:
        break

      time.sleep(1)
      limit -= 1
    
    toggling = True
    if doplay and (pathsize == 2):
      _logger.debug(f"Already playing [{pathsize}].  Do nothing [1]")
      toggling = False
    elif not doplay and (pathsize == 1):
      _logger.debug(f"Already stopped [{pathsize}].  Do nothing [2]")
      toggling = False
    else:
      _logger.debug(repr({"pathsize": pathsize}))
    
    return self._toggle_play(doplay=doplay, href=href) if toggling else 5

  def _toggle_play(self, doplay=True, href=None):
    _logger.debug(f"Think play = {doplay}")

    play_locator = LOCATORS['sc_play_time']
    self._click_on('sc_play_toggle', wtime=0)
    if doplay:
      if len(self.sdriver.find_element(play_locator, index=-1)) >= 3:
        sleep_round = 0
        while True:
          remain = self._remain_time()
          if remain and (remain > 0):
            if href and (sleep_round > 5):
              sdriver.navigate.refresh()
            break
          elif sleep_round > 60:
            _logger.info('Wait too long')
            if href:
              self.refresh()
            break
          elif (msg := self.sdriver.find_element(LOCATORS['sc_oh_no']).text) == 'Oh, no!':
            _logger.info(f"See Oh, no! message - [{msg}]")
            if href:
              self.refresh()
          
          _logger.debug(f"Waiting for time - {sleep_round}")
          time.sleep(2)
          sleep_round += 1
          self.refresh()
        
      else:
        _logger.error(f"Can't see time element.  Just pause and guess")
        time.sleep(2)
      
      remain = self._remain_time()
      if not remain:
        remain = 300

    else:
      remain = 0
    
    return remain
 
  def _remain_time(self):
    """ Get remaining play time of current song."""
    play_locator = LOCATORS['sc_play_time']
    if len(self.sdriver.find_element(play_locator, index=-1)) < 3:
      return nil

    curtime   = self.sdriver.find_element(play_locator, index=1).text.split(':')
    curtime_s = int(curtime[0])*60 + int(curtime[1])

    endtime   = self.sdriver.find_element(play_locator, index=2).text.split(':')
    endtime_s = int(endtime[0])*60 + int(endtime[1])

    return (endtime_s - curtime_s)
 
  def toggle_song_favorite(self, fav = True):
    self._click_on('sc_song_menu', wtime = 1)

    locator = LOCATORS['sc_favorite_toggle']

    cval = self.sdriver.find_element(f"{locator} svg path").get_attribute('fill')
    if not cval:
      _logger.error(f"Like not found - {locator}")
      return False

    rcode = False
    if fav and (cval == '#FFCE42'):
      _logger.debug('Already fav, skip it')
    elif (not fav) and (cval != '#FFCE42'):
      _logger.info('Already not-fav, skip it')
    else:
      self.sdriver.click(locator, wtime=1)
      rcode = True

    self.sdriver.click('body', wtime=0)
    return rcode

  def _song_note(self):
    locator = LOCATORS['sc_song_note']
    elem = self.sdriver.find_element(locator)
    if not elem:
      _logger.error(f"{locator} not found (song note)")
      return ''
    return elem.text

  def add_song_tag(self, tags, sinfo = None):
    # Get the current note
    oldnote = sinfo['message'] = self._song_note()
    newnote = oldnote
    for tag_t in tags:
      tag = sinfo['created'].strftime(tag_t)
      if tag not in oldnote:
        newnote += f" {tag}"

    # Nothing change - just return
    if oldnote == newnote:
      return True

    self._click_on('sc_song_menu')

    locator = LOCATORS['sc_song_menu_text']
    if 'Edit performance' not in self.sdriver.find_element(locator, index=3).text:
      self.sdriver.click('body', wtime=0)
      return False

    self.sdriver.click(locator, wtime=1, index=3)

    self.sdriver.type('textarea#message', newnote)
    sinfo['message'] = newnote
    _logger.info(f"Setting note to: {newnote}")
    self.sdriver.click('input#recording-save')
    return True

#
#  def speed_video(rate)
#    Plog.debug("Set play rate to #{rate}")
#    if (vid = (css('video')[0] || {})['id'])
#      execute_script("document.getElementById('#{vid}').playbackRate=#{rate}")
#    end
#  end
#
#
#  def add_any_song_tag(user, sinfo = nil, _options = {})
#    return unless sinfo
#
#    tagset = []
#    if sinfo && sinfo[:isfav]
#      toggle_song_favorite(fav: true)
#      tagset << '#thvfavs_%y'
#    elsif !sinfo[:record_by] || !sinfo[:record_by].start_with?(user)
#      return
#    end
#
#    if sinfo[:song_info_url]
#      tagset += SongInfo.get_tags(sinfo[:song_info_url], :smule_tag)
#                        .map { |f| "##{f}" }
#    end
#
#    if (sinfo[:record_by] == user) &&
#       (sinfo[:created] < Time.now - 8 * 24 * 3600)
#      tagset << '#thvopen_%y'
#    end
#    if sinfo[:record_by] == "#{user},#{user}" &&
#       (!sinfo[:message] || !sinfo[:message].include?('#thvduets'))
#      tagset << '#thvduets'
#    end
#    return unless tagset.size > 0
#
#    add_song_tag(tagset, sinfo)
#  end
#
#  def comment_from_page
#    set_size = css(LOCATORS[:sc_comment_open]).size
#    self._click_on(:sc_comment_open, index: set_size - 2, delay: 0.5)
#    res = []
#    css(LOCATORS[:sc_comment_text]).reverse.each do |acmt|
#      comment = acmt.text.split
#      user = comment[0]
#      msg  = (comment[1..] || []).join(' ')
#      res << [user, msg]
#    end
#    self._click_on(:sc_comment_close, delay: 0)
#    res
#  end
#
#  def autoplay_off
#    self._click_on(:sc_auto_play_off, expose: true)
#  end
#
#  def _collect_fgroup(tab_css, gname)
#    find_elements(:css, tab_css)[0].click
#    sleep(0.5)
#    # Do this but for the subwindow though
#
#    osize = 0
#    ent_css = LOCATORS[:sc_fentry]
#    progress_set((1..100).to_a, gname) do |i, _bar|
#      execute_script("document.getElementsByClassName('sc-djvmMF ebukrc')[0].scrollTo(0,#{i * 1000})")
#      sleep(0.5)
#      rcode = true
#      if (i % 5) == 0
#        refresh
#        nsize = page.css(ent_css).size
#        if nsize == osize
#          rcode = false
#        else
#          osize = nsize
#        end
#      end
#      rcode
#    end
#
#    result = page.css(ent_css).map do |r|
#      r.text.sub(/^.*@/, '').sub(/(Follow|Following)$/, '')
#    end
#
#    Plog.dump {{result:}}
#    result
#  end
#
#  def collect_followers(user)
#    self.goto("https://www.smule.com/#{user}")
#    self._click_on(:sc_finit, index: 1, delay: 0)
#
#    sleep(0.5)
#    followers  = _collect_fgroup(LOCATORS[:sc_followers], :followers)
#    followings = _collect_fgroup(LOCATORS[:sc_followings], :followings)
#
#    navigate.back
#    [followers, followings]
#  end
#
#  def songs_from_notification
#    self.goto('https://www.smule.com/user/notifications')
#    selector = LOCATORS[:sc_notification]
#    links    = css(selector).select {|r| r[:href] =~ /sing-recording/}
#                  .map {|r| "https://www.smule.com#{r[:href]}" }
#                  .uniq
#    navigate.back
#    Plog.info("Picked up #{links.size} songs from notification")
#  end
#end
#end
#    links
