# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Request Handler for /main endpoint."""

__author__ = 'nnd@google.com (Niket Desai)'


import io
import jinja2
import logging
import os
import webapp2
import json
import urllib
import re


from google.appengine.api import memcache
from google.appengine.api import urlfetch

import httplib2
from apiclient import errors
from apiclient.http import MediaIoBaseUpload
from apiclient.http import BatchHttpRequest
from oauth2client.appengine import StorageByKeyName

from model import Credentials
import util


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class _BatchCallback(object):
  """Class used to track batch request responses."""

  def __init__(self):
    """Initialize a new _BatchCallbaclk object."""
    self.success = 0
    self.failure = 0

  def callback(self, request_id, response, exception):
    """Method called on each HTTP Response from a batch request.

    For more information, see
      https://developers.google.com/api-client-library/python/guide/batch
    """
    if exception is None:
      self.success += 1
    else:
      self.failure += 1
      logging.error(
          'Failed to insert item for user %s: %s', request_id, exception)


class MainHandler(webapp2.RequestHandler):
  """Request Handler for the main endpoint."""

  def _render_template(self, message=None):
    """Render the main page template."""
    template_values = {'userId': self.userid}
    if message:
      template_values['message'] = message
    # self.mirror_service is initialized in util.auth_required.
    try:
      template_values['contact'] = self.mirror_service.contacts().get(
        id='Python Quick Start').execute()
    except errors.HttpError:
      logging.info('Unable to find Python Quick Start contact.')

    timeline_items = self.mirror_service.timeline().list(maxResults=3).execute()
    template_values['timelineItems'] = timeline_items.get('items', [])

    subscriptions = self.mirror_service.subscriptions().list().execute()
    for subscription in subscriptions.get('items', []):
      collection = subscription.get('collection')
      if collection == 'timeline':
        template_values['timelineSubscriptionExists'] = True
      elif collection == 'locations':
        template_values['locationSubscriptionExists'] = True

    template = jinja_environment.get_template('templates/index.html')
    self.response.out.write(template.render(template_values))

  @util.auth_required
  def get(self):
    """Render the main page."""
    # Get the flash message and delete it.
    message = memcache.get(key=self.userid)
    memcache.delete(key=self.userid)
    self._render_template(message)

  @util.auth_required
  def post(self):
    """Execute the request and render the template."""
    operation = self.request.get('operation')
    # Dict of operations to easily map keys to methods.
    operations = {
        'sendHoroscopes': self.sendHoroscopes
    }
    if operation in operations:
      message = operations[operation]()
    else:
      message = "I don't know how to " + operation
    # Store the flash message for 5 seconds.
    memcache.set(key=self.userid, value=message, time=5)
    self.redirect('/')
  
  
  
  """ NIKET'S HOROSCOPE SHIT """
  
  def getHoroscopes(self):
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
    scopeBundle = []
    
    # Create and add first card template.
    body = {
        'notification': {'level': 'DEFAULT'},
        'bundleID' : '2718281828',
        'isBundleCover': True,
        "html": "<article class=\"photo\">\n  <img src=\"http://thechalkboardmag.com/wp-content/uploads/2013/02/astrology-wheel-zodiac-horoscope-january-2013.jpeg\" width=\"100%\">\n  <div class=\"photo-overlay\"/>\n  <section>\n    <p class=\"text-auto-size\">Today's Horoscopes</p>\n  </section>\n</article>\n",
    }
    scopeBundle.append(body)
    
    # Create remaining Horoscope Card Templates
    # and add to scopeBundle.
    for sign in horoscopes:
      body = {
          # 'notification': {'level': 'DEFAULT'},
          'bundleID' : '2718281828',
          'isBundleCover': False
      }
      message = """
                <article>\n
                  <section>\n
                    <p class=\"text-auto-size\">
                      %(horoscope)s
                    </p>\n
                  </section>\n
                  <footer>
                    %(sign)s
                  </footer>\n
                </article>\n
                """ % {'horoscope': horoscopes[sign], 'sign': sign}
      body['html'] = message
      scopeBundle.append(body)
    
    return scopeBundle
      
      
  def sendHoroscopes(self):
    """Insert timeline items."""
    logging.info('Inserting timeline item')
    
    horoscopes = self.getHoroscopes()
    scope_bundle = self.createHoroscopeBundle(horoscopes) 
    
    for body in scope_bundle:
      # self.mirror_service is initialized in util.auth_required.
      self.mirror_service.timeline().insert(body=body).execute()
      return  'A horoscope timeline bundle has been inserted.'
  

MAIN_ROUTES = [
    ('/', MainHandler)
]
