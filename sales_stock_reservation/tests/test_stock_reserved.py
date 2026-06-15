# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestStockReserved(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockReserved, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Reserved',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product Reserved',
            'type': 'consu',
            'is_storable': True,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_stock_reserved_creation_and_sequence(self):
        """Test that stock.reserved records are created successfully and sequence name is generated."""
        reserved_record = self.env['stock.reserved'].create({
            'order_line_name': 'Test Reserved Line',
            'product_id': self.product.id,
            'reserved_quantity': 10.0,
            'sale_order_id': self.sale_order.id,
            'status': 'reserved',
        })
        
        # Verify the record fields
        self.assertEqual(reserved_record.order_line_name, 'Test Reserved Line')
        self.assertEqual(reserved_record.product_id, self.product)
        self.assertEqual(reserved_record.reserved_quantity, 10.0)
        self.assertEqual(reserved_record.sale_order_id, self.sale_order)
        self.assertEqual(reserved_record.status, 'reserved')
        
        # Verify sequence generation for name field
        # The sequence is defined in data/ir_sequence_data.xml with prefix 'STOCK/RES/'
        self.assertTrue(reserved_record.name)
        self.assertTrue(reserved_record.name.startswith('STOCK/RES/'))
