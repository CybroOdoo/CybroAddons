# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import timedelta


class TestSaleOrder(TransactionCase):

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner Subscription',
        })
        self.product = self.env['product.product'].create({
            'name': 'Subscription Service',
            'type': 'service',
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
            # If the module expects an end_date field on sale.order, 
            # I should check if it exists in the manifest or model.
            # Looking at action_subscription_id_card, it uses self.end_date.
        })
        # Ensure company has a report layout to avoid redirect to layout configurator
        self.env.company.external_report_layout_id = self.env.ref('web.external_layout_standard')

    def test_action_subscription_id_card(self):
        """Test the print subscription ID card action"""
        # We need to make sure end_date exists if it's used in the function.
        # If it's a custom field added by this module, it should be fine.
        # Let's mock or set it if possible.
        if hasattr(self.sale_order, 'end_date'):
            self.sale_order.end_date = fields.Date.today() + timedelta(days=365)

        action = self.sale_order.action_subscription_id_card()

        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'print_subscription_id_card.report_subscription_id_card')

        data = action.get('data')
        self.assertTrue(data, "The action should contain a 'data' dictionary")
        self.assertEqual(data['name'], self.partner.name)
        self.assertIn('Subscription Service', data['products'])
        self.assertEqual(data['partner_id'], self.partner.id)

        self.assertTrue(action.get('close_on_report_download'), "Should close on report download")
