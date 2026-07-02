# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResPartner, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Setup configuration parameters
        cls.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.customer_prefix', 'CUST-')

    def test_01_res_partner_create_sequence(self):
        """Test sequence generation on partner creation"""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'customer_rank': 1
        })
        self.assertTrue(partner.sequence)
        self.assertTrue(partner.sequence.startswith('CUST-'))

    def test_02_res_partner_create_without_prefix(self):
        """Test error when creating partner without prefix"""
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.customer_prefix', False)
        with self.assertRaises(UserError):
            self.env['res.partner'].create({
                'name': 'Test Partner No Prefix',
            })
        # Revert
        self.env['ir.config_parameter'].sudo().set_param('customer_product_qr.config.customer_prefix', 'CUST-')

    def test_03_res_partner_action_generate_sequence(self):
        """Test manual generation of sequence for partner"""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        partner.sequence = False
        partner.action_generate_sequence()
        self.assertTrue(partner.sequence)
        self.assertTrue(partner.sequence.startswith('CUST-'))

    def test_04_res_partner_action_generate_qr(self):
        """Test QR code generation for partner"""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        action = partner.action_generate_qr()
        self.assertTrue(partner.qr)
        self.assertEqual(action.get('type'), 'ir.actions.report')

    def test_05_res_partner_get_partner_by_qr(self):
        """Test fetching partner by QR sequence"""
        partner = self.env['res.partner'].create({'name': 'Test Partner QR'})
        partner.action_generate_sequence()
        sequence = partner.sequence
        
        partner.sequence = str(partner.id)
        fetched_id = partner.get_partner_by_qr()
        self.assertEqual(fetched_id, partner.id)

    def test_06_res_partner_init_function(self):
        """Test the init function for res.partner"""
        partner = self.env['res.partner'].create({
            'name': 'Init Partner',
            'customer_rank': 1
        })
        partner.init()
        # Should be updated to 'DEFINITPARTNER<id>'
        expected_sequence = 'DEFINITPARTNER' + str(partner.id)
        self.assertEqual(partner.sequence, expected_sequence)
