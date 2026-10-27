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
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged

# Minimal valid 1x1 GIF in base64
TINY_IMAGE_B64 = (
    b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test suite for res.partner membership fields and card generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Alice Member',
            'phone': '+1 555-0144',
            'email': 'alice@example.com',
            'function': 'Lead Designer',
            'image_1920': TINY_IMAGE_B64,
        })

        cls.service_product = cls.env['product.template'].create({
            'name': 'Standard Membership Service',
            'type': 'service',
        })

    def test_default_values(self):
        """Test default field values on res.partner."""
        new_partner = self.env['res.partner'].create({
            'name': 'Default Member Partner',
        })
        self.assertFalse(new_partner.free_member)
        self.assertFalse(new_partner.member_lines)

    def test_server_action_empty_recordset(self):
        """Test calling server action on an empty partner recordset."""
        res = self.env['res.partner'].server_action_get_card()
        self.assertFalse(res)

    def test_server_action_multi_recordset_fails(self):
        """Test that server_action_get_card enforces singleton."""
        partner_two = self.env['res.partner'].create({'name': 'Partner Two'})
        partners = self.partner | partner_two
        with self.assertRaises(ValueError):
            partners.server_action_get_card()

    def test_server_action_missing_image_fails(self):
        """Test validation error when partner has no image."""
        partner_no_img = self.env['res.partner'].create({
            'name': 'No Image Partner',
            'phone': '123456789',
            'image_1920': False,
        })
        with self.assertRaises(ValidationError) as error:
            partner_no_img.server_action_get_card()
        self.assertIn("Please provide an image", str(error.exception))

    def test_server_action_missing_phone_fails(self):
        """Test validation error when partner has no phone."""
        partner_no_phone = self.env['res.partner'].create({
            'name': 'No Phone Partner',
            'image_1920': TINY_IMAGE_B64,
            'phone': False,
        })
        with self.assertRaises(ValidationError) as error:
            partner_no_phone.server_action_get_card()
        self.assertIn("Please provide a phone number", str(error.exception))

    def test_server_action_non_free_member_without_lines_fails(self):
        """Test non-free member with no lines raises ValidationError."""
        partner_no_lines = self.env['res.partner'].create({
            'name': 'No Lines Member',
            'phone': '123456789',
            'image_1920': TINY_IMAGE_B64,
            'free_member': False,
        })
        with self.assertRaises(ValidationError) as error:
            partner_no_lines.server_action_get_card()
        self.assertIn("does not have a membership plan", str(error.exception))

    def test_server_action_non_free_member_no_service_lines_fails(self):
        """Test non-free member with non-service lines raises error."""
        partner = self.env['res.partner'].create({
            'name': 'Non Service Member',
            'phone': '123456789',
            'image_1920': TINY_IMAGE_B64,
            'free_member': False,
        })
        temp_product = self.env['product.template'].create({
            'name': 'Mock Service Product',
            'type': 'service',
        })
        today = fields.Date.context_today(partner)
        self.env['membership.card.line'].create({
            'partner_id': partner.id,
            'membership_id': temp_product.id,
            'date_from': today,
            'date_to': today + timedelta(days=30),
        })
        # Simulate product type updated to consumable
        self.env.cr.execute(
            "UPDATE product_template SET type = 'consu' WHERE id = %s",
            [temp_product.id],
        )
        temp_product.invalidate_recordset(['type'])

        with self.assertRaises(ValidationError) as error:
            partner.server_action_get_card()
        self.assertIn(
            "does not have a valid service membership product",
            str(error.exception),
        )

    def test_server_action_active_membership_line(self):
        """Test printing card for partner with an active membership line."""
        today = fields.Date.context_today(self.partner)
        # Expired line
        self.env['membership.card.line'].create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today - timedelta(days=400),
            'date_to': today - timedelta(days=35),
        })
        # Active line
        self.env['membership.card.line'].create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today - timedelta(days=10),
            'date_to': today + timedelta(days=355),
        })

        action = self.partner.server_action_get_card()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(
            action.get('report_name'),
            'membership_card_odoo.print_member_ship_card',
        )
        data = action['data']
        self.assertEqual(data['name'], self.partner.name)
        self.assertEqual(data['phone'], self.partner.phone)
        self.assertFalse(data['free_member'])
        self.assertEqual(
            data['membership_product'], [self.service_product.name],
        )
        self.assertTrue(data['start_date'])
        self.assertTrue(data['end_date'])

    def test_server_action_fallback_to_most_recent_line(self):
        """Test fallback to most recent line if no active line is present."""
        partner = self.env['res.partner'].create({
            'name': 'Past Member',
            'phone': '123456789',
            'image_1920': TINY_IMAGE_B64,
            'free_member': False,
        })
        today = fields.Date.context_today(partner)
        self.env['membership.card.line'].create({
            'partner_id': partner.id,
            'membership_id': self.service_product.id,
            'date_from': today - timedelta(days=40),
            'date_to': today - timedelta(days=10),
        })

        action = partner.server_action_get_card()
        data = action['data']
        self.assertEqual(
            data['membership_product'], [self.service_product.name],
        )
        self.assertTrue(data['start_date'])
        self.assertTrue(data['end_date'])

    def test_server_action_free_member(self):
        """Test printing card for an honorary free member."""
        partner_free = self.env['res.partner'].create({
            'name': 'Honorary Member',
            'phone': '+1 555-0999',
            'function': 'VIP Patron',
            'image_1920': TINY_IMAGE_B64,
            'free_member': True,
        })

        action = partner_free.server_action_get_card()
        data = action['data']
        self.assertTrue(data['free_member'])
        self.assertEqual(data['membership_product'], [])
        self.assertEqual(data['start_date'], '')
        self.assertEqual(data['end_date'], '')
        self.assertEqual(data['function'], 'VIP Patron')

    def test_server_action_image_str_format(self):
        """Test image_data handling when image_1920 is string format."""
        partner_str = self.env['res.partner'].create({
            'name': 'String Image Partner',
            'phone': '123456789',
            'image_1920': TINY_IMAGE_B64.decode('ascii'),
            'free_member': True,
        })
        action = partner_str.server_action_get_card()
        self.assertEqual(
            action['data']['image'], TINY_IMAGE_B64.decode('ascii'),
        )

    def test_server_action_custom_company(self):
        """Test report data uses partner company_id when configured."""
        custom_company = self.env['res.company'].create({
            'name': 'Custom Branch Inc.',
            'phone': '+1 555-0800',
            'email': 'branch@example.com',
            'website': 'https://branch.example.com',
        })
        partner = self.env['res.partner'].create({
            'name': 'Branch Partner',
            'phone': '+1 555-0801',
            'image_1920': TINY_IMAGE_B64,
            'free_member': True,
            'company_id': custom_company.id,
        })
        action = partner.server_action_get_card()

        data = action['data']
        self.assertEqual(data['company_name'], 'Custom Branch Inc.')
        self.assertEqual(data['company_email'], 'branch@example.com')
        self.assertEqual(data['company_phone'], '+1 555-0800')
        self.assertEqual(data['website'], 'https://branch.example.com')
