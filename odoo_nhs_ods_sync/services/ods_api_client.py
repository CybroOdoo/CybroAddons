# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
import time
from threading import Lock

_logger = logging.getLogger(__name__)

BASE_URL = 'https://directory.spineservices.nhs.uk/ORD/2-0-0'
DEFAULT_TIMEOUT = 30
RATE_LIMIT_PER_SEC = 5.0
MAX_RETRIES = 3


class OdsApiError(Exception):
    """Base exception class for all ODS API client errors."""
    pass

class OdsNotFoundError(OdsApiError):
    """Exception raised when an organization is not found (HTTP 404)."""
    pass


class OdsTransientError(OdsApiError):
    """Exception raised on server errors or transient request issues."""
    pass


class OdsAuthError(OdsApiError):
    """Exception raised on unauthorized or forbidden access (HTTP 401/403)."""
    pass


class OdsApiClient:
    """API Client to communicate with the Spine ODS REST API."""

    def __init__(self, env):
        """Initialise the ODS API client using configuration parameters."""
        self.env = env
        cp = env['ir.config_parameter'].sudo()
        self.base_url = cp.get_param('nhs_ods_sync.base_url', BASE_URL).rstrip('/')
        self.timeout = int(cp.get_param('nhs_ods_sync.timeout', str(DEFAULT_TIMEOUT)))
        self.rate = float(cp.get_param('nhs_ods_sync.rate_per_sec', str(RATE_LIMIT_PER_SEC)))
        self.contact = cp.get_param('nhs_ods_sync.contact_email', '')
        self._lock = Lock()
        self._last_call_ts = 0.0

    def _throttle(self):
        """Rate limit requests to conform to the specified rate limit per second."""
        with self._lock:
            elapsed = time.monotonic() - self._last_call_ts
            wait = max(0, (1.0 / self.rate) - elapsed)
            if wait:
                time.sleep(wait)
            self._last_call_ts = time.monotonic()

    def _headers(self):
        """Build HTTP request headers including User-Agent identification."""
        return {
            'Accept': 'application/json',
            'User-Agent': f'Odoo-NHS-ODS-Sync/1.0 (+{self.contact})',
        }

    def _request_with_retry(self, method, url, params=None):
        """Send HTTP request with automatic transient error retries and exponential backoff."""
        import requests
        backoff = [0.5, 1.0, 2.0]
        last_exc = None
        for attempt in range(MAX_RETRIES):
            self._throttle()
            try:
                resp = requests.request(
                    method, url,
                    params=params,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
                if resp.status_code == 404:
                    raise OdsNotFoundError(f"ODS 404 for {url}")
                if resp.status_code in (401, 403):
                    raise OdsAuthError(f"ODS auth error {resp.status_code} for {url}")
                if resp.status_code >= 500:
                    raise OdsTransientError(f"ODS server error {resp.status_code}")
                resp.raise_for_status()
                return resp
            except (OdsNotFoundError, OdsAuthError):
                raise
            except OdsTransientError as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(backoff[attempt])
            except Exception as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(backoff[attempt])
        raise OdsTransientError(f"ODS request failed after {MAX_RETRIES} retries: {last_exc}")

    def _next_link(self, payload):
        """Extract the next page link URL from the ODS response JSON payload."""
        links = payload.get('_links', {})
        nxt = links.get('next', {})
        if isinstance(nxt, dict):
            return nxt.get('href')
        return None

    def get_organisation(self, ods_code):
        """Fetch a single organization payload from ODS API or return mock for Scottish boards."""
        code_upper = ods_code.upper()
        if code_upper.startswith('S08') or code_upper.startswith('SCO-') or code_upper.startswith('S27'):
            board = self.env['nhs.health.board'].search([('code', '=', code_upper)], limit=1)
            if board:
                return {
                    'Organisation': {
                        'OrgId': {'extension': board.code},
                        'Name': board.name,
                        'Status': 'Active',
                        'Date': [{'Type': 'Operational', 'Start': '2000-01-01'}],
                        'Roles': {
                            'Role': [
                                {'id': 'RO140', 'primaryRole': True, 'Status': 'Active'}
                            ]
                        },
                        'LastChangeDate': '2026-06-11'
                    }
                }
        url = f'{self.base_url}/organisations/{code_upper}'
        resp = self._request_with_retry('GET', url)
        return resp.json()

    def search_organisations(self, **params):
        """Search for organisations matching specific primary roles or dates with pagination."""
        url = f'{self.base_url}/organisations'
        results = []
        query_params = {k: v for k, v in params.items() if v is not None}
        while url:
            resp = self._request_with_retry('GET', url, params=query_params)
            payload = resp.json()
            orgs = payload.get('Organisations', [])
            if isinstance(orgs, list):
                results.extend(orgs)
            elif isinstance(orgs, dict):
                results.append(orgs)
            url = resp.headers.get('Next-Page')
            query_params = None
        return results

    def ping(self):
        """Perform connection test probe to verify ODS API server availability and latency."""
        import time as _time
        try:
            t0 = _time.monotonic()
            self.get_organisation('RW1')
            latency_ms = int((_time.monotonic() - t0) * 1000)
            return True, latency_ms, 'OK'
        except OdsNotFoundError:
            return True, 0, 'OK (404 is expected for some codes)'
        except Exception as exc:
            return False, 0, str(exc)

