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
import horoscopes


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
  
  def sendHoroscopes(self):
    """Insert timeline items."""
    logging.info('Attempting to push horoscopes.')
    
    scopes = horoscopes.getHoroscopes(self)
    body   = horoscopes.createHoroscopeBundle(self, scopes) 
    
    self.mirror_service.timeline().insert(body=body).execute()
    return  'Houston, we have horoscopes. Check your Glass Device to confirm.'


class UpdateHoroscopesHandler(webapp2.RequestHandler):
  """Request Handler for the cron job that updates horoscopes."""
  
  def _render_template(self):
      """Render the update page template."""
      template = jinja_environment.get_template('templates/update.html')
      self.response.out.write(template.render())
  
  def get(self):
    """Insert a timeline item to all authorized users."""
    logging.info('Inserting horoscopes item to all users')
    users = Credentials.all()
    total_users = users.count()
    
    scopes = horoscopes.getHoroscopes(self)
    body   = horoscopes.createHoroscopeBundle(self, scopes) 
    
    for user in users:
      creds = StorageByKeyName(
          Credentials, user.key().name(), 'credentials').get()
      mirror_service = util.create_service('mirror', 'v1', creds)
      mirror_service.timeline().insert(body=body).execute()
        
    self._render_template()
    

MAIN_ROUTES = [
    ('/', MainHandler),
    ('/update', UpdateHoroscopesHandler)
]
