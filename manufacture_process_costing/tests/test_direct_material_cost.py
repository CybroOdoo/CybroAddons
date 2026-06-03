# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestDirectMaterialCost(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.component = cls.env['product.product'].create({
            'name': 'Costing Component',
            'type': 'product',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
        })

    def test_compute_total_costs(self):
        material = self.env['direct.material.cost'].create({
            'product_id': self.component.id,
            'planned_qty': 5.0,
            'actual_quantity': 4,
            'cost_unit': 7.0,
        })

        self.assertAlmostEqual(material.total_cost, 35.0)
        self.assertAlmostEqual(material.total_actual_cost, 28.0)
