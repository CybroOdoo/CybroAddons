# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestGoogleTagManagerSettings(TransactionCase):
    """Test that the res.config.settings fields are correctly wired to
    their ir.config_parameter keys."""

    def test_fields_default_to_false(self):
        settings = self.env['res.config.settings'].create({})

        self.assertFalse(settings.google_tag_manager)
        self.assertFalse(settings.container_id)

    def test_saving_settings_persists_config_parameters(self):
        icp = self.env['ir.config_parameter'].sudo()

        settings = self.env['res.config.settings'].create({
            'google_tag_manager': True,
            'container_id': 'GTM-ABCDEF',
        })
        settings.execute()

        self.assertEqual(
            icp.get_param('google_tag_manager.google_tag_manager'), 'True')
        self.assertEqual(
            icp.get_param('google_tag_manager.container_id'), 'GTM-ABCDEF')

    def test_disabling_settings_clears_config_parameter(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('google_tag_manager.google_tag_manager', 'True')

        settings = self.env['res.config.settings'].create({
            'google_tag_manager': False,
        })
        settings.execute()

        self.assertFalse(
            icp.get_param('google_tag_manager.google_tag_manager'))


@tagged('-at_install', 'post_install')
class TestGoogleTagManagerLayout(HttpCase):
    """Test that the layout_inherit template correctly injects (or omits)
    the GTM script and noscript iframe based on the config parameters,
    which the template reads directly off `request.env` rather than
    through a controller - so this needs a real rendered page rather
    than a plain TransactionCase."""

    def _set_gtm(self, enabled, container_id=''):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('google_tag_manager.google_tag_manager', enabled)
        icp.set_param('google_tag_manager.container_id', container_id)

    def test_script_not_injected_when_disabled(self):
        self._set_gtm(False)

        html = self.url_open('/').text

        self.assertNotIn('googletagmanager.com/gtm.js', html)
        self.assertNotIn('googletagmanager.com/ns.html', html)

    def test_script_injected_with_container_id_when_enabled(self):
        self._set_gtm(True, 'GTM-TEST123')

        html = self.url_open('/').text

        # The gtm.js URL is built client-side via string concatenation,
        # so the container id shows up as the literal passed into the
        # IIFE rather than appended to the URL itself.
        self.assertIn('googletagmanager.com/gtm.js?id=', html)
        self.assertIn("'dataLayer','GTM-TEST123');", html)
        # The noscript iframe src is rendered server-side, so the id is
        # inlined directly into the URL.
        self.assertIn(
            'googletagmanager.com/ns.html?id=GTM-TEST123', html)
        self.assertIn('<noscript>', html)

    def test_noscript_iframe_is_hidden(self):
        self._set_gtm(True, 'GTM-TEST123')

        html = self.url_open('/').text

        self.assertIn('style="display:none;visibility:hidden"', html)

    def test_script_injected_with_empty_id_when_container_id_not_set(self):
        self._set_gtm(True, container_id='')

        html = self.url_open('/').text

        self.assertIn('googletagmanager.com/gtm.js?id=', html)
        self.assertIn("'dataLayer','');", html)
        self.assertIn('googletagmanager.com/ns.html?id=', html)

    def test_disabling_after_enabling_removes_the_script(self):
        self._set_gtm(True, 'GTM-TEST123')
        self.assertIn(
            'googletagmanager.com/gtm.js', self.url_open('/').text)

        self._set_gtm(False, 'GTM-TEST123')

        html = self.url_open('/').text
        self.assertNotIn('googletagmanager.com/gtm.js', html)
        self.assertNotIn('googletagmanager.com/ns.html', html)
