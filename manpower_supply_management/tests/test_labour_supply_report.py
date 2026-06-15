from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestLabourSupplyReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Manpower Customer",
            "email": "customer@example.com",
        })
        cls.today = fields.Date.today()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

    @classmethod
    def _create_contract(cls, **extra_vals):
        vals = {
            "customer_id": cls.partner.id,
        }
        vals.update(extra_vals)
        return cls.env["labour.supply"].create(vals)

    def test_get_report_values_returns_selected_labour_supply_records(self):
        contract = self._create_contract()

        values = self.env[
            "report.manpower_supply_management.form_print_labour_supply"
        ]._get_report_values(contract.ids)

        self.assertEqual(values["docs_ids"], contract.ids)
        self.assertEqual(values["labour_supply"], contract)

    def test_wizard_customer_wise_report_raises_without_matching_data(self):
        wizard = self.env["labour.supply.report"].create({
            "filter": "customer_wise",
            "customer_id": self.partner.id,
            "from_date": self.tomorrow,
            "to_date": self.next_week,
        })

        with self.assertRaisesRegex(UserError, "No data found"):
            wizard.action_print_pdf()

    def test_wizard_customer_wise_report_returns_action_when_data_exists(self):
        self._create_contract(
            from_date=self.tomorrow,
            to_date=self.next_week,
            total_amount=250,
            state="ready",
        )
        wizard = self.env["labour.supply.report"].create({
            "filter": "customer_wise",
            "customer_id": self.partner.id,
            "from_date": self.tomorrow,
            "to_date": self.next_week,
        })

        action = wizard.action_print_pdf()

        self.assertIsInstance(action, dict)
        self.assertIn("type", action)

    def test_wizard_state_wise_report_returns_action_when_data_exists(self):
        self._create_contract(
            from_date=self.tomorrow,
            to_date=self.next_week,
            total_amount=250,
            state="ready",
        )
        wizard = self.env["labour.supply.report"].create({
            "filter": "state_wise",
            "state_id": "ready",
            "from_date": self.tomorrow,
            "to_date": self.next_week,
        })

        action = wizard.action_print_pdf()

        self.assertIsInstance(action, dict)
        self.assertIn("type", action)

