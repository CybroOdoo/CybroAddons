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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    def test_set_get_values(self):
        """Test setting and getting LinkedIn recruitment configuration parameters."""
        config = self.env['res.config.settings'].create({
            'li_username': 'linkedin_user',
            'li_password': 'linkedin_secret_password',
        })
        config.set_values()
        
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('recruitment.li_username'),
            'linkedin_user'
        )
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param('recruitment.li_password'),
            'linkedin_secret_password'
        )

        values = config.get_values()
        self.assertEqual(values.get('li_username'), 'linkedin_user')
        self.assertEqual(values.get('li_password'), 'linkedin_secret_password')
