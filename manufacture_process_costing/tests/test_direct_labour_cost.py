# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestDirectLabourCost(TransactionCase):

    def test_compute_total_costs(self):
        labour = self.env['direct.labour.cost'].create({
            'operation': 'Assembly',
            'planned_minute': 12.0,
            'actual_minute': 9.0,
            'cost_minute': 4.0,
        })

        self.assertAlmostEqual(labour.total_cost, 48.0)
        self.assertAlmostEqual(labour.total_actual_cost, 36.0)
