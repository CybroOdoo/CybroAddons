# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMealsPlanning(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_method = cls.env["pos.payment.method"].create({
            "name": "Meals Planning Payment",
        })
        cls.pos_config = cls.env["pos.config"].create({
            "name": "Meals Planning POS",
            "payment_method_ids": [(6, 0, cls.payment_method.ids)],
        })
        cls.pos_session = cls.env["pos.session"].create({
            "config_id": cls.pos_config.id,
            "user_id": cls.env.uid,
        })

    def _create_plan(self, **extra_vals):
        vals = {
            "name": "Breakfast",
            "pos_ids": [(6, 0, self.pos_session.ids)],
            "time_from": 8.0,
            "time_to": 10.0,
        }
        vals.update(extra_vals)
        return self.env["meals.planning"].create(vals)

    def test_load_pos_data_helpers(self):
        model = self.env["meals.planning"]

        self.assertIn("menu_product_ids", model._load_pos_data_fields(False))
        self.assertEqual(model._load_pos_data_domain({}, False), [])
        data = {"pos.session": [{"id": self.pos_session.id}]}
        self.assertEqual(
            model._load_pos_data_domain(data, False),
            [("pos_ids", "in", [self.pos_session.id])],
        )

    def test_time_range_validation(self):
        with self.assertRaises(ValidationError):
            self._create_plan(time_from=12.0, time_to=10.0)

        with self.assertRaises(ValidationError):
            self._create_plan(time_from=23.0, time_to=25.0)

    def test_activate_and_deactivate_meals_plan(self):
        plan = self._create_plan()

        plan.action_activate_meals_plan()
        self.assertEqual(plan.state, "activated")

        plan.action_deactivate_meals_plan()
        self.assertEqual(plan.state, "deactivated")
