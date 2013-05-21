#  Module: horoscopes.py
#  Author: Niket Desai
#  Date:   2013.05.21

# Author
__author__ = 'nnd@google.com (Niket Desai)'

# Imports
import logging
import json
import urllib
import re

def getHoroscopes(self):
  """ Fetches Horoscope Information.
      
      Retrieves horoscope daily summaries from shine.yahoo.com
      and returns a dictionary of sign / horoscope key value pairs.
  
      Args:
          None
      
      Returns:
          String sign horoscope key value pairs.
          
          { 
            'leo' : 'Today is a good day to go outside and enjoy the number 2',
            'virgo' : 'Eat apples today, the doctor is coming'
            
            ... 
          }
  """

  scopes = ('aries', 'taurus', 'gemini', 'cancer', 
            'leo', 'virgo', 'libra', 'scorpio',
            'sagittarius', 'capricorn', 'aquarius', 'pisces')
  horoscopes = {}
  url = 'http://shine.yahoo.com/horoscope/'
  
  for scope in scopes:
    scope_url = url + scope + '/'
    url_file = urllib.urlopen(scope_url)
    contents = url_file.read()
    horoscopes[scope] = re.search('<div class="astro-tab-body">(.*)</div></div></div></div></div></div>', contents).group(1)
    
  return horoscopes



def createHoroscopeBundle(self, horoscopes):
  """ Creates Horoscope Glass Card Bundle.
      
      Retrieves horoscope daily summaries from shine.yahoo.com
      and returns a dictionary of sign / horoscope key value pairs.
  
      Args:
          horoscopes: Dictionary of sign/horoscope key value pairs.
      
      Returns:
          JSON formatted Glass Template object.
          {  
            'notification': {'level': 'DEFAULT'},
            'html': "<article><p>Some HTML</p></article>",
            'htmlPages' : []
          }
  """
  body = {
      'notification': {'level': 'DEFAULT'},
      'html': "<article class='photo'><img src='http://thechalkboardmag.com/wp-content/uploads/2013/02/astrology-wheel-zodiac-horoscope-january-2013.jpeg' width='100%'><div class='photo-overlay'/><section><p class='text-auto-size'>Today's Horoscopes</p></section></article>",
  }
  
  # Create remaining Horoscope Card Templates
  # and add to scopeBundle.
  body['htmlPages'] = []
  for sign in horoscopes:
    message = "<article><section><p class='text-auto-size'> %(horoscope)s </p></section><footer> %(sign)s </footer></article>" % {'horoscope': horoscopes[sign], 'sign': sign}
    body['htmlPages'].append(message)
  
  return body