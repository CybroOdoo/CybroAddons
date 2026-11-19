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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestResPartner(TransactionCase):
    """Test suite for duplicate contact details validation on res.partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.email_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'email'),
        ], limit=1)
        cls.phone_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'phone'),
        ], limit=1)

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_bool(
            'duplicate_contact_details_alert.is_unique_contact', True,
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', '[]',
        )

    def tearDown(self):
        super().tearDown()
        self.env['ir.config_parameter'].sudo().set_bool(
            'duplicate_contact_details_alert.is_unique_contact', False,
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', '[]',
        )

    def test_01_duplicate_contact_creation_without_config(self):
        """Test creating partners when unique fields configuration is empty."""
        partner1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'test@example.com',
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'test@example.com',
        })
        self.assertTrue(partner1.id and partner2.id)

    def test_02_duplicate_contact_creation_with_config(self):
        """Test duplicate detection on partner creation when email uniqueness is configured."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids),
        )
        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'unique@example.com',
        })

        with self.assertRaises(ValidationError) as e:
            self.env['res.partner'].create({
                'name': 'Test Partner 2',
                'email': 'unique@example.com',
            })
        self.assertIn("Duplicate contact details were found", str(e.exception))

    def test_03_duplicate_contact_write_with_config(self):
        """Test duplicate detection on partner write when email uniqueness is configured."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids),
        )
        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'write1@example.com',
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'write2@example.com',
        })

        with self.assertRaises(ValidationError) as e:
            partner2.write({
                'email': 'write1@example.com',
            })
        self.assertIn("Duplicate contact details were found", str(e.exception))

    def test_04_write_same_value(self):
        """Test updating non-unique fields on a partner without triggering false duplicates."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids),
        )
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'same@example.com',
        })
        partner.write({
            'name': 'Updated Test Partner',
            'email': 'same@example.com',
        })
        self.assertEqual(partner.name, 'Updated Test Partner')

    def test_05_multiple_fields_validation(self):
        """Test validation when both email and phone fields are configured for uniqueness."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids',
            str((self.email_field + self.phone_field).ids),
        )
        self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'multi@example.com',
            'phone': '1234567890',
        })

        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Test Partner 2',
                'email': 'other@example.com',
                'phone': '1234567890',
            })

    def test_06_multi_record_write_error_handling(self):
        """Test multi-record write operations to ensure proper exception handling."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids),
        )
        partner1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'multi_write1@example.com',
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'multi_write2@example.com',
        })

        with self.assertRaises(ValidationError) as err:
            (partner1 | partner2).write({
                'email': 'shared@example.com',
            })
        self.assertIn("Duplicate contact details were found", str(err.exception))

    def test_07_phone_formatting_variations(self):
        """Test phone number duplicate detection across punctuation and spacing formats."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.phone_field.ids),
        )
        self.env['res.partner'].create({
            'name': 'Phone Contact 1',
            'phone': '+1 (555) 012-3456',
        })

        with self.assertRaises(ValidationError) as e:
            self.env['res.partner'].create({
                'name': 'Phone Contact 2',
                'phone': '555-012-3456',
            })
        self.assertIn("Duplicate contact details were found", str(e.exception))

        partner3 = self.env['res.partner'].create({
            'name': 'Phone Contact 3',
            'phone': '9999999999',
        })
        with self.assertRaises(ValidationError):
            partner3.write({
                'phone': '555 012 3456',
            })

    def test_08_phone_whitespace_handling(self):
        """Test phone duplicate detection with leading and trailing whitespaces."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.phone_field.ids),
        )
        self.env['res.partner'].create({
            'name': 'Phone Partner 1',
            'phone': '1234567890',
        })

        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Phone Partner 2',
                'phone': '  1234567890  ',
            })

    def test_09_email_case_insensitivity(self):
        """Test case-insensitive duplicate detection on email addresses."""
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.email_field.ids),
        )
        self.env['res.partner'].create({
            'name': 'Email Partner 1',
            'email': 'Test.Case@Example.Com',
        })

        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Email Partner 2',
                'email': 'test.case@example.com',
            })

    def test_10_disabled_unique_setting(self):
        """Test partner creation when unique contacts setting is explicitly disabled."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'duplicate_contact_details_alert.is_unique_contact', False,
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'duplicate_contact_details_alert.unique_contact_ids', str(self.phone_field.ids),
        )

        partner1 = self.env['res.partner'].create({
            'name': 'Partner A',
            'phone': '1112223333',
        })
        partner2 = self.env['res.partner'].create({
            'name': 'Partner B',
            'phone': '1112223333',
        })
        self.assertTrue(partner1.id and partner2.id)
