from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLabourSupply(TransactionCase):
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
        cls.today = fields.Date.today()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

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

    @classmethod
    def _create_contract_with_skill(cls, required=1, **extra_vals):
        skill_vals = {
            "skill_id": cls.skill.id,
            "number_of_labour_required": required,
            "from_date": cls.tomorrow,
            "to_date": cls.next_week,
        }
        vals = {
            "customer_id": cls.partner.id,
            "skill_ids": [(0, 0, skill_vals)],
        }
        vals.update(extra_vals)
        return cls.env["labour.supply"].create(vals)

    def test_create_assigns_sequence_number(self):
        contract = self._create_contract()

        self.assertNotEqual(contract.sequence_number, "New")

    def test_action_fetch_assigns_available_workers_and_amount(self):
        worker = self._create_worker(rate=125)
        contract = self._create_contract_with_skill(required=1)

        contract.action_fetch()

        self.assertEqual(contract.state, "ready")
        self.assertEqual(contract.workers_ids, worker)
        self.assertTrue(contract.view_workers_page)
        self.assertEqual(contract.from_date, self.tomorrow)
        self.assertEqual(contract.to_date, self.next_week)
        self.assertEqual(contract.total_amount, 125 * 7)

    def test_action_fetch_requires_skill_lines(self):
        contract = self._create_contract()

        with self.assertRaisesRegex(ValidationError, "Enter Skill Required"):
            contract.action_fetch()

    def test_action_fetch_rejects_invalid_skill_dates(self):
        contract = self._create_contract_with_skill(
            skill_ids=[(0, 0, {
                "skill_id": self.skill.id,
                "number_of_labour_required": 1,
                "from_date": self.next_week,
                "to_date": self.tomorrow,
            })],
        )

        with self.assertRaisesRegex(ValidationError, "Invalid start date"):
            contract.action_fetch()

    def test_action_fetch_rejects_insufficient_workers(self):
        contract = self._create_contract_with_skill(required=2)
        self._create_worker()

        with self.assertRaisesRegex(ValidationError, "Insufficient workers"):
            contract.action_fetch()

    def test_action_fetch_excludes_workers_on_overlapping_contracts(self):
        busy_worker = self._create_worker(name="Busy Worker")
        self._create_worker(name="Free Worker")
        existing_contract = self._create_contract(
            from_date=self.tomorrow,
            to_date=self.next_week,
            state="confirmed",
            workers_ids=[(6, 0, busy_worker.ids)],
        )
        contract = self._create_contract_with_skill(required=1)

        contract.action_fetch()

        self.assertNotIn(busy_worker, contract.workers_ids)
        self.assertEqual(existing_contract.workers_ids, busy_worker)

    def test_action_confirm_requires_workers(self):
        contract = self._create_contract()

        with self.assertRaisesRegex(ValidationError, "without assigning workers"):
            contract.action_confirm()

    def test_action_confirm_sets_confirmed_state(self):
        worker = self._create_worker()
        contract = self._create_contract(workers_ids=[(6, 0, worker.ids)])

        contract.action_confirm()

        self.assertEqual(contract.state, "confirmed")

    def test_action_draft_rejects_invoiced_contract(self):
        contract = self._create_contract(state="invoiced")

        with self.assertRaisesRegex(ValidationError, "invoiced contract"):
            contract.action_draft()

    def test_action_draft_clears_assignment_fields(self):
        worker = self._create_worker()
        contract = self._create_contract(
            state="ready",
            workers_ids=[(6, 0, worker.ids)],
            total_amount=500,
            view_workers_page=True,
            is_alert=True,
        )

        contract.action_draft()

        self.assertEqual(contract.state, "draft")
        self.assertFalse(contract.workers_ids)
        self.assertFalse(contract.total_amount)
        self.assertFalse(contract.view_workers_page)
        self.assertFalse(contract.is_alert)

    def test_action_cancel_releases_workers(self):
        worker = self._create_worker(state="not_available")
        contract = self._create_contract(workers_ids=[(6, 0, worker.ids)])

        contract.action_cancel()

        self.assertEqual(contract.state, "canceled")
        self.assertEqual(worker.state, "available")

    def test_action_create_invoice_requires_workers(self):
        contract = self._create_contract()

        with self.assertRaisesRegex(ValidationError, "without assigned workers"):
            contract.action_create_invoice()

    def test_action_labour_supply_invoices_returns_filtered_action(self):
        contract = self._create_contract()

        action = contract.action_labour_supply_invoices()

        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["domain"], [
            ("invoice_origin", "=", contract.sequence_number)
        ])

    def test_cron_change_state_expires_old_contract_and_releases_worker(self):
        worker = self._create_worker(state="not_available")
        yesterday = fields.Date.today() - timedelta(days=1)
        old_day = fields.Date.today() - timedelta(days=3)
        contract = self._create_contract(
            from_date=old_day,
            to_date=yesterday,
            state="confirmed",
            workers_ids=[(6, 0, worker.ids)],
        )

        self.env["labour.supply"].cron_change_state()

        self.assertEqual(contract.state, "expired")
        self.assertEqual(worker.state, "available")

    def test_cron_change_state_marks_today_invoiced_workers_busy(self):
        worker = self._create_worker()
        contract = self._create_contract(
            from_date=fields.Date.today(),
            to_date=self.next_week,
            state="invoiced",
            workers_ids=[(6, 0, worker.ids)],
        )

        self.env["labour.supply"].cron_change_state()

        self.assertEqual(contract.state, "invoiced")
        self.assertEqual(worker.state, "not_available")
