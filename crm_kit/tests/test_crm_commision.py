# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCrmCommission(TransactionCase):

    def test_check_date_rejects_invalid_range(self):
        with self.assertRaises(ValidationError):
            self.env["crm.commission"].create({
                "name": "Invalid Commission",
                "date_from": "2026-06-10",
                "date_to": "2026-06-01",
            })

    def test_onchange_type_revenue_clears_product_rules(self):
        commission = self.env["crm.commission"].new({
            "name": "Revenue Commission",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "type": "revenue",
            "product_comm_ids": [(0, 0, {"percentage": 5.0})],
        })

        commission._onchange_type()

        self.assertFalse(commission.product_comm_ids)

    def test_onchange_type_product_clears_revenue_settings(self):
        commission = self.env["crm.commission"].new({
            "name": "Product Commission",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "type": "product",
            "revenue_type": "straight",
            "straight_commission_rate": 10.0,
            "revenue_grd_comm_ids": [(0, 0, {
                "amount_from": 0.0,
                "amount_to": 100.0,
                "graduated_commission_rate": 2.0,
            })],
        })

        commission._onchange_type()

        self.assertFalse(commission.revenue_type)
        self.assertEqual(commission.straight_commission_rate, 0.0)
        self.assertFalse(commission.revenue_grd_comm_ids)
