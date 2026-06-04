# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from unittest.mock import patch, MagicMock
from odoo.tests.common import HttpCase, TransactionCase
from odoo.tests import tagged

_CTRL_MODULE = (
    'odoo.addons.odoo_google_contact_integration'
    '.controllers.google_contact_integration'
)

def _mock_token_response(access_token='tok', expires_in=3600,
                         refresh_token='rtok', include_access=True):
    resp = MagicMock()
    data = {'expires_in': expires_in, 'refresh_token': refresh_token}
    if include_access:
        data['access_token'] = access_token
    resp.json.return_value = data
    return resp


# ---------------------------------------------------------------------------
# HttpCase  — pure HTTP checks (status codes, response body, call args)
# ---------------------------------------------------------------------------

@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestGoogleContactAuthController(HttpCase):
    """HTTP-level tests for /google_contact_authentication."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.write({
            'contact_client_id': 'ctrl-client-id',
            'contact_client_secret': 'ctrl-client-secret',
            'contact_redirect_uri':
                'http://localhost:8016/google_contact_authentication',
        })

    # ------------------------------------------------------------------
    # 1. Route accessibility
    # ------------------------------------------------------------------

    def test_route_returns_200_with_code(self):
        """GET /google_contact_authentication?code=... must return HTTP 200."""
        with patch('requests.post') as mock_post:
            mock_post.return_value = _mock_token_response()
            resp = self.url_open(
                '/google_contact_authentication?code=test_auth_code')
            self.assertEqual(resp.status_code, 200)

    def test_route_returns_200_without_code(self):
        """GET /google_contact_authentication with no code must return 200."""
        resp = self.url_open('/google_contact_authentication')
        self.assertEqual(resp.status_code, 200)

    # ------------------------------------------------------------------
    # 2. Response-body / mock call-args checks (no DB-state assertions)
    # ------------------------------------------------------------------

    @patch('requests.post')
    def test_auth_sends_code_in_payload(self, mock_post):
        """Controller must include the received code in the token POST."""
        mock_post.return_value = _mock_token_response()
        self.url_open(
            '/google_contact_authentication?code=payload_code_123')
        data_sent = mock_post.call_args[1].get('data', {})
        self.assertEqual(data_sent.get('code'), 'payload_code_123')

    @patch('requests.post')
    def test_auth_success_response_contains_success_message(self, mock_post):
        """Successful auth must return a body containing a success indication."""
        mock_post.return_value = _mock_token_response()
        resp = self.url_open(
            '/google_contact_authentication?code=good_code')
        body = resp.text.lower()
        self.assertTrue(
            'success' in body or 'authentication' in body,
            f"Response body did not mention success: {resp.text[:200]}"
        )

    # ------------------------------------------------------------------
    # 3. No code in callback
    # ------------------------------------------------------------------

    def test_no_code_does_not_update_tokens(self):
        """Callback without code must not change the company's token fields."""
        original_token = self.company.contact_company_access_token
        self.url_open('/google_contact_authentication')
        self.company.invalidate_recordset()
        self.assertEqual(self.company.contact_company_access_token,
                         original_token)

# ---------------------------------------------------------------------------
# TransactionCase  — DB-state checks via direct controller invocation
# ---------------------------------------------------------------------------

@tagged('post_install', '-at_install', 'odoo_google_contact_integration')
class TestGoogleContactAuthControllerDirect(TransactionCase):
    """DB-state tests for GoogleContactAuth.get_auth_code, called directly."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.write({
            'contact_client_id': 'ctrl-client-id',
            'contact_client_secret': 'ctrl-client-secret',
            'contact_redirect_uri':
                'http://localhost:8016/google_contact_authentication',
        })
        # Import once; the class is already registered in the router.
        from odoo.addons.odoo_google_contact_integration.controllers\
            .google_contact_integration import GoogleContactAuth
        self._ctrl = GoogleContactAuth()

    def _invoke(self, code=None, mock_response=None):
        """Call get_auth_code directly, injecting a fake Odoo request.
        """
        kw = {'code': code} if code else {}
        if mock_response is None:
            mock_response = _mock_token_response()

        fake_req = MagicMock()
        fake_req.uid = self.env.uid
        fake_req.env = self.env

        with patch(_CTRL_MODULE + '.request', fake_req), \
             patch(_CTRL_MODULE + '.http') as mock_http, \
             patch(_CTRL_MODULE + '.requests') as mock_requests:
            mock_http.request = fake_req
            mock_requests.post.return_value = mock_response
            result = self._ctrl.get_auth_code(**kw)

        return result


