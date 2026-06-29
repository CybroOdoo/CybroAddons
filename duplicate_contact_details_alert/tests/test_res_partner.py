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
from odoo.exceptions import ValidationError


@tagged('-at_install', 'post_install')
class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.email_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'email')
        ], limit=1)
        cls.phone_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'phone')
        ], limit=1)

    def setUp(self):
        super().setUp()
        # Clean config params before each test
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', '[]')

    def test_01_duplicate_contact_creation_without_config(self):
        # Should not raise any error
        partner1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'test@example.com'
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'test@example.com'
        })
        self.assertTrue(partner1.id and partner2.id)

    def test_02_duplicate_contact_creation_with_config(self):
        # Set config to check email
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids))

        # Create first partner
        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'unique@example.com'
        })

        # Create second partner with same email should fail
        with self.assertRaises(ValidationError) as e:
            self.env['res.partner'].create({
                'name': 'Test Partner 2',
                'email': 'unique@example.com'
            })
        self.assertIn("Duplicate contact details were found", str(e.exception))

    def test_03_duplicate_contact_write_with_config(self):
        # Set config to check email
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids))

        # Create first partner
        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'write1@example.com'
        })

        # Create second partner
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'write2@example.com'
        })

        # Update second partner with first partner's email should fail
        with self.assertRaises(ValidationError) as e:
            partner2.write({
                'email': 'write1@example.com'
            })
        self.assertIn("Duplicate contact details were found", str(e.exception))

    def test_04_write_same_value(self):
        # Set config to check email
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids))

        # Create partner
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'same@example.com'
        })

        # Updating other fields should not raise error, even if email is in vals
        partner.write({
            'name': 'Updated Test Partner',
            'email': 'same@example.com'
        })
        self.assertEqual(partner.name, 'Updated Test Partner')

    def test_05_multiple_fields_validation(self):
        # Set config to check email and phone
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', str((self.email_field + self.phone_field).ids))

        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'multi@example.com',
            'phone': '1234567890'
        })

        # Should fail on phone
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Test Partner 2',
                'email': 'other@example.com',
                'phone': '1234567890'
            })

    def test_06_multi_record_write_error_handling(self):
        # Test if the model handles writing to multiple records properly
        # if len(self) > 1, `self.id` in `('id', '!=', self.id)` will raise ValueError
        self.env['ir.config_parameter'].sudo().set_param(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids))

        partner1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'multi_write1@example.com'
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'multi_write2@example.com'
        })
        
        # We don't want to crash with ValueError: Expected singleton
        try:
            (partner1 | partner2).write({
                'email': 'shared@example.com'
            })
        except ValueError as e:
            if "Expected singleton" in str(e):
                self.fail("write method crashed with Expected singleton error on multi-record write")
            else:
                raise
        except ValidationError:
            pass # Expected to fail since they'd both have the same email and one would duplicate the other
