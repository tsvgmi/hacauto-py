import logging
import yaml
import time

from sdriver import SDriver

_logger = logging.getLogger(__name__)

class SiteConnect:
  def __init__(self, site):
    _logger.info(f"Connect to site: {site}")
    with open('etc/access.yml') as fid:
      config = yaml.safe_load(fid)[site]

    self.driver = SiteConnect.connect_smule(config)

  def close(self):
    self.driver.close()
  
  def connect_smule(config):
    sdriver = SDriver(config['url'])
    sdriver.goto('/user/login')
    identity, password = config['auth'].split(':')
    time.sleep(3)

    sdriver.click('div.sc-jmNpzm.jEZoYe', wtime=1, index=2)
    sdriver.type('input[name="snp-username"]', f"{identity}\n")
    time.sleep(3)
    sdriver.type('input[name="snp-password"]', f"{password}\n")
    
    time.sleep(1)
    sdriver.click('button.sc-hAsxaJ', wtime=1)
    return sdriver

#  def connect_hac(options)
#    auth = options[:auth]
#    identity, password = auth.split(':')
#    sdriver = SDriver.new(options[:url], user: identity,
#                                         browser: options[:browser],
#                                         verbose: options[:verbose])
#    sdriver.click('#login-link', wtime=5)
#    sdriver.type('#identity', identity)
#    sdriver.type('#password', password)
#    sdriver.click('#submit-btn')
#    sdriver
#  end
#
#  def connect_gmusic(options)
#    auth = options[:auth]
#    identity, password = auth.split(':')
#    sdriver = SDriver.new(options[:url], user: identity,
#                                         browser: options[:browser],
#                                         verbose: options[:verbose])
#    sdriver.click('paper-button[data-action="signin"]')
#    sdriver.type('#identifierId', "#{identity}\n")
#    sdriver.type('input[name="password"]', "#{password}\n")
#
#    warn 'Confirm authentication on cell phone and continue'
#    $stdin.gets
#    sdriver
#  end
#
#  def connect_singsalon(options)
#    sdriver = SDriver.new('https://sing.salon', options)
#    if !options[:skip_auth] && !(auth = options[:auth]).nil?
#      identity, password = auth.split(':')
#      sdriver.click('#elUserSignIn')
#      sdriver.type('input[name="auth"]', "#{identity}\n")
#      sdriver.type('input[name="snp-password"]', "#{password}\n")
#      # sdriver.click('#elSignIn_submit')
#    end
#    sdriver
#  end
#
#  def connect_other(options)
#    SDriver.new(options[:url], options)
#  end
#
#
#end
