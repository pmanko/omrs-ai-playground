# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Connections to a FHIR Server."""

import os
import json
from typing import Dict, Union, Optional
import google.auth
import google.auth.transport.requests
import requests
import requests.adapters

FhirClient = Union['GcpClient', 'OpenMrsClient', 'HapiClient']


def _process_response(response: requests.Response) -> Dict[str, str]:
  # Handle non-2xx early with helpful diagnostics
  if response.status_code >= 400:
    raise ValueError(
        'Request to %s failed with code %s and response:\n%s' %
        (response.url, response.status_code, response.text)
    )
  # Some endpoints can return empty body on success; treat as empty JSON
  if not response.text:
    return {}
  try:
    return json.loads(response.text)
  except json.JSONDecodeError:
    raise ValueError(
        'Expected JSON but got non-JSON from %s (status %s):\n%s' %
        (response.url, response.status_code, response.text[:500])
    )


def _setup_session(base_url: str):
  session = requests.Session()
  retry = requests.adapters.Retry()
  adapter = requests.adapters.HTTPAdapter(max_retries=retry)
  session.mount(base_url, adapter)
  session.headers.update(
      {'Content-Type': 'application/fhir+json;charset=utf-8'})
  return session


class OpenMrsClient:
  """Client to connect to an OpenMRS Server."""

  def __init__(self, base_url: str):
    self.base_url = base_url
    self.session = _setup_session(self.base_url)
    # Optional basic auth via env if provided, default to OpenMRS dev creds
    username = os.environ.get('FHIR_USERNAME', 'admin')
    password = os.environ.get('FHIR_PASSWORD', 'Admin123')
    self.session.auth = (username, password)
    self.response = None

  def post_single_resource(self, resource: str, data: Dict[str, str]):
    url = f'{self.base_url}/{resource}'
    response_ = self.session.post(url, json.dumps(data))
    self.response = _process_response(response_)

  def get_resource(self, resource: str):
    url = f'{self.base_url}/{resource}'
    response_ = self.session.get(url)
    self.response = _process_response(response_)
    return self.response

  def find_patient_id_by_identifier(self, identifier_value: str) -> Optional[str]:
    """Searches for a Patient by identifier value and returns its id if found."""
    try:
      bundle = self.get_resource(f'Patient?identifier={identifier_value}')
      entries = bundle.get('entry', [])
      if entries:
        return entries[0]['resource']['id']
    except Exception:
      return None
    return None


class GcpClient:
  """Client to connect to GCP FHIR Store."""

  def __init__(self, base_url: str):
    self.base_url = base_url
    self.session = _setup_session(base_url)
    self._auth_req = google.auth.transport.requests.Request()
    self._creds, _ = google.auth.default()
    self.response = None

  def _add_auth_token(self):
    self._creds.refresh(self._auth_req)
    auth_dict = {'Authorization': f'Bearer {self._creds.token}'}
    self.session.headers.update(auth_dict)

  def post_bundle(self, data: Dict[str, str]):
    self._add_auth_token()
    response_ = self.session.post(self.base_url, json.dumps(data))
    self.response = _process_response(response_)

  def post_single_resource(self, resource: str, data: Dict[str, str]):
    self._add_auth_token()
    url = f'{self.base_url}/{resource}'
    response_ = self.session.post(url, json.dumps(data))
    self.response = _process_response(response_)

  def get_resource(self, resource: str):
    self._add_auth_token()
    url = f'{self.base_url}/{resource}'
    response_ = self.session.get(url)
    self.response = _process_response(response_)
    return self.response


class HapiClient(OpenMrsClient):
  """Client to connect to HAPI FHIR Server."""

  def __init__(self, base_url: str):
    super().__init__(base_url)
    # Allow override via env; default hapi/hapi
    username = os.environ.get('FHIR_USERNAME', 'hapi')
    password = os.environ.get('FHIR_PASSWORD', 'hapi')
    self.session.auth = (username, password)

  def post_bundle(self, data: Dict[str, str]):
    response_ = self.session.post(self.base_url, json.dumps(data))
    self.response = _process_response(response_)
