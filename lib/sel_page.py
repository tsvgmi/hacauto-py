import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

# A simple class to combine the Slenium and and Nokogiri parsing
# support.  selenim itself could do css parsing too but documentation
# is wanting ...
class SelPage:

  def __init__(self, sdriver):
    self.sdriver = sdriver
    self.refresh()

  def refresh(self):
    self.page = BeautifulSoup(self.sdriver.browser.page_source, 'html.parser')

  def goto(self, link, wait=1):
    self.sdriver.goto(link)
    time.sleep(wait)
    self.refresh()

  def css(self, spec):
    return self.page.css(spec)


#
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
#    end
#  end
#
#
#  def method_missing(method, *argv)
#    @sdriver.send(method.to_s, *argv)
#  end
#
#  def respond_to_missing?(_method)
#    true
#  end
#end
