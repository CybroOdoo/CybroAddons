# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWorkersDetails(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.skill_1 = cls.env["skill.details"].create({"name": "Welder"})
        cls.skill_2 = cls.env["skill.details"].create({"name": "Plumber"})
        cls.customer_1 = cls.env["res.partner"].create({"name": "Customer A", "email": "a@example.com"})
        cls.customer_2 = cls.env["res.partner"].create({"name": "Customer B", "email": "b@example.com"})
        cls.worker_model = cls.env["workers.details"]
        cls.worker_1 = cls.worker_model.create({
            "name": "Alpha",
            "phone_number": "111",
            "email": "alpha@example.com",
            "rate": 100,
            "wage": 80,
            "skill_ids": [(6, 0, cls.skill_1.ids)],
        })
        cls.worker_2 = cls.worker_model.create({
            "name": "Beta",
            "phone_number": "222",
            "email": "beta@example.com",
            "rate": 150,
            "wage": 90,
            "state": "not_available",
            "skill_ids": [(6, 0, (cls.skill_1 + cls.skill_2).ids)],
        })
        today = fields.Date.today()
        next_month_day = today + relativedelta(months=1, day=min(today.day, 28))
        cls.contract_daily = cls.env["labour.supply"].create({
            "customer_id": cls.customer_1.id,
            "from_date": today,
            "to_date": today + datetime.timedelta(days=1),
            "state": "invoiced",
            "total_amount": 250,
            "workers_ids": [(6, 0, cls.worker_1.ids)],
            "skill_ids": [(0, 0, {
                "skill_id": cls.skill_1.id,
                "from_date": today,
                "to_date": today + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        })
        cls.contract_confirmed = cls.env["labour.supply"].create({
            "customer_id": cls.customer_1.id,
            "from_date": next_month_day,
            "to_date": next_month_day + datetime.timedelta(days=1),
            "state": "confirmed",
            "total_amount": 350,
            "workers_ids": [(6, 0, cls.worker_2.ids)],
            "skill_ids": [(0, 0, {
                "skill_id": cls.skill_2.id,
                "from_date": next_month_day,
                "to_date": next_month_day + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        })
        cls.contract_ready = cls.env["labour.supply"].create({
            "customer_id": cls.customer_2.id,
            "from_date": today + datetime.timedelta(days=2),
            "to_date": today + datetime.timedelta(days=3),
            "state": "ready",
            "total_amount": 450,
            "skill_ids": [(0, 0, {
                "skill_id": cls.skill_1.id,
                "from_date": today + datetime.timedelta(days=2),
                "to_date": today + datetime.timedelta(days=3),
                "number_of_labour_required": 1,
            })],
        })

    def test_create_creates_related_partner(self):
        self.assertTrue(self.worker_1.related_partner_id)
        self.assertEqual(self.worker_1.related_partner_id.name, "Alpha")
        self.assertEqual(self.worker_1.related_partner_id.phone, "111")

    def test_dashboard_count_and_amount_methods(self):
        self.assertEqual(
            self.worker_model.get_labour_supply_details(),
            {"ongoing_contract": 1},
        )
        workers_count = self.worker_model.get_workers_count()
        self.assertEqual(workers_count["state"], ["Not Available", "Available"])
        self.assertEqual(workers_count["count"], [1, 1])
        self.assertEqual(
            self.worker_model.get_total_invoiced_amount(),
            {"invoiced_amount": 250},
        )
        self.assertEqual(
            self.worker_model.get_expected_amount(),
            {"expected_amount": 600},
        )
        contract_state = self.worker_model.get_contract_count_state()
        self.assertEqual(contract_state["count"], [0, 1, 1, 1, 0, 0])

    def test_dashboard_sql_and_grouping_methods(self):
        top_customer = self.worker_model.get_top_customer()["customer"]
        self.assertEqual(top_customer[0]["name"], "Customer A")
        self.assertEqual(top_customer[0]["count"], 2)

        skills = self.worker_model.get_skills_available()["skill"]
        self.assertEqual({item["name"] for item in skills}, {"Welder", "Plumber"})

        workers = self.worker_model.get_workers_available()["workers"]
        self.assertEqual([item["name"] for item in workers], ["Alpha"])

        contract_amount = self.worker_model.get_contract_amount()
        self.assertEqual(set(contract_amount["sequence"]), {
            self.contract_daily.sequence_number,
            self.contract_confirmed.sequence_number,
            self.contract_ready.sequence_number,
        })
        self.assertEqual(set(contract_amount["amount"]), {250, 350, 450})

        customer_count = self.worker_model.get_contract_count_customer()
        self.assertEqual(dict(zip(customer_count["name"], customer_count["count"])), {
            "Customer A": 2,
            "Customer B": 1,
        })

    def test_get_details_amount_filters_periods(self):
        daily = self.worker_model.get_details_amount("daily")
        self.assertEqual(daily["sequence"], [self.contract_daily.sequence_number])
        self.assertEqual(daily["amount"], [250])

        monthly = self.worker_model.get_details_amount("monthly")
        self.assertIn(self.contract_daily.sequence_number, monthly["sequence"])
        self.assertIn(self.contract_ready.sequence_number, monthly["sequence"])

        yearly = self.worker_model.get_details_amount("yearly")
        self.assertEqual(set(yearly["sequence"]), {
            self.contract_daily.sequence_number,
            self.contract_confirmed.sequence_number,
            self.contract_ready.sequence_number,
        })
        self.assertEqual(set(yearly["amount"]), {250, 350, 450})
