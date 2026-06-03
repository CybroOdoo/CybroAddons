# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCommissionGraduated(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission = cls.env["crm.commission"].create({
            "name": "Graduated Commission",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "type": "revenue",
            "revenue_type": "graduated",
        })

    def test_check_amounts_rejects_invalid_range(self):
        with self.assertRaises(ValidationError):
            self.env["commission.graduated"].create({
                "commission_id": self.commission.id,
                "amount_from": 500.0,
                "amount_to": 100.0,
                "graduated_commission_rate": 5.0,
            })

    def test_compute_sequence_numbers_commission_rules(self):
        rules = self.env["commission.graduated"].create([
            {
                "commission_id": self.commission.id,
                "amount_from": 0.0,
                "amount_to": 100.0,
                "graduated_commission_rate": 2.0,
            },
            {
                "commission_id": self.commission.id,
                "amount_from": 101.0,
                "amount_to": 500.0,
                "graduated_commission_rate": 5.0,
            },
        ])

        rules._compute_sequence()

        self.assertEqual(rules.sorted("id").mapped("sequence"), [1, 2])
