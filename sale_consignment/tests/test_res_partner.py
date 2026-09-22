# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestResPartner(TestConsignmentCommon):

    def test_partner_consignment_field(self):
        """Test default partner is_consignment configurations."""
        self.assertTrue(self.partner_consignment.is_consignment)
        self.assertFalse(self.partner_normal.is_consignment)

        # Test condition check computation on consignment
        consignment = self.env['sale.consignment'].new({
            'partner_id': self.partner_consignment.id,
        })
        self.assertTrue(consignment.customer_domain)
        self.assertIn('is_consignment', consignment.condition_check)
