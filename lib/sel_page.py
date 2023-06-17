from bs4 import BeautifulSoup

# A simple class to combine the Slenium and and Nokogiri parsing
# support.  selenim itself could do css parsing too but documentation
# is wanting ...
class SelPage:

  def __init__(self, sdriver):
    self.sdriver = sdriver
    self.clicks  = 0
    self.refresh()

  def refresh(self):
    self.page = BeautifulSoup(self.sdriver.browser.page_source, 'html.parser')
#
#  def find_and_click_links(lselector, rselector, options = {})
#    links = @page.css(lselector).map { |asong| asong['href'] }
#    click_links(links, rselector, options)
#  end
#
#  def click_links(links, rselector, options = {})
#    limit = (options[:limit] || 1000).to_i
#    return if links.size <= 0
#
#    Plog.info("Click #{links.size} links")
#    links.each do |link|
#      goto(link)
#      @sdriver.click_and_wait(rselector, 3)
#      @clicks += 1
#      break if @clicks >= limit
#    end
#  end
#
#  def goto(link, wait = 1)
#    @sdriver.goto(link)
#    sleep(wait)
#    refresh
#  end
#
#  def css(spec)
#    @page.css(spec)
#  end
#
#  def method_missing(method, *argv)
#    @sdriver.send(method.to_s, *argv)
#  end
#
#  def respond_to_missing?(_method)
#    true
#  end
#end
