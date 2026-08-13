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

class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        
        # Partner & Product
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'list_price': 100.0,
        })
        
        # Email Template
        cls.template = cls.env['mail.template'].create({
            'name': 'Test Sale Template',
            'model_id': cls.env['ir.model'].search([('model', '=', 'sale.order')]).id,
            'subject': 'Test Subject',
            'body_html': '<p>Test Body</p>',
        })

    def test_action_direct_send_sale_disabled(self):
        """Test when configuration is disabled"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })]
        })
        
        # Disable config
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_sale', False)
        
        with self.assertRaises(ValidationError):
            sale_order.action_direct_send_sale()

    def test_action_direct_send_sale_no_template(self):
        """Test when configuration is enabled but no template is set"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        
        # Enable config but don't set template ID
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_sale', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_sq', False)
        
        with self.assertRaises(ValidationError):
            sale_order.action_direct_send_sale()

    def test_action_direct_send_sale_quotation(self):
        """Test sending email for draft quotation"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_sale', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_sq', str(self.template.id))
        
        # Execute action
        sale_order.action_direct_send_sale()
        
        # Verify
        self.assertTrue(sale_order.direct_send_quo, "direct_send_quo should be True")

    def test_action_direct_send_sale_order(self):
        """Test sending email for confirmed sale order"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        sale_order.action_confirm() # changes state to 'sale'
        
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.is_direct_send_email_sale', True)
        self.env['ir.config_parameter'].sudo().set_param('direct_send_email_template.direct_send_mailtemplate_so', str(self.template.id))
        
        # Execute action
        sale_order.action_direct_send_sale()
        
        # Verify
        self.assertTrue(sale_order.direct_send_so, "direct_send_so should be True")
