# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.ResConfigSettings = cls.env['res.config.settings']
        cls.email_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'email')
        ], limit=1)

    def test_set_and_get_values(self):
        # Create and set values
        settings = self.ResConfigSettings.create({
            'is_unique_contact': True,
            'unique_contact_ids': [(6, 0, self.email_field.ids)]
        })
        settings.set_values()

        # Check ir.config_parameter
        is_unique_contact = self.env['ir.config_parameter'].sudo().get_param(
            'duplicate_contact_details_alert.is_unique_contact')
        self.assertTrue(is_unique_contact, "is_unique_contact should be True")

        unique_contact_ids_param = self.env['ir.config_parameter'].sudo().get_param(
            'duplicate_contact_details_alert.unique_contact_ids')
        self.assertEqual(eval(unique_contact_ids_param), self.email_field.ids, "unique_contact_ids should match")

        # Get values
        new_settings = self.ResConfigSettings.create({})
        res = new_settings.get_values()
        
        self.assertTrue(res.get('is_unique_contact'), "is_unique_contact should be in get_values")
        self.assertEqual(res.get('unique_contact_ids')[0][2], self.email_field.ids, "unique_contact_ids should be in get_values")
