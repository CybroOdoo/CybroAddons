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
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosCustomerRestrict(TransactionCase):
    """Test suite for POS Customer Restrict module."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for POS customer restriction tests."""
        super().setUpClass()
        company = cls.env.company
        if not company.chart_template:
            company.chart_template = 'generic_coa'
            company.try_loading(install_demo=False)
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop',
        })
        cls.partner_allowed = cls.env['res.partner'].create({
            'name': 'Allowed Customer',
            'is_available_in_pos': True,
        })
        cls.partner_restricted = cls.env['res.partner'].create({
            'name': 'Restricted Customer',
            'is_available_in_pos': False,
        })

    def test_default_is_available_in_pos(self):
        """Verify that newly created partners default to is_available_in_pos=False in backend."""
        partner = self.env['res.partner'].create({'name': 'Default Customer'})
        self.assertFalse(partner.is_available_in_pos)

    def test_explicit_is_available_in_pos(self):
        """Verify that partner can be explicitly marked as available in POS."""
        self.assertTrue(self.partner_allowed.is_available_in_pos)
        self.assertFalse(self.partner_restricted.is_available_in_pos)

    def test_write_toggle_pos_availability(self):
        """Verify toggling is_available_in_pos via backend write."""
        self.partner_restricted.write({'is_available_in_pos': True})
        self.assertTrue(self.partner_restricted.is_available_in_pos)
        self.partner_restricted.write({'is_available_in_pos': False})
        self.assertFalse(self.partner_restricted.is_available_in_pos)

    def test_load_pos_data_fields(self):
        """Verify is_available_in_pos is included in loaded POS fields."""
        fields_list = self.env['res.partner']._load_pos_data_fields(self.pos_config)
        self.assertIn('is_available_in_pos', fields_list)

    def test_load_pos_data_domain(self):
        """Verify load domain includes restriction to is_available_in_pos=True."""
        dummy_data = {'pos.config': self.pos_config}
        domain = self.env['res.partner']._load_pos_data_domain(dummy_data)
        self.assertIn(('is_available_in_pos', '=', True), domain)

    def test_load_pos_data_domain_filtering(self):
        """Verify searching res.partner with the pos domain only finds allowed partners."""
        dummy_data = {'pos.config': self.pos_config}
        domain = self.env['res.partner']._load_pos_data_domain(dummy_data)
        found_partners = self.env['res.partner'].search(domain)
        self.assertIn(self.partner_allowed, found_partners)
        self.assertNotIn(self.partner_restricted, found_partners)

    def test_clean_pos_values(self):
        """Verify _clean_pos_values converts [id, name] pairs into integer ids."""
        vals = {
            'name': 'Clean Partner',
            'country_id': [1, 'United States'],
            'phone': '1234567890',
            'tag_ids': [],
            'category_id': [31],
        }
        cleaned = self.env['res.partner']._clean_pos_values(vals)
        self.assertEqual(cleaned['country_id'], 1)
        self.assertEqual(cleaned['name'], 'Clean Partner')
        self.assertEqual(cleaned['phone'], '1234567890')
        self.assertEqual(cleaned['tag_ids'], [])
        self.assertEqual(cleaned['category_id'], [31])

    def test_pos_ui_create_auto_available(self):
        """Verify partners created from POS UI are automatically marked available in POS."""
        mock_req = Mock()
        mock_req.httprequest.referrer = 'http://localhost:8069/pos/ui?config_id=1'
        with patch('odoo.addons.pos_customer_restrict.models.res_partner.request', mock_req):
            pos_partner = self.env['res.partner'].create({'name': 'POS Created Customer'})
            self.assertTrue(pos_partner.is_available_in_pos)

    def test_pos_ui_write_auto_available(self):
        """Verify partners updated from POS UI are automatically marked available in POS."""
        mock_req = Mock()
        mock_req.httprequest.referrer = 'http://localhost:8069/pos/ui?config_id=1'
        with patch('odoo.addons.pos_customer_restrict.models.res_partner.request', mock_req):
            self.partner_restricted.write({'phone': '9876543210'})
            self.assertTrue(self.partner_restricted.is_available_in_pos)

    def test_batch_create_partners(self):
        """Verify create handles batch list of dicts properly."""
        vals_list = [
            {'name': 'Batch Customer 1', 'is_available_in_pos': False},
            {'name': 'Batch Customer 2', 'is_available_in_pos': True},
        ]
        partners = self.env['res.partner'].create(vals_list)
        self.assertEqual(len(partners), 2)
        self.assertFalse(partners[0].is_available_in_pos)
        self.assertTrue(partners[1].is_available_in_pos)
