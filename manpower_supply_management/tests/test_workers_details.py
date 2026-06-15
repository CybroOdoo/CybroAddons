from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestWorkersDetails(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Manpower Customer",
            "email": "customer@example.com",
        })
        cls.skill = cls.env["skill.details"].create({
            "name": "Test Welding",
        })
        cls.next_week = fields.Date.today() + timedelta(days=7)

    @classmethod
    def _create_worker(cls, name="Test Worker", rate=100, state="available"):
        return cls.env["workers.details"].create({
            "name": name,
            "phone_number": "555-0100",
            "email": "%s@example.com" % name.lower().replace(" ", "-"),
            "image_worker": False,
            "rate": rate,
            "state": state,
            "skill_ids": [(6, 0, cls.skill.ids)],
        })

    @classmethod
    def _create_contract(cls, **extra_vals):
        vals = {
            "customer_id": cls.partner.id,
        }
        vals.update(extra_vals)
        return cls.env["labour.supply"].create(vals)

    def test_create_creates_related_partner(self):
        worker = self._create_worker(name="Partner Linked Worker")

        self.assertTrue(worker.related_partner_id)
        self.assertEqual(worker.related_partner_id.name, worker.name)
        self.assertEqual(worker.related_partner_id.email, worker.email)

    def test_get_labour_supply_details_counts_ongoing_invoiced_contracts(self):
        self._create_contract(
            from_date=fields.Date.today(),
            to_date=self.next_week,
            state="invoiced",
        )
        self._create_contract(
            from_date=fields.Date.today(),
            to_date=self.next_week,
            state="draft",
        )

        result = self.env["workers.details"].get_labour_supply_details()

        self.assertGreaterEqual(result["ongoing_contract"], 1)

    def test_get_workers_count_returns_available_and_not_available_counts(self):
        self._create_worker(name="Available Worker", state="available")
        self._create_worker(name="Unavailable Worker", state="not_available")

        result = self.env["workers.details"].get_workers_count()

        self.assertIn("Available", result["state"])
        self.assertIn("Not Available", result["state"])
        self.assertGreaterEqual(result["count"][result["state"].index("Available")], 1)
        self.assertGreaterEqual(
            result["count"][result["state"].index("Not Available")], 1
        )

    def test_dashboard_sql_helpers_return_expected_keys(self):
        self._create_worker(name="Dashboard Worker")
        self._create_contract(
            from_date=fields.Date.today(),
            to_date=self.next_week,
            total_amount=300,
            state="invoiced",
        )
        workers = self.env["workers.details"]

        self.assertIn("customer", workers.get_top_customer())
        self.assertIn("skill", workers.get_skills_available())
        self.assertIn("workers", workers.get_workers_available())

    def test_amount_helpers_return_expected_totals_and_series(self):
        self._create_contract(
            from_date=fields.Date.today(),
            to_date=self.next_week,
            total_amount=700,
            state="invoiced",
        )
        workers = self.env["workers.details"]

        self.assertGreaterEqual(
            workers.get_total_invoiced_amount()["invoiced_amount"], 700
        )
        self.assertGreaterEqual(workers.get_expected_amount()["expected_amount"], 700)
        self.assertIn("sequence", workers.get_contract_amount())
        self.assertIn("amount", workers.get_details_amount("daily"))

    def test_contract_count_helpers_return_chart_data(self):
        self._create_contract(state="draft")

        workers = self.env["workers.details"]

        state_result = workers.get_contract_count_state()
        customer_result = workers.get_contract_count_customer()
        self.assertIn("Draft", state_result["state"])
        self.assertIn(self.partner.name, customer_result["name"])
