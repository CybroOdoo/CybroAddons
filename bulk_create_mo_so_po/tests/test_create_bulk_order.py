# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestCreateBulkOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCreateBulkOrder, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        cls.product_with_bom = cls.env['product.product'].create({
            'name': 'Product with BOM',
            'list_price': 100.0,
            'standard_price': 50.0,
            'is_storable': True,
        })
        cls.product_no_bom = cls.env['product.product'].create({
            'name': 'Product without BOM',
            'list_price': 80.0,
            'standard_price': 40.0,
            'is_storable': True,
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_with_bom.product_tmpl_id.id,
            'product_id': cls.product_with_bom.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        
        cls.bulk_order_sale = cls.env['create.bulk.order'].create({
            'partner_id': cls.partner.id,
            'order_type': 'sale',
            'bulk_order_line_ids': [
                (0, 0, {
                    'product_id': cls.product_no_bom.id,
                    'qty': 5,
                })
            ]
        })

        cls.bulk_order_purchase = cls.env['create.bulk.order'].create({
            'partner_id': cls.partner.id,
            'order_type': 'purchase',
            'bulk_order_line_ids': [
                (0, 0, {
                    'product_id': cls.product_no_bom.id,
                    'qty': 10,
                })
            ]
        })

        cls.bulk_order_mrp = cls.env['create.bulk.order'].create({
            'partner_id': cls.partner.id,
            'order_type': 'manufacturing',
            'bulk_order_line_ids': [
                (0, 0, {
                    'product_id': cls.product_with_bom.id,
                    'bom_id': cls.bom.id,
                    'qty': 2,
                })
            ]
        })

        cls.bulk_order_mrp_no_bom = cls.env['create.bulk.order'].create({
            'partner_id': cls.partner.id,
            'order_type': 'manufacturing',
            'bulk_order_line_ids': [
                (0, 0, {
                    'product_id': cls.product_no_bom.id,
                    'qty': 2,
                })
            ]
        })
        
        cls.bulk_order_empty = cls.env['create.bulk.order'].create({
            'partner_id': cls.partner.id,
            'order_type': 'sale',
        })

    def test_01_action_confirm(self):
        """Test action_confirm"""
        self.assertEqual(self.bulk_order_sale.state, 'draft')
        self.bulk_order_sale.action_confirm()
        self.assertEqual(self.bulk_order_sale.state, 'confirm')
        self.assertNotEqual(self.bulk_order_sale.name, 'New')
        
        # Test missing lines
        with self.assertRaises(UserError):
            self.bulk_order_empty.action_confirm()

    def test_02_action_create_sale_order(self):
        """Test action_create_sale_order"""
        self.bulk_order_sale.action_confirm()
        self.bulk_order_sale.action_create_sale_order()
        self.assertEqual(self.bulk_order_sale.state, 'done')
        self.assertEqual(self.bulk_order_sale.sale_order_count, 1)
        self.assertTrue(self.bulk_order_sale.sale_order_ids)

    def test_03_action_create_purchase_order(self):
        """Test action_create_purchase_order"""
        self.bulk_order_purchase.action_confirm()
        self.bulk_order_purchase.action_create_purchase_order()
        self.assertEqual(self.bulk_order_purchase.state, 'done')
        self.assertEqual(self.bulk_order_purchase.purchase_order_count, 1)
        self.assertTrue(self.bulk_order_purchase.purchase_order_ids)

    def test_04_action_create_manufacturing_order(self):
        """Test action_create_manufacturing_order"""
        self.bulk_order_mrp.action_confirm()
        self.bulk_order_mrp.action_create_manufacturing_order()
        self.assertEqual(self.bulk_order_mrp.state, 'done')
        self.assertEqual(self.bulk_order_mrp.manufacturing_order_count, 1)
        self.assertTrue(self.bulk_order_mrp.manufacturing_order_ids)
        
        # Test no BOM error
        self.bulk_order_mrp_no_bom.action_confirm()
        with self.assertRaises(ValidationError):
            self.bulk_order_mrp_no_bom.action_create_manufacturing_order()

    def test_05_action_reset_to_draft(self):
        """Test action_reset_to_draft"""
        self.bulk_order_sale.action_confirm()
        self.bulk_order_sale.action_reset_to_draft()
        self.assertEqual(self.bulk_order_sale.state, 'draft')

    def test_06_get_actions(self):
        """Test get action methods"""
        sale_action = self.bulk_order_sale.get_sale_order()
        self.assertEqual(sale_action['domain'], [('bulk_order_id', '=', self.bulk_order_sale.id)])
        
        purchase_action = self.bulk_order_purchase.get_purchase_order()
        self.assertEqual(purchase_action['domain'], [('bulk_order_id', '=', self.bulk_order_purchase.id)])
        
        mrp_action = self.bulk_order_mrp.get_manufacturing_order()
        self.assertEqual(mrp_action['domain'], [('bulk_order_id', '=', self.bulk_order_mrp.id)])

    def test_07_onchange_methods(self):
        """Test onchange methods of bulk.order.line"""
        line = self.env['bulk.order.line'].new({
            'product_id': self.product_with_bom.id
        })
        line._onchange_product_id()
        self.assertEqual(line.list_price, 100.0)
        self.assertEqual(line.product_cost, 50.0)

        line.bom_id = self.bom.id
        line._onchange_bom_id()
        self.assertEqual(line.product_id.id, self.product_with_bom.id)
        
        line.product_id = False
        line._onchange_product_id()
        self.assertEqual(line.list_price, 0)
        self.assertEqual(line.product_cost, 0)
