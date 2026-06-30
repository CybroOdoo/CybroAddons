# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        
        cls.sale_order_1 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })]
        })
        
        cls.sale_order_2 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })]
        })

    def test_01_action_multi_confirm(self):
        """Test action_multi_confirm for sale orders"""
        self.assertEqual(self.sale_order_1.state, 'draft')
        self.assertEqual(self.sale_order_2.state, 'draft')
        
        active_ids = [self.sale_order_1.id, self.sale_order_2.id]
        
        self.env['sale.order'].with_context(active_ids=active_ids).action_multi_confirm()
        
        self.assertEqual(self.sale_order_1.state, 'sale')
        self.assertEqual(self.sale_order_2.state, 'sale')

    def test_02_action_multi_cancel(self):
        """Test action_multi_cancel for sale orders"""
        self.assertEqual(self.sale_order_1.state, 'draft')
        self.assertEqual(self.sale_order_2.state, 'draft')
        
        active_ids = [self.sale_order_1.id, self.sale_order_2.id]
        
        self.env['sale.order'].with_context(active_ids=active_ids).action_multi_cancel()
        
        self.assertEqual(self.sale_order_1.state, 'cancel')
        self.assertEqual(self.sale_order_2.state, 'cancel')
