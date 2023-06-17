import emoji
import logging
import re
import requests
import json as JS
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

def get_page_curl(url, ofile=None, json=False, raw=False):
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"
  }
  _logger.debug('Request from %s', url)
  resp = requests.get(url, headers=headers)
  if ofile:
    with open(ofile, 'wb') as f:
      f.write(resp.content)
    _logger.debug('Written to %s', ofile)
    return

  if raw:
    return resp.content
  if json:
    return JS.loads(resp.content)
  return BeautifulSoup(resp.content, 'html.parser')

def to_stitle(str):
  str    = clean_emoji(str)
  stitle = re.sub('\s+[-=(].*$', '', str).replace('"', '')
  stitle = normalize_vnaccent(stitle)
  stitle = re.sub('[^a-z0-9 ]', '', stitle.lower())
  stitle = re.sub('\s+', ' ', stitle)
  stitle.strip()

def clean_emoji(str):
  return re.sub(':[^:]+:', '', emoji.demojize(str))

ACCENT_MAP = {
  '[áàảãạâấầẩẫậăắằẳẵặ]': 'a',
  '[ÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶ]': 'A',
  'đ': 'd',
  'Đ': 'D',
  '[éèẻẽẹêếềểễệ]': 'e',
  '[ÉÈẺẼẸÊẾỀỂỄỆ]': 'E',
  '[íìỉĩị]': 'i',
  '[ÍÌỈĨỊ]': 'I',
  '[óòỏõọôốồổỗộơớờởỡợ]': 'o',
  '[ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]': 'O',
  '[úùủũụưứừửữự]': 'u',
  '[ÚÙỦŨỤƯỨỪỬỮỰ]': 'U',
  '[ýỳỷỹỵ]': 'y',
  '[ÝỲỶỸỴ]': 'Y',
}

def normalize_vnaccent(str):
  for ptn, rep in ACCENT_MAP.items():
    str = re.sub(ptn, rep, str)
  return str


