# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestHoverRelatedFields(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestHoverRelatedFields, cls).setUpClass()
        # Find res.partner model
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.field_email = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'email')
        ], limit=1)
        cls.field_phone = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.partner_model.id),
            ('name', '=', 'phone')
        ], limit=1)

        # Create a test partner
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Test Partner Client',
            'email': 'testpartner@example.com',
            'phone': '9876543210',
        })

        # Find res.users model
        cls.users_model = cls.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
        cls.field_login = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.users_model.id),
            ('name', '=', 'login')
        ], limit=1)

        # Create a test user linked to the test partner
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuserlogin',
            'partner_id': cls.test_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

    def test_01_create_config(self):
        """Test simple creation of hover related fields configuration and computed model_ids"""
        config = self.env['hover.related.fields'].create({
            'model_id': self.partner_model.id,
            'field_ids': [(6, 0, [self.field_email.id, self.field_phone.id])],
        })
        self.assertTrue(config.active, "Configuration should be active by default")
        self.assertEqual(config.model_id, self.partner_model, "Model should be res.partner")
        self.assertIn(self.field_email, config.field_ids, "Email field should be in configured fields")
        self.assertIn(self.field_phone, config.field_ids, "Phone field should be in configured fields")

        # Check computed field model_ids
        config._compute_model_ids()
        self.assertIn(self.partner_model.id, config.model_ids.ids, "Configured model should be in model_ids")

    def test_02_finding_the_data_to_show_tooltip(self):
        """Test the finding_the_data_to_show_tooltip method"""
        # Create configuration for res.partner
        self.env['hover.related.fields'].create({
            'model_id': self.partner_model.id,
            'field_ids': [(6, 0, [self.field_email.id, self.field_phone.id])],
        })

        info = {
            'resModel': 'res.users',
            'resId': self.test_user.id,
            'field': {
                'name': 'partner_id',
                'relation': 'res.partner'
            }
        }

        data = self.env['hover.related.fields'].finding_the_data_to_show_tooltip(info)
        self.assertTrue(data, "Should return configured fields data")
        self.assertEqual(len(data), 2, "Should return data for the 2 configured fields")

        email_data = next((item for item in data if item['field_name'] == 'email'), None)
        phone_data = next((item for item in data if item['field_name'] == 'phone'), None)

        self.assertIsNotNone(email_data)
        self.assertEqual(email_data['value'], 'testpartner@example.com')
        self.assertEqual(email_data['field'], self.field_email.field_description)

        self.assertIsNotNone(phone_data)
        self.assertEqual(phone_data['value'], '9876543210')
        self.assertEqual(phone_data['field'], self.field_phone.field_description)

    def test_03_finding_the_data_to_show_tooltip_many2many(self):
        """Test finding_the_data_to_show_tooltip_many2many method"""
        # Create configuration for res.partner
        self.env['hover.related.fields'].create({
            'model_id': self.partner_model.id,
            'field_ids': [(6, 0, [self.field_email.id, self.field_phone.id])],
        })

        info = {
            'field': {
                'relation': 'res.partner'
            },
            'related_record_id': self.test_partner.id,
            'viewMode': 'form'
        }

        data = self.env['hover.related.fields'].finding_the_data_to_show_tooltip_many2many(info)
        self.assertTrue(data, "Should return configured fields data")
        self.assertEqual(len(data), 2, "Should return data for the 2 configured fields")

        email_data = next((item for item in data if item['field_name'] == 'email'), None)
        self.assertEqual(email_data['value'], 'testpartner@example.com')

    def test_04_finding_the_data_to_show_tooltip_many2many_no_config(self):
        """Test when no configuration exists and viewMode is list"""
        info = {
            'field': {
                'relation': 'res.partner'
            },
            'related_record_id': self.test_partner.id,
            'viewMode': 'list'
        }

        # Clear any existing configurations to ensure no config exists for res.partner
        self.env['hover.related.fields'].search([]).unlink()

        data = self.env['hover.related.fields'].finding_the_data_to_show_tooltip_many2many(info)
        self.assertEqual(data, self.test_partner.display_name, "Should return the display name of the record")
