# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestSubscriptionClose(TransactionCase):
    """Test Subscription Close Wizard"""

    def setUp(self):
        """Setup test variables"""
        super(TestSubscriptionClose, self).setUp()
        self.SubPackage = self.env['subscription.package']
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.plan = self.env['subscription.package.plan'].create({
            'name': 'Plan A',
            'renewal_value': '1',
            'renewal_period': 'months'
        })
        self.stage_closed = self.env['subscription.package.stage'].search(
            [('category', '=', 'closed')], limit=1) or self.env['subscription.package.stage'].create({
            'name': 'Closed',
            'category': 'closed'
        })
        self.stop_reason = self.env['subscription.package.stop'].create({'name': 'End of Contract'})
        
        self.product = self.env['product.product'].create({
            'name': 'Sub Product',
            'is_subscription': True
        })
        
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0
            })]
        })
        
        self.sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'sale_order_id': self.order.id
        })

    def test_button_submit_wizard(self):
        """Test close wizard button_submit logic"""
        wizard = self.env['subscription.close'].with_context(active_id=self.sub.id).create({
            'close_reason_id': self.stop_reason.id,
            'closed_by': self.env.user.id,
            'close_date': '2026-06-10'
        })
        
        wizard.button_submit()
        
        # Verify subscription is closed
        self.assertTrue(self.sub.is_closed)
        self.assertEqual(self.sub.stage_id, self.stage_closed)
        self.assertEqual(self.sub.close_reason_id, self.stop_reason)
        
        # Verify sale order lines are updated
        line = self.order.order_line[0]
        self.assertEqual(line.qty_invoiced, 5.0)
        self.assertEqual(line.qty_to_invoice, 0.0)
