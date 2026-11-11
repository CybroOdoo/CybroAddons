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
#############################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestAddressExtractionWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls.env['res.country'].search([('code', '=', 'US')], limit=1)
        if not cls.country_us:
            cls.country_us = cls.env['res.country'].create({'name': 'United States', 'code': 'US'})

        cls.state_ca = cls.env['res.country.state'].search([
            ('code', '=', 'CA'),
            ('country_id', '=', cls.country_us.id),
        ], limit=1)
        if not cls.state_ca:
            cls.state_ca = cls.env['res.country.state'].create({
                'name': 'California',
                'code': 'CA',
                'country_id': cls.country_us.id,
            })

        cls.partner = cls.env['res.partner'].create({
            'name': 'ACME Corp',
            'street': 'Old Street 10',
            'city': 'Old City',
        })

    def test_default_get_with_context(self):
        """Test default_get initializes partner_id and raw_address from active context."""
        ctx = {
            'active_model': 'res.partner',
            'active_id': self.partner.id,
            'default_is_partner_readonly': True,
        }
        wizard_vals = self.env['address.extraction.wizard'].with_context(**ctx).default_get([
            'partner_id', 'raw_address', 'is_partner_readonly',
        ])
        self.assertEqual(wizard_vals.get('partner_id'), self.partner.id)
        self.assertTrue(wizard_vals.get('is_partner_readonly'))
        self.assertIn("Old Street 10", wizard_vals.get('raw_address', ''))

    def test_action_extract_address_validation(self):
        """Test action_extract_address raises UserError when raw_address is blank."""
        wizard = self.env['address.extraction.wizard'].create({
            'partner_id': self.partner.id,
            'raw_address': '   ',
        })
        with self.assertRaises(UserError):
            wizard.action_extract_address()

    def test_action_extract_address_success(self):
        """Test action_extract_address parses components and advances state."""
        extracted_mock = {
            'street': '742 Evergreen Terrace',
            'street2': 'Apt 2',
            'city': 'Springfield',
            'state': 'California',
            'zip': '97477',
            'country': 'USA',
        }
        wizard = self.env['address.extraction.wizard'].create({
            'partner_id': self.partner.id,
            'raw_address': '742 Evergreen Terrace, Apt 2, Springfield, California, USA',
        })

        with patch.object(type(self.env['gemini.service']), 'extract_address', return_value=extracted_mock):
            wizard.action_extract_address()
            self.assertEqual(wizard.state, 'extracted')
            self.assertEqual(wizard.extracted_street, '742 Evergreen Terrace')
            self.assertEqual(wizard.extracted_street2, 'Apt 2')
            self.assertEqual(wizard.extracted_city, 'Springfield')
            self.assertEqual(wizard.extracted_zip, '97477')
            self.assertEqual(wizard.extracted_country_id.id, self.country_us.id)
            self.assertEqual(wizard.extracted_state_id.id, self.state_ca.id)

    def test_resolve_country_variations(self):
        """Test _resolve_country with code alias, ISO code, name, and empty."""
        wizard = self.env['address.extraction.wizard'].new()

        # Alias USA
        res_alias = wizard._resolve_country('USA')
        self.assertEqual(res_alias.code, 'US')

        # Exact code
        res_code = wizard._resolve_country('US')
        self.assertEqual(res_code.code, 'US')

        # Full name
        res_name = wizard._resolve_country('United States')
        self.assertEqual(res_name.code, 'US')

        # Empty / whitespace
        res_empty = wizard._resolve_country('   ')
        self.assertFalse(res_empty)

    def test_resolve_state_variations(self):
        """Test _resolve_state with state code, name, and country scoping."""
        wizard = self.env['address.extraction.wizard'].new()

        # Code with country
        res_code = wizard._resolve_state('CA', self.country_us)
        self.assertEqual(res_code.id, self.state_ca.id)

        # Name with country
        res_name = wizard._resolve_state('California', self.country_us)
        self.assertEqual(res_name.id, self.state_ca.id)

        # Empty query
        res_empty = wizard._resolve_state('', self.country_us)
        self.assertFalse(res_empty)

    def test_action_apply_to_contact_without_overwrite(self):
        """Test apply to contact without overwrite preserves existing contact fields."""
        wizard = self.env['address.extraction.wizard'].create({
            'partner_id': self.partner.id,
            'raw_address': 'Test Raw',
            'state': 'extracted',
            'extracted_street': 'New Street 99',  # partner already has street 'Old Street 10'
            'extracted_street2': 'Suite 400',     # partner street2 was empty
            'extracted_city': 'New City',         # partner already has city 'Old City'
            'extracted_zip': '90210',             # partner zip was empty
            'extracted_country_id': self.country_us.id,
            'extracted_state_id': self.state_ca.id,
            'overwrite_existing': False,
        })
        wizard.action_apply_to_contact()

        # Preserved
        self.assertEqual(self.partner.street, 'Old Street 10')
        self.assertEqual(self.partner.city, 'Old City')
        # Populated
        self.assertEqual(self.partner.street2, 'Suite 400')
        self.assertEqual(self.partner.zip, '90210')
        self.assertEqual(self.partner.country_id.id, self.country_us.id)
        self.assertEqual(self.partner.state_id.id, self.state_ca.id)

    def test_action_apply_to_contact_with_overwrite(self):
        """Test apply to contact with overwrite=True overwrites existing contact fields."""
        wizard = self.env['address.extraction.wizard'].create({
            'partner_id': self.partner.id,
            'raw_address': 'Test Raw',
            'state': 'extracted',
            'extracted_street': 'Overwritten Street 50',
            'extracted_city': 'Overwritten City',
            'overwrite_existing': True,
        })
        wizard.action_apply_to_contact()

        self.assertEqual(self.partner.street, 'Overwritten Street 50')
        self.assertEqual(self.partner.city, 'Overwritten City')

    def test_action_apply_to_contact_missing_partner_raises_user_error(self):
        """Test UserError is raised if partner_id is not set."""
        wizard = self.env['address.extraction.wizard'].new({
            'partner_id': False,
            'raw_address': 'Some address',
            'state': 'extracted',
        })
        with self.assertRaises(UserError):
            wizard.action_apply_to_contact()

    def test_action_create_contact(self):
        """Test creating a brand new contact from confirmed address components."""
        wizard = self.env['address.extraction.wizard'].new({
            'partner_id': False,
            'raw_address': 'Googleplex HQ\n1600 Amphitheatre Pkwy',
            'state': 'extracted',
            'extracted_street': '1600 Amphitheatre Pkwy',
            'extracted_city': 'Mountain View',
            'extracted_zip': '94043',
            'extracted_country_id': self.country_us.id,
            'extracted_state_id': self.state_ca.id,
        })
        action = wizard.action_create_contact()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'res.partner')
        new_partner_id = action.get('res_id')
        self.assertTrue(new_partner_id)

        new_partner = self.env['res.partner'].browse(new_partner_id)
        self.assertEqual(new_partner.name, 'Googleplex HQ')
        self.assertEqual(new_partner.street, '1600 Amphitheatre Pkwy')
        self.assertEqual(new_partner.city, 'Mountain View')
        self.assertEqual(new_partner.zip, '94043')
        self.assertEqual(new_partner.country_id.id, self.country_us.id)
        self.assertEqual(new_partner.state_id.id, self.state_ca.id)
