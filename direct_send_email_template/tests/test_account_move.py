# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMove, cls).setUpClass()
        
        # Partner & Product
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer/Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'list_price': 100.0,
        })
        
        # Email Template
        cls.template = cls.env['mail.template'].create({
            'name': 'Test Account Move Template',
            'model_id': cls.env['ir.model'].search([('model', '=', 'account.move')]).id,
            'subject': 'Test Subject',
            'body_html': '<p>Test Body</p>',
        })

    def test_action_direct_send_account_disabled(self):
        """Test when configuration is disabled"""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        
        # Disable config
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_account', False)
        
        with self.assertRaises(ValidationError):
            move.action_direct_send_account()

    def test_action_direct_send_account_no_template(self):
        """Test when configuration is enabled but no template is set"""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })]
        })
        move.action_post()
        
        # Enable config but don't set template ID
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_account', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_inv', False)
        
        with self.assertRaises(ValidationError):
            move.action_direct_send_account()

    def test_action_direct_send_account_invoice(self):
        """Test sending email for Customer Invoice"""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })]
        })
        move.action_post()
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_account', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_inv', str(self.template.id))
        
        # Execute action
        move.action_direct_send_account()
        
        # Verify
        self.assertTrue(move.direct_send_inv, "direct_send_inv should be True")

    def test_action_direct_send_account_bill(self):
        """Test sending email for Vendor Bill"""
        from odoo import fields
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.context_today(self.env.user),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })]
        })
        move.action_post()
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_account', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_bill', str(self.template.id))
        
        # Execute action
        move.action_direct_send_account()
        
        # Verify
        self.assertTrue(move.direct_send_bill, "direct_send_bill should be True")
