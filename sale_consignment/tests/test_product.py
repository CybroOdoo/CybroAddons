# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from datetime import date, timedelta
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestProduct(TestConsignmentCommon):

    def test_product_consignment_field(self):
        """Test default product is_consignment configurations."""
        self.assertTrue(self.product_consignment.is_consignment)
        self.assertFalse(self.product_normal.is_consignment)

        # Test condition check computation on consignment line
        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
        })
        line = self.env['sale.consignment.line'].new({
            'product_id': self.product_consignment.id,
            'consignment_id': consignment.id,
        })
        self.assertTrue(line.product_domain)
        self.assertIn('is_consignment', line.condition_check_line)
