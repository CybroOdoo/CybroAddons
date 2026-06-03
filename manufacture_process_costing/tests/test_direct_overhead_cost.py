# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestDirectOverheadCost(TransactionCase):

    def test_compute_total_costs(self):
        overhead = self.env['direct.overhead.cost'].create({
            'operation': 'Assembly',
            'planned_minute': 10.0,
            'actual_minute': 8.0,
            'cost_minute': 6.0,
        })

        self.assertAlmostEqual(overhead.total_cost, 60.0)
        self.assertAlmostEqual(overhead.total_actual_cost, 48.0)
