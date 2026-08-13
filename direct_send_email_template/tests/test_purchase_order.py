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

class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseOrder, cls).setUpClass()
        
        # Partner & Product
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'standard_price': 50.0,
        })
        
        # Email Template
        cls.template = cls.env['mail.template'].create({
            'name': 'Test Purchase Template',
            'model_id': cls.env['ir.model'].search([('model', '=', 'purchase.order')]).id,
            'subject': 'Test Subject',
            'body_html': '<p>Test Body</p>',
        })

    def test_action_direct_send_purchase_disabled(self):
        """Test when configuration is disabled"""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        
        # Disable config
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_purchase', False)
        
        with self.assertRaises(ValidationError):
            purchase_order.action_direct_send_purchase()

    def test_action_direct_send_purchase_no_template(self):
        """Test when configuration is enabled but no template is set"""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        
        # Enable config but don't set template ID
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_purchase', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_prfq', False)
        
        with self.assertRaises(ValidationError):
            purchase_order.action_direct_send_purchase()

    def test_action_direct_send_purchase_rfq(self):
        """Test sending email for draft RFQ"""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_purchase', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_prfq', str(self.template.id))
        
        # Execute action
        purchase_order.action_direct_send_purchase()
        
        # Verify
        self.assertTrue(purchase_order.direct_send_rfq, "direct_send_rfq should be True")

    def test_action_direct_send_purchase_order(self):
        """Test sending email for confirmed purchase order"""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        purchase_order.button_confirm() # changes state to 'purchase'
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_purchase', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_po', str(self.template.id))
        
        # Execute action
        purchase_order.action_direct_send_purchase()
        
        # Verify
        self.assertTrue(purchase_order.direct_send_po, "direct_send_po should be True")
