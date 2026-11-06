# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Tests of the session expiry setting."""

    def test_default_value(self):
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.session_expire_time, 10)

    def test_value_is_saved_in_config_parameter(self):
        settings = self.env['res.config.settings'].create(
            {'session_expire_time': 25})
        settings.execute()
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                'restrict_logins.session_expire_time'), '25')

    def test_value_below_one_minute_is_refused(self):
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create(
                {'session_expire_time': 0})
