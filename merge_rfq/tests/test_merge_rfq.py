# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError

@tagged('post_install', '-at_install')
class TestMergeRfq(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMergeRfq, cls).setUpClass()
        # Setup data
        cls.partner_1 = cls.env['res.partner'].create({'name': 'Vendor 1'})
        cls.partner_2 = cls.env['res.partner'].create({'name': 'Vendor 2'})
        
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Product A',
            'type': 'consu',
            'standard_price': 100.0,
            'list_price': 150.0,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Product B',
            'type': 'consu',
            'standard_price': 50.0,
            'list_price': 80.0,
        })

        # Create PO 1
        cls.po_1 = cls.env['purchase.order'].create({
            'partner_id': cls.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product_1.id,
                    'product_qty': 5,
                    'price_unit': 100.0,
                }),
            ]
        })

        # Create PO 2
        cls.po_2 = cls.env['purchase.order'].create({
            'partner_id': cls.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product_1.id,
                    'product_qty': 10,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': cls.product_2.id,
                    'product_qty': 3,
                    'price_unit': 50.0,
                }),
            ]
        })

        # Create PO 3
        cls.po_3 = cls.env['purchase.order'].create({
            'partner_id': cls.partner_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product_2.id,
                    'product_qty': 2,
                    'price_unit': 40.0, # Different price
                }),
            ]
        })

    def test_merge_orders_less_than_two(self):
        """Test merging with less than two orders raises UserError."""
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id]).create({
            'merge_type': 'cancel_and_new',
            'partner_id': self.partner_1.id,
        })
        with self.assertRaises(UserError):
            wizard.action_merge_orders()

    def test_merge_orders_wrong_state(self):
        """Test merging orders not in draft or sent state raises UserError."""
        self.po_1.button_confirm() # Purchase status -> not draft/sent
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id, self.po_2.id]).create({
            'merge_type': 'cancel_and_new',
            'partner_id': self.partner_1.id,
        })
        with self.assertRaises(UserError):
            wizard.action_merge_orders()

    def test_merge_cancel_and_new(self):
        """Test Cancel and New merge type"""
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id, self.po_2.id]).create({
            'merge_type': 'cancel_and_new',
            'partner_id': self.partner_1.id,
        })
        wizard.action_merge_orders()
        
        # Check original POs are cancelled
        self.assertEqual(self.po_1.state, 'cancel')
        self.assertEqual(self.po_2.state, 'cancel')

        # Check new PO was created
        # The new PO is created via `self.env["purchase.order"].create`, so we can search for a draft order for partner 1
        # that is not po_1 or po_2
        new_po = self.env['purchase.order'].search([
            ('partner_id', '=', self.partner_1.id),
            ('id', 'not in', [self.po_1.id, self.po_2.id]),
            ('state', 'in', ['draft', 'sent'])
        ])
        self.assertEqual(len(new_po), 1)

        # Check merged lines
        # po_1 has product_1: 5 (100)
        # po_2 has product_1: 10 (100) and product_2: 3 (50)
        # merged should have product_1: 15 (100) and product_2: 3 (50)
        product_1_lines = new_po.order_line.filtered(lambda l: l.product_id == self.product_1)
        self.assertEqual(len(product_1_lines), 1)
        self.assertEqual(product_1_lines.product_qty, 15)

        product_2_lines = new_po.order_line.filtered(lambda l: l.product_id == self.product_2)
        self.assertEqual(len(product_2_lines), 1)
        self.assertEqual(product_2_lines.product_qty, 3)

    def test_merge_delete_and_new(self):
        """Test Delete and New merge type"""
        po_1_id = self.po_1.id
        po_2_id = self.po_2.id
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id, self.po_2.id]).create({
            'merge_type': 'delete_and_new',
            'partner_id': self.partner_2.id,
        })
        wizard.action_merge_orders()

        # Check original POs are deleted
        pos = self.env['purchase.order'].search([('id', 'in', [po_1_id, po_2_id])])
        self.assertFalse(pos)

        # Check new PO was created
        new_po = self.env['purchase.order'].search([
            ('partner_id', '=', self.partner_2.id),
            ('state', 'in', ['draft', 'sent'])
        ])
        # We expect a new PO because we used partner_2 here for uniqueness
        new_po = new_po.filtered(lambda p: p.id not in [po_1_id, po_2_id, self.po_3.id])
        self.assertEqual(len(new_po), 1)

    def test_merge_cancel_and_merge(self):
        """Test Cancel and Merge merge type"""
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id, self.po_2.id]).create({
            'merge_type': 'cancel_and_merge',
            'purchase_order_id': self.po_1.id,
        })
        wizard.action_merge_orders()

        # po_2 should be cancelled
        self.assertEqual(self.po_2.state, 'cancel')

        # po_1 should contain merged lines
        # po_1 original product_1: 5 (100)
        # po_2 product_1: 10 (100), product_2: 3 (50)
        # result po_1: product_1: 15 (100), product_2: 3 (50)
        self.assertEqual(self.po_1.state, 'draft')
        
        product_1_lines = self.po_1.order_line.filtered(lambda l: l.product_id == self.product_1)
        self.assertEqual(len(product_1_lines), 1)
        self.assertEqual(product_1_lines.product_qty, 15.0)

        product_2_lines = self.po_1.order_line.filtered(lambda l: l.product_id == self.product_2)
        self.assertEqual(len(product_2_lines), 1)
        self.assertEqual(product_2_lines.product_qty, 3.0)

    def test_merge_delete_and_merge(self):
        """Test Delete and Merge merge type"""
        po_2_id = self.po_2.id
        wizard = self.env['merge.rfq'].with_context(active_ids=[self.po_1.id, self.po_2.id, self.po_3.id]).create({
            'merge_type': 'delete_and_merge',
            'purchase_order_id': self.po_1.id,
        })
        wizard.action_merge_orders()

        # po_2 & po_3 should be deleted
        pos = self.env['purchase.order'].search([('id', 'in', [po_2_id, self.po_3.id])])
        self.assertFalse(pos)

        # po_1 should contain merged lines
        # po_1 has:
        # - product_1 at 100
        # - product_2 at 50
        # - product_2 at 40 (po_3)
        product_1_lines = self.po_1.order_line.filtered(lambda l: l.product_id == self.product_1)
        self.assertEqual(len(product_1_lines), 1)
        self.assertEqual(product_1_lines.product_qty, 15.0)
        
        product_2_lines_50 = self.po_1.order_line.filtered(lambda l: l.product_id == self.product_2 and l.price_unit == 50.0)
        self.assertEqual(len(product_2_lines_50), 1)
        self.assertEqual(product_2_lines_50.product_qty, 3.0)

        product_2_lines_40 = self.po_1.order_line.filtered(lambda l: l.product_id == self.product_2 and l.price_unit == 40.0)
        self.assertEqual(len(product_2_lines_40), 1)
        self.assertEqual(product_2_lines_40.product_qty, 2.0)

