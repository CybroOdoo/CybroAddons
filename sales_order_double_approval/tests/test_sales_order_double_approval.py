# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSalesOrderDoubleApproval(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.config = cls.env["ir.config_parameter"].sudo()

        cls.partner = cls.env["res.partner"].create({
            "name": "Double Approval Customer",
        })
        cls.product = cls.env["product.product"].create({
            "name": "Double Approval Product",
            "type": "consu",
            "list_price": 250.0,
            "taxes_id": [Command.clear()],
        })

        cls.sales_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create({
            "name": "Double Approval Sales User",
            "login": "double_approval_sales_user",
            "email": "double_approval_sales_user@example.com",
            "groups_id": [Command.set(
                cls.env.ref("sales_team.group_sale_salesman").ids
            )],
            "company_id": cls.company.id,
            "company_ids": [Command.set(cls.company.ids)],
        })
        cls.sales_manager = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create({
            "name": "Double Approval Sales Manager",
            "login": "double_approval_sales_manager",
            "email": "double_approval_sales_manager@example.com",
            "groups_id": [Command.set(
                cls.env.ref("sales_team.group_sale_manager").ids
            )],
            "company_id": cls.company.id,
            "company_ids": [Command.set(cls.company.ids)],
        })

    def setUp(self):
        super().setUp()
        self.company.so_double_validation = False
        self.config.set_param("sales_order_double_approval.so_approval", False)
        self.config.set_param("sales_order_double_approval.so_min_amount", 0.0)

    def _configure_approval(self, enabled=True, min_amount=100.0):
        self.company.so_double_validation = enabled
        self.config.set_param("sales_order_double_approval.so_approval", enabled)
        self.config.set_param("sales_order_double_approval.so_min_amount", min_amount)

    def _create_order(self, user, price_unit):
        return self.env["sale.order"].with_user(user).create({
            "partner_id": self.partner.id,
            "order_line": [Command.create({
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": price_unit,
            })],
        })

    def test_salesperson_order_above_threshold_moves_to_approve(self):
        self._configure_approval(enabled=True, min_amount=100.0)
        order = self._create_order(self.sales_user, 250.0)

        result = order.with_user(self.sales_user).action_confirm()
        order.invalidate_recordset()

        self.assertTrue(result)
        self.assertEqual(order.state, "to_approve")

    def test_salesperson_order_at_or_below_threshold_confirms_directly(self):
        self._configure_approval(enabled=True, min_amount=100.0)
        order = self._create_order(self.sales_user, 100.0)

        order.with_user(self.sales_user).action_confirm()
        order.invalidate_recordset()

        self.assertEqual(order.state, "sale")

    def test_sales_manager_can_confirm_order_without_extra_approval(self):
        self._configure_approval(enabled=True, min_amount=100.0)
        order = self._create_order(self.sales_manager, 250.0)

        order.with_user(self.sales_manager).action_confirm()
        order.invalidate_recordset()

        self.assertEqual(order.state, "sale")

    def test_disabled_approval_configuration_skips_to_approve_state(self):
        self._configure_approval(enabled=False, min_amount=100.0)
        order = self._create_order(self.sales_user, 250.0)

        order.with_user(self.sales_user).action_confirm()
        order.invalidate_recordset()

        self.assertEqual(order.state, "sale")

    def test_button_approve_confirms_order_waiting_for_approval(self):
        self._configure_approval(enabled=True, min_amount=100.0)
        order = self._create_order(self.sales_user, 250.0)
        order.with_user(self.sales_user).action_confirm()

        order.with_user(self.sales_manager).button_approve()
        order.invalidate_recordset()

        self.assertEqual(order.state, "sale")

    def test_action_cancel_sets_order_to_cancel(self):
        self._configure_approval(enabled=True, min_amount=100.0)
        order = self._create_order(self.sales_user, 250.0)
        order.with_user(self.sales_user).action_confirm()

        order.with_user(self.sales_manager).action_cancel()
        order.invalidate_recordset()

        self.assertEqual(order.state, "cancel")


@tagged("post_install", "-at_install")
class TestSalesOrderDoubleApprovalSettings(TransactionCase):
    def setUp(self):
        super().setUp()
        self.config = self.env["ir.config_parameter"].sudo()
        self.config.set_param("sales_order_double_approval.so_approval", False)
        self.config.set_param("sales_order_double_approval.so_min_amount", 0.0)

    def test_settings_set_and_get_values(self):
        settings = self.env["res.config.settings"].create({
            "so_approval": True,
            "so_min_amount": 750.0,
        })

        settings.set_values()
        values = self.env["res.config.settings"].get_values()

        self.assertEqual(
            self.config.get_param("sales_order_double_approval.so_approval"),
            "True",
        )
        self.assertEqual(
            float(self.config.get_param("sales_order_double_approval.so_min_amount")),
            750.0,
        )
        self.assertTrue(values["so_approval"])
        self.assertEqual(values["so_min_amount"], 750.0)
