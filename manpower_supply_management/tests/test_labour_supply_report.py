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

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLabourSupplyReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        customer = cls.env["res.partner"].create({"name": "Report Customer"})
        skill = cls.env["skill.details"].create({"name": "Assembler"})
        cls.contract = cls.env["labour.supply"].create({
            "customer_id": customer.id,
            "from_date": fields.Date.today(),
            "to_date": fields.Date.today() + datetime.timedelta(days=1),
            "skill_ids": [(0, 0, {
                "skill_id": skill.id,
                "from_date": fields.Date.today(),
                "to_date": fields.Date.today() + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        })

    def test_get_report_values_returns_selected_contracts(self):
        report = self.env["report.manpower_supply_management.form_print_labour_supply"]
        result = report._get_report_values(self.contract.ids)
        self.assertEqual(result["docs_ids"], self.contract.ids)
        self.assertEqual(result["labour_supply"], self.contract)
