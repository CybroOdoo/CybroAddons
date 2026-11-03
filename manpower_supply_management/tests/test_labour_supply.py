# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import datetime
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLabourSupply(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.customer = cls.env["res.partner"].create({"name": "Contract Customer"})
        cls.skill = cls.env["skill.details"].create({"name": "Electrician"})
        cls.worker_1 = cls.env["workers.details"].create({
            "name": "Worker 1",
            "rate": 100,
            "wage": 75,
            "skill_ids": [(6, 0, cls.skill.ids)],
        })
        cls.worker_2 = cls.env["workers.details"].create({
            "name": "Worker 2",
            "rate": 150,
            "wage": 90,
            "skill_ids": [(6, 0, cls.skill.ids)],
        })

    def _create_contract(self, **extra_vals):
        today = fields.Date.today()
        vals = {
            "customer_id": self.customer.id,
            "skill_ids": [(0, 0, {
                "skill_id": self.skill.id,
                "from_date": today,
                "to_date": today + datetime.timedelta(days=2),
                "number_of_labour_required": 1,
            })],
        }
        vals.update(extra_vals)
        return self.env["labour.supply"].create(vals)

    def test_create_assigns_sequence(self):
        contract = self._create_contract()
        self.assertTrue(contract.sequence_number)
        self.assertNotEqual(contract.sequence_number, "New")

    def test_cron_change_state_updates_contracts_and_workers(self):
        today = fields.Date.today()
        expired_contract = self._create_contract(
            from_date=today - datetime.timedelta(days=5),
            to_date=today - datetime.timedelta(days=1),
            state="confirmed",
            workers_ids=[(6, 0, self.worker_1.ids)],
        )
        invoiced_contract = self._create_contract(
            from_date=today,
            to_date=today + datetime.timedelta(days=1),
            state="invoiced",
            workers_ids=[(6, 0, self.worker_2.ids)],
        )
        self.worker_1.state = "not_available"

        self.env["labour.supply"].cron_change_state()

        self.assertEqual(expired_contract.state, "expired")
        self.assertEqual(self.worker_1.state, "available")
        self.assertEqual(self.worker_2.state, "not_available")
        self.assertEqual(invoiced_contract.state, "invoiced")

    def test_state_actions(self):
        contract = self._create_contract(
            state="ready",
            total_amount=500,
            workers_ids=[(6, 0, self.worker_1.ids)],
            view_workers_page=True,
            is_alert=True,
        )

        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")

        contract.action_draft()
        self.assertEqual(contract.state, "draft")
        self.assertFalse(contract.workers_ids)
        self.assertFalse(contract.view_workers_page)
        self.assertFalse(contract.is_alert)
        self.assertEqual(contract.total_amount, 0)

        contract.write({"workers_ids": [(6, 0, self.worker_1.ids)]})
        self.worker_1.state = "not_available"
        contract.action_cancel()
        self.assertEqual(contract.state, "canceled")
        self.assertEqual(self.worker_1.state, "available")

    def test_action_create_invoice_returns_form_action(self):
        contract = self._create_contract(
            from_date=fields.Date.today(),
            to_date=fields.Date.today() + datetime.timedelta(days=1),
            total_amount=300,
            workers_ids=[(6, 0, self.worker_1.ids)],
        )
        fake_invoice = SimpleNamespace(id=987)
        captured_writes = []

        def fake_write(recordset, vals):
            captured_writes.append(vals)
            return True

        with patch.object(type(self.env["account.move"]), "create", autospec=True, return_value=fake_invoice):
            with patch.object(type(contract), "write", autospec=True, side_effect=fake_write):
                action = contract.action_create_invoice()

        self.assertEqual(self.worker_1.state, "not_available")
        self.assertEqual(action["res_id"], 987)
        self.assertEqual(action["res_model"], "account.move")
        self.assertIn({"invoice_id": 987, "state": "invoiced"}, captured_writes)

    def test_action_labour_supply_invoices_filters_by_origin(self):
        contract = self._create_contract()
        action = contract.action_labour_supply_invoices()
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["domain"], [("invoice_origin", "=", contract.sequence_number)])

    def test_action_fetch_validates_and_assigns_workers(self):
        contract = self._create_contract(skill_ids=False)

        with self.assertRaises(ValidationError):
            contract.action_fetch()

        contract.write({
            "skill_ids": [(0, 0, {
                "skill_id": self.skill.id,
                "from_date": fields.Date.today() - datetime.timedelta(days=1),
                "to_date": fields.Date.today(),
                "number_of_labour_required": 1,
            })]
        })
        with self.assertRaises(ValidationError):
            contract.action_fetch()

        contract.skill_ids.unlink()
        start = fields.Date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        contract.write({
            "skill_ids": [(0, 0, {
                "skill_id": self.skill.id,
                "from_date": start,
                "to_date": end,
                "number_of_labour_required": 3,
            })]
        })

        contract.action_fetch()

        self.assertEqual(contract.state, "ready")
        self.assertTrue(contract.view_workers_page)
        self.assertTrue(contract.is_alert)
        self.assertEqual(contract.from_date, start)
        self.assertEqual(contract.to_date, end)
        self.assertEqual(contract.period, 2)
        self.assertEqual(set(contract.workers_ids.ids), {self.worker_1.id, self.worker_2.id})
        self.assertEqual(contract.total_amount, (100 + 150) * 3)

    def test_create_multi_assigns_unique_sequence_to_each_record(self):
        today = fields.Date.today()
        vals = {
            "customer_id": self.customer.id,
            "skill_ids": [(0, 0, {
                "skill_id": self.skill.id,
                "from_date": today,
                "to_date": today + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        }
        contracts = self.env["labour.supply"].create([dict(vals), dict(vals)])
        numbers = contracts.mapped("sequence_number")
        self.assertEqual(len(set(numbers)), 2)
        self.assertNotIn("New", numbers)

    def test_fetch_skips_workers_booked_on_overlapping_dates(self):
        day = fields.Date.today() + datetime.timedelta(days=3)
        line = {
            "skill_id": self.skill.id,
            "from_date": day,
            "to_date": day,
            "number_of_labour_required": 1,
        }
        booked = self._create_contract(
            from_date=day, to_date=day, state="confirmed",
            workers_ids=[(6, 0, self.worker_1.ids)],
            skill_ids=[(0, 0, dict(line))],
        )
        self.assertEqual(booked.workers_ids, self.worker_1)

        # Same day: worker_1 is booked, so worker_2 must be offered.
        same_day = self._create_contract(skill_ids=[(0, 0, dict(line))])
        same_day.action_fetch()
        self.assertEqual(same_day.workers_ids, self.worker_2)

        # A different day: worker_1 is free again.
        other = dict(line, from_date=day + datetime.timedelta(days=1),
                     to_date=day + datetime.timedelta(days=1))
        other_day = self._create_contract(skill_ids=[(0, 0, other)])
        other_day.action_fetch()
        self.assertEqual(other_day.workers_ids, self.worker_1)
