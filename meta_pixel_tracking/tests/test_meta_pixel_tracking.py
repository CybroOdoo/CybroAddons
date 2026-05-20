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
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.tests.common import TransactionCase


class TestMetaPixelTracking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref('website.default_website')
        cls.ir_config_parameter = cls.env['ir.config_parameter'].sudo()
        cls.render_template = cls.env['ir.ui.view'].create({
            'name': 'meta pixel tracking test page',
            'type': 'qweb',
            'key': 'meta_pixel_tracking.test_page',
            'arch_db': '''
                <t t-name="meta_pixel_tracking.test_page">
                    <t t-call="web.layout">
                        <div id="wrap">
                            <div class="oe_structure"/>
                        </div>
                    </t>
                </t>
            ''',
        })

    def setUp(self):
        super().setUp()
        self.ir_config_parameter.set_param('meta_pixel_tracking.meta_tracking', False)
        self.ir_config_parameter.set_param('meta_pixel_tracking.pixel_id', False)

    def _render_page(self):
        with MockRequest(self.env, website=self.website):
            return str(
                self.env['ir.qweb']._render(
                    self.render_template.id,
                    website_id=self.website.id,
                )
            )

    def test_settings_persist_values_in_namespaced_parameters(self):
        settings = self.env['res.config.settings'].create({
            'meta_tracking': True,
            'pixel_id': ' 1234567890 ',
        })

        settings.execute()

        self.assertEqual(
            self.ir_config_parameter.get_param('meta_pixel_tracking.meta_tracking'),
            'True',
        )
        self.assertEqual(
            self.ir_config_parameter.get_param('meta_pixel_tracking.pixel_id'),
            '1234567890',
        )

        new_settings = self.env['res.config.settings'].create({})
        self.assertTrue(new_settings.meta_tracking)
        self.assertEqual(new_settings.pixel_id, '1234567890')

    def test_onchange_clears_pixel_id_when_tracking_disabled(self):
        settings = self.env['res.config.settings'].new({
            'meta_tracking': True,
            'pixel_id': '1234567890',
        })

        settings.meta_tracking = False
        settings._onchange_meta_tracking()

        self.assertEqual(settings.pixel_id, '')

    def test_pixel_template_renders_only_when_tracking_enabled(self):
        self.ir_config_parameter.set_param('meta_pixel_tracking.meta_tracking', True)
        self.ir_config_parameter.set_param('meta_pixel_tracking.pixel_id', '1234567890')

        rendered = self._render_page()

        self.assertIn("fbq('track', 'PageView');", rendered)
        self.assertIn("fbq('init', myVariable);", rendered)
        self.assertIn('https://www.facebook.com/tr?id=1234567890&amp;ev=PageView&amp;noscript=1', rendered)

    def test_pixel_template_is_hidden_when_tracking_disabled(self):
        self.ir_config_parameter.set_param('meta_pixel_tracking.meta_tracking', False)
        self.ir_config_parameter.set_param('meta_pixel_tracking.pixel_id', '1234567890')

        rendered = self._render_page()

        self.assertNotIn("fbq('track', 'PageView');", rendered)
        self.assertNotIn('https://www.facebook.com/tr?id=1234567890&amp;ev=PageView&amp;noscript=1', rendered)
