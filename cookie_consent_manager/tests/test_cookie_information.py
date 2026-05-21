# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C)2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Henna Mehjabin @cybrosys(odoo@cybrosys.com)
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCookieInformation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cookie_template = cls.env['cookie.information'].create({
            'template_title': 'Test Template',
            'pop_up_text': 'We use cookies',
            'cookie_color': 1,
            'accept_btn_txt': 'Accept',
            'reject_btn_txt': 'Reject',
            'cookie_policy_btn': 'Read More',
        })

    def test_cookie_information_creation(self):
        """Test cookie information record creation."""
        self.assertEqual(
            self.cookie_template.template_title,
            'Test Template'
        )
        self.assertEqual(
            self.cookie_template.pop_up_text,
            'We use cookies'
        )

    def test_get_color_valid(self):
        """Test valid cookie color mapping."""
        color = self.cookie_template._get_color(1)
        self.assertEqual(
            color,
            '#FF0000'
        )

    def test_get_color_invalid(self):
        """Test invalid cookie color mapping."""
        color = self.cookie_template._get_color(99)
        self.assertEqual(
            color,
            '#FFFFFF'
        )

    def test_res_config_settings_cookie_template(self):
        """Test cookie template configuration setting."""
        settings = self.env['res.config.settings'].create({
            'cookie_template_id': self.cookie_template.id,
        })
        settings.set_values()
        config_value = self.env[
            'ir.config_parameter'
        ].sudo().get_param(
            'cookie_consent_manager.cookie_template_id'
        )
        self.assertEqual(
            int(config_value),
            self.cookie_template.id
        )
