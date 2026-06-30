# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseOrder, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 50.0,
        })
        
        cls.purchase_order_1 = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'name': cls.product.name,
                'product_id': cls.product.id,
                'product_qty': 1.0,
                'price_unit': 50.0,
            })]
        })
        
        cls.purchase_order_2 = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'name': cls.product.name,
                'product_id': cls.product.id,
                'product_qty': 2.0,
                'price_unit': 50.0,
            })]
        })

    def test_01_action_multi_confirm(self):
        """Test action_multi_confirm for purchase orders"""
        self.assertEqual(self.purchase_order_1.state, 'draft')
        self.assertEqual(self.purchase_order_2.state, 'draft')
        
        active_ids = [self.purchase_order_1.id, self.purchase_order_2.id]
        
        self.env['purchase.order'].with_context(active_ids=active_ids).action_multi_confirm()
        
        self.assertEqual(self.purchase_order_1.state, 'purchase')
        self.assertEqual(self.purchase_order_2.state, 'purchase')

    def test_02_action_multi_cancel(self):
        """Test action_multi_cancel for purchase orders"""
        self.assertEqual(self.purchase_order_1.state, 'draft')
        self.assertEqual(self.purchase_order_2.state, 'draft')
        
        active_ids = [self.purchase_order_1.id, self.purchase_order_2.id]
        
        self.env['purchase.order'].with_context(active_ids=active_ids).action_multi_cancel()
        
        self.assertEqual(self.purchase_order_1.state, 'cancel')
        self.assertEqual(self.purchase_order_2.state, 'cancel')
