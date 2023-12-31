import atexit
import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

_logger = logging.getLogger(__name__)

class SDriver:
  def __init__(self, base_url, browser='firefox'):
    self.url     = base_url
    _logger.debug(f"Goto {self.url} using {browser}")
    self.browser = webdriver.Firefox()
    atexit.register(self.browser.quit)
    self.browser.get(self.url)
    time.sleep(1)

  def find_element(self, selector, index = 0):
    elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
    if index < 0:
      return elements

    if len(elements) <= index:
      _logger.error(f"Element {selector}[{index}] not found")
      return False
    return elements[index]

  def click(self, selector, wtime = 2, index = 0, move=False):
    _logger.debug(f"Click on {selector}[{index}]")
    if not (element := self.find_element(selector, index=index)):
      return False
    element.click()
    if wtime > 0:
      time.sleep(wtime)
    return True

  def type(self, selector, data, append=False):
    _logger.debug(f"Enter on {selector} - {data[0:19]}")
    elem = self.browser.find_element(By.CSS_SELECTOR, selector)
    if not append:
      elem.clear()
    elem.send_keys(data)

  def goto(self, path):
    if not path.startswith('http'):
      path = re.sub('^/', '', path)
      path = f"{self.url}/{path}" 
    _logger.debug(f"Goto {path}")
    self.browser.get(path)

#
#  def alert
#    @driver.switch_to.alert
#  end
#
#  def method_missing(method, *argv)
#    @driver.send(method.to_s, *argv)
#  end
#
#  def respond_to_missing?(_method)
#    True
#  end
#end
