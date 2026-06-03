# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestMrpWorkcenterCosting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Costing Work Center',
            'labour_cost': 2.0,
            'overhead_cost': 3.0,
        })

    def test_cost_fields_are_writable(self):
        self.workcenter.write({
            'labour_cost': 5.5,
            'overhead_cost': 6.5,
        })

        self.assertAlmostEqual(self.workcenter.labour_cost, 5.5)
        self.assertAlmostEqual(self.workcenter.overhead_cost, 6.5)
