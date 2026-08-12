# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby(<https://www.cybrosys.com>)
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
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from werkzeug.wrappers import Response
from odoo.addons.website_sale_auto_backend.controllers.website_sale_auto_backend import WebsiteSalePayment
import odoo.addons.website_sale_auto_backend.controllers.website_sale_auto_backend as controller_module


class TestWebsiteSaleAutoBackend(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product', 
            'type': 'consu', 
            'list_price': 100, 
            'invoice_policy': 'order'
        })
        
        cls.acquirer = cls.env['payment.provider'].create({
            'name': 'Test Provider',
            'state': 'test',
        })

    def _create_order_and_tx(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })]
        })
        payment_method = self.env['payment.method'].search([], limit=1)
        if not payment_method:
            self.env.cr.execute("ALTER TABLE payment_transaction ALTER COLUMN payment_method_id DROP NOT NULL")
            
        tx_vals = {
            'amount': 100.0,
            'currency_id': self.env.company.currency_id.id,
            'provider_id': self.acquirer.id,
            'reference': 'test_tx_%s' % order.id,
            'partner_id': self.partner.id,
            'sale_order_ids': [(6, 0, order.ids)],
            'state': 'done'
        }
        if payment_method:
            tx_vals['payment_method_id'] = payment_method.id
            
        tx = self.env['payment.transaction'].create(tx_vals)

        return order, tx

    def test_shop_payment_validate(self):
        """Test for the function shop_payment_validate in WebsiteSalePayment controller"""
        controller = WebsiteSalePayment()
        def run_validate(order):
            mock_request = MagicMock()
            mock_request.env = self.env
            mock_request.website.sale_get_order.return_value = order
            mock_request.session = {'sale_last_order_id': order.id}
            mock_request.redirect.return_value = Response("redirected")
            
            original_request = controller_module.request
            controller_module.request = mock_request
            try:
                controller.shop_payment_validate(sale_order_id=order.id)
            finally:
                controller_module.request = original_request

        self.env['ir.config_parameter'].sudo().set_param(
            'website_sale_auto_backend.website_order_configuration', 'confirm_order')
        order1, _ = self._create_order_and_tx()
        run_validate(order1)
        self.assertEqual(order1.state, 'sale')
        
        self.env['ir.config_parameter'].sudo().set_param(
            'website_sale_auto_backend.website_order_configuration', 'confirm_order_create_inv')
        order2, _ = self._create_order_and_tx()
        run_validate(order2)
        self.assertEqual(order2.state, 'sale')
        self.assertTrue(order2.invoice_ids)
        self.assertEqual(order2.invoice_ids[0].state, 'draft')
        
        self.env['ir.config_parameter'].sudo().set_param(
            'website_sale_auto_backend.website_order_configuration', 'confirm_order_post_inv')
        order3, _ = self._create_order_and_tx()
        run_validate(order3)
        self.assertEqual(order3.state, 'sale')
        self.assertTrue(order3.invoice_ids)
        self.assertEqual(order3.invoice_ids[0].state, 'posted')
        
        self.env['ir.config_parameter'].sudo().set_param(
            'website_sale_auto_backend.website_order_configuration', 'confirm_quotation_create_payment')
        order4, _ = self._create_order_and_tx()
        with patch('odoo.addons.account_payment.models.payment_transaction.PaymentTransaction._create_payment') as mock_create_payment:
            run_validate(order4)
            self.assertEqual(order4.state, 'sale')
            self.assertTrue(order4.invoice_ids)
            self.assertEqual(order4.invoice_ids[0].state, 'posted')
            mock_create_payment.assert_called_once()
