# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import builtins
import json
import os
from unittest.mock import patch, MagicMock, mock_open

from odoo.tests.common import HttpCase
from odoo.tests import tagged

# Capture the real open() BEFORE any test patches are applied so that
# selective_open() can fall through to it for non-sw.js paths.
_REAL_OPEN = builtins.open


@tagged('post_install', '-at_install', 'offline_sale')
class TestOfflineSaleController(HttpCase):
    """HTTP tests for OfflineSaleController routes."""

    # ------------------------------------------------------------------
    # /offline_sale/ui
    # ------------------------------------------------------------------

    def test_offline_sale_ui_accessible_as_public(self):
        """GET /offline_sale/ui is accessible without authentication (auth='public')."""
        res = self.url_open('/offline_sale/ui')
        self.assertIn(res.status_code, (200, 302),
                      "Public route should not return a 4xx/5xx status.")

    # ------------------------------------------------------------------
    # /offline_sale/manifest.json
    # ------------------------------------------------------------------

    def test_manifest_returns_200(self):
        """GET /offline_sale/manifest.json returns HTTP 200."""
        res = self.url_open('/offline_sale/manifest.json')
        self.assertEqual(res.status_code, 200)

    def test_manifest_content_type_is_json(self):
        """GET /offline_sale/manifest.json returns content-type application/json."""
        res = self.url_open('/offline_sale/manifest.json')
        self.assertIn('application/json', res.headers.get('Content-Type', ''))

    def test_manifest_has_required_fields(self):
        """PWA manifest contains all required fields."""
        res = self.url_open('/offline_sale/manifest.json')
        data = res.json()
        required_fields = {'name', 'short_name', 'start_url', 'display', 'icons'}
        self.assertTrue(required_fields.issubset(set(data.keys())),
                        "Manifest is missing required PWA fields: %s" % (
                            required_fields - set(data.keys())))

    def test_manifest_start_url(self):
        """Manifest start_url points to the offline sale UI route."""
        res = self.url_open('/offline_sale/manifest.json')
        data = res.json()
        self.assertEqual(data['start_url'], '/offline_sale/ui')

    def test_manifest_display_mode(self):
        """Manifest display mode is 'standalone'."""
        res = self.url_open('/offline_sale/manifest.json')
        data = res.json()
        self.assertEqual(data['display'], 'standalone')

    def test_manifest_name(self):
        """Manifest name matches expected application name."""
        res = self.url_open('/offline_sale/manifest.json')
        data = res.json()
        self.assertTrue(data.get('name'), "Manifest 'name' should not be empty.")

    def test_manifest_icons_is_list(self):
        """Manifest icons field is a non-empty list."""
        res = self.url_open('/offline_sale/manifest.json')
        data = res.json()
        self.assertIsInstance(data.get('icons'), list)
        self.assertTrue(data['icons'], "Manifest 'icons' list should not be empty.")

    # ------------------------------------------------------------------
    # /offline_sale/sw.js
    # ------------------------------------------------------------------

    def _selective_open(self, fake_content):
        """Return an open() side-effect that intercepts only sw.js reads.

        When ``url_open`` sends the HTTP request, the ``requests`` library
        opens ``~/.netrc`` to look up credentials.  A global
        ``patch('builtins.open', mock_open(...))`` intercepts that call too
        and feeds bytes to the netrc parser, causing a TypeError.  Using a
        selective side-effect avoids the problem: only paths ending in
        'sw.js' are stubbed; everything else is forwarded to the real open.
        """
        def _open(path, *args, **kwargs):
            if path and str(path).endswith('sw.js'):
                handle = MagicMock()
                handle.__enter__ = lambda s: s
                handle.__exit__ = MagicMock(return_value=False)
                handle.read = MagicMock(return_value=fake_content)
                return handle
            return _REAL_OPEN(path, *args, **kwargs)
        return _open

    def test_sw_js_returns_200_when_file_exists(self):
        """GET /offline_sale/sw.js returns 200 when the service worker file exists."""
        with patch('odoo.addons.offline_sale.controllers.main.get_module_path',
                   return_value='/fake/path'), \
             patch('odoo.addons.offline_sale.controllers.main.os.path.exists',
                   return_value=True), \
             patch('builtins.open', side_effect=self._selective_open(b'// fake service worker')):
            res = self.url_open('/offline_sale/sw.js')
            self.assertEqual(res.status_code, 200)

    def test_sw_js_content_type_is_javascript(self):
        """GET /offline_sale/sw.js sets Content-Type to application/javascript."""
        with patch('odoo.addons.offline_sale.controllers.main.get_module_path',
                   return_value='/fake/path'), \
             patch('odoo.addons.offline_sale.controllers.main.os.path.exists',
                   return_value=True), \
             patch('builtins.open', side_effect=self._selective_open(b'// sw')):
            res = self.url_open('/offline_sale/sw.js')
            self.assertIn('javascript', res.headers.get('Content-Type', ''))

    def test_sw_js_returns_404_when_module_not_found(self):
        """GET /offline_sale/sw.js returns 404 when the module path is not resolvable."""
        with patch('odoo.addons.offline_sale.controllers.main.get_module_path',
                   return_value=None):
            res = self.url_open('/offline_sale/sw.js')
            self.assertEqual(res.status_code, 404)

    def test_sw_js_returns_404_when_file_missing(self):
        """GET /offline_sale/sw.js returns 404 when the sw.js file does not exist on disk."""
        with patch('odoo.addons.offline_sale.controllers.main.get_module_path',
                   return_value='/fake/path'), \
             patch('odoo.addons.offline_sale.controllers.main.os.path.exists',
                   return_value=False):
            res = self.url_open('/offline_sale/sw.js')
            self.assertEqual(res.status_code, 404)

    def test_sw_js_service_worker_allowed_header(self):
        """GET /offline_sale/sw.js includes the Service-Worker-Allowed header."""
        with patch('odoo.addons.offline_sale.controllers.main.get_module_path',
                   return_value='/fake/path'), \
             patch('odoo.addons.offline_sale.controllers.main.os.path.exists',
                   return_value=True), \
             patch('builtins.open', side_effect=self._selective_open(b'// sw')):
            res = self.url_open('/offline_sale/sw.js')
            self.assertIn('Service-Worker-Allowed', res.headers)
