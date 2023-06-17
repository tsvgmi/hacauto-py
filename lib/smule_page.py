from sel_page import SelPage

class SmulePage(SelPage):
  def __init__(self, driver):
    super().__init__(driver)

#  LOCATORS = {
#    sc_auto_play_off: 'div.sc-dsQDmV.bWqwJs',
#    sc_comment_close: 'div.sc-bSakgD.ccMbSJ',
#    sc_comment_open: 'div.sc-gILORG.iQzmBv',
#    sc_play_toggle: 'div.sc-bTmccw.fSDrYS svg path',
#    sc_song_menu: 'button.sc-gpxMCN.cGCDHp',
#    sc_heart: 'div.sc-gILORG.iQzmBv',
#
#    sc_favorite_toggle: 'li.sc-iLIByi.rLGZk',
#    sc_comment_text: 'div.sc-bPPhlf.bLuqb',
#    sc_play_time: 'span.sc-kDDrLX.bnygEQ',
#    sc_song_menu_text: 'span.sc-kDDrLX.XrXfW',
#    sc_song_note: 'p.sc-iJkHyd.etjGnv',
#    sc_oh_no: 'div.sc-gYMRRK.dJWJvi',
#
#    sc_finit: '.sc-tQuYZ.bnsezK',
#    sc_followers: '.sc-btIRyd.kdDvya',
#    sc_followings: '.sc-kDDrLX.bigqPT',
#    sc_fentry: 'div.sc-knuRna.idgPUg',
#
#    sc_notification: 'div.sc-dvwKko.fircjK a',
#  }.freeze
#
#  def speed_video(rate)
#    Plog.debug("Set play rate to #{rate}")
#    if (vid = (css('video')[0] || {})['id'])
#      execute_script("document.getElementById('#{vid}').playbackRate=#{rate}")
#    end
#  end
#
#  # Click an logical element on smule page
#  def _click_on(log_elem, options = {})
#    if (elem = LOCATORS[log_elem]).nil?
#      Plog.error "#{log_elem} not defined in Locators"
#      return false
#    end
#    index = options[:index] || 0
#    delay = options[:delay] || 2
#    unless clickit(elem, wait: delay, index: index, move: true)
#      Plog.error "Error clicking #{log_elem} => #{elem}"
#      return false unless options[:expose]
#
#      # Expose bug in sdriver - if I have to scroll, the 1st time element
#      # access would still fail
#      unless clickit(elem, index: index, move: true)
#        Plog.error "Error clicking #{elem}"
#        return false
#      end
#    end
#    refresh if delay > 0
#    true
#  end
#
#  def toggle_song_favorite(fav: true)
#    _click_on(:sc_song_menu, delay: 1)
#
#    locator = LOCATORS[:sc_favorite_toggle]
#    cval = (css("#{locator} svg path")[0] || {})[:fill]
#    return false unless cval
#
#    if fav && cval == '#FFCE42'
#      Plog.debug('Already fav, skip it')
#      find_element(:css, 'body').click
#      return false
#    elsif !fav && cval != '#FFCE42'
#      Plog.info('Already not-fav, skip it')
#      find_element(:css, 'body').click
#      return false
#    end
#    click_and_wait(locator, 1, 0)
#    find_element(:css, 'body').click
#    true
#  end
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
#  def add_song_tag(tags, sinfo = nil)
#    # Get the current note
#    snote = ''
#    if sinfo && (snote = sinfo[:message]).nil?
#      snote = sinfo[:message] = _song_note
#    end
#
#    osnote  = snote
#    newnote = snote
#    tags.each do |tag_t|
#      if sinfo
#        tag = sinfo[:created].strftime(tag_t)
#        newnote += " #{tag}" if snote !~ /#{tag}/
#      else
#        tag = Time.now.strftime(tag_t)
#        newnote += " #{tag}"
#      end
#    end
#
#    # Nothing change - just return
#    return true if osnote == newnote
#
#    _click_on(:sc_song_menu)
#
#    locator = LOCATORS[:sc_song_menu_text]
#    if page.css(locator).text !~ /Edit performance/
#      find_element(:xpath, '//html').click
#      return false
#    end
#
#    click_and_wait(locator, 1, 3)
#
#    type('textarea#message', newnote, append: false) # Enter tag
#    sinfo[:message] = newnote if sinfo
#    Plog.info("Setting note to: #{newnote}")
#    click_and_wait('input#recording-save')
#  end
#
#  def like_song(href = nil)
#    goto(href, 3) if href
#    elem = LOCATORS[:sc_heart]
#    raise "#{elem} not defined in Locators" unless elem
#
#    unless (fill = (css("#{elem} svg path")[0] || {})[:fill])
#      Plog.error("Like not found - #{elem}")
#      return false
#    end
#
#    if fill == '#FD286E'
#      Plog.error('Already starred')
#      return false
#    end
#    _click_on(:sc_heart, delay: 1)
#    true
#  end
#
#  # Get remaining play time of current song.
#  def _remain_time
#    play_locator = LOCATORS[:sc_play_time]
#    return nil if css(play_locator).size < 3
#
#    curtime   = css(play_locator)[1].text.split(':')
#    curtime_s = curtime[0].to_i * 60 + curtime[1].to_i
#
#    endtime   = css(play_locator)[2].text.split(':')
#    endtime_s = endtime[0].to_i * 60 + endtime[1].to_i
#
#    endtime_s - curtime_s
#  end
#
#  def _toggle_play(doplay: true, href: nil)
#    Plog.debug("Think play = #{doplay}")
#
#    play_locator = LOCATORS[:sc_play_time]
#    _click_on(:sc_play_toggle, delay: 0)
#    if doplay
#      if css(play_locator).size >= 3
#        sleep_round = 0
#        while true
#          remain = _remain_time
#          if remain && (remain > 0)
#            sdriver.navigate.refresh if href && (sleep_round > 5)
#            break
#          elsif sleep_round > 60
#            Plog.info 'Wait too long'
#            sdriver.navigate.refresh if href
#            break
#          elsif (msg = css(LOCATORS[:sc_oh_no]).text) == 'Oh, no!'
#            Plog.info "See Oh, no! message - [#{msg}]"
#            sdriver.navigate.refresh if href
#          end
#          Plog.debug("Waiting for time - #{sleep_round}")
#          sleep 2
#          sleep_round += 1
#          refresh
#        end
#      else
#        Plog.error("Can't see time element.  Just pause and guess")
#        sleep 2
#      end
#      _remain_time || 300
#    else
#      remain = 0
#    end
#    remain
#  end
#
#  # Play or pause song
#  def toggle_play(doplay: true, href: nil)
#    refresh
#    limit = 5
#    paths = nil
#
#    Plog.dump {{doplay: doplay}}
#    while limit > 0
#      paths = css(LOCATORS[:sc_play_toggle]).size
#      break if paths > 0
#
#      #_click_on(:sc_play_time, delay: 1)
#      sleep 1
#      limit -= 1
#    end
#    toggling = true
#    if doplay && paths == 2
#      Plog.debug("Already playing [#{paths}].  Do nothing [1]")
#      toggling = false
#    elsif !doplay && paths == 1
#      Plog.debug("Already stopped [#{paths}].  Do nothing [2]")
#      toggling = false
#    else
#      Plog.dump {{paths: paths}}
#    end
#    toggling ? _toggle_play(doplay: doplay, href: href) : 5
#  end
#
#  def comment_from_page
#    set_size = css(LOCATORS[:sc_comment_open]).size
#    _click_on(:sc_comment_open, index: set_size - 2, delay: 0.5)
#    res = []
#    css(LOCATORS[:sc_comment_text]).reverse.each do |acmt|
#      comment = acmt.text.split
#      user = comment[0]
#      msg  = (comment[1..] || []).join(' ')
#      res << [user, msg]
#    end
#    _click_on(:sc_comment_close, delay: 0)
#    res
#  end
#
#  def autoplay_off
#    _click_on(:sc_auto_play_off, expose: true)
#  end
#
#  def _song_note
#    locator = LOCATORS[:sc_song_note]
#    if css(locator).empty?
#      Plog.error("#{locator} not found (song note)")
#      ''
#    else
#      css(locator)[0].text
#    end
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
#    goto("https://www.smule.com/#{user}")
#    _click_on(:sc_finit, index: 1, delay: 0)
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
#    goto('https://www.smule.com/user/notifications')
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
