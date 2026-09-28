# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestPaymentStatusInSale(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.company_data["product_service_order"]
        cls.invoice_context = {
            "default_journal_id": cls.company_data["default_journal_sale"].id,
        }

    def _create_sale_order(self, price_unit=100.0, quantity=1.0):
        return self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "partner_invoice_id": self.partner_a.id,
            "partner_shipping_id": self.partner_a.id,
            "pricelist_id": self.company_data["default_pricelist"].id,
            "order_line": [Command.create({
                "product_id": self.product.id,
                "product_uom_qty": quantity,
                "price_unit": price_unit,
                "tax_id": False,
            })],
        })

    def _create_posted_invoice(self, order):
        order.action_confirm()
        invoice = order.with_context(**self.invoice_context)._create_invoices()
        invoice.action_post()
        return invoice

    def _register_payment(self, invoice, amount=None):
        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({
            "amount": amount or invoice.amount_total,
        })
        return payment_register._create_payments()

    def test_order_without_invoices_has_no_payment_status(self):
        order = self._create_sale_order()

        self.assertEqual(order.payment_status, "No invoice")
        self.assertEqual(order.invoice_state, "No invoice")
        self.assertEqual(order.amount_due, 0.0)
        self.assertFalse(order.payment_details)

    def test_draft_invoice_keeps_no_invoice_status_and_draft_state(self):
        order = self._create_sale_order()
        order.action_confirm()
        invoice = order.with_context(**self.invoice_context)._create_invoices()
        order.invalidate_recordset()

        self.assertEqual(invoice.state, "draft")
        self.assertEqual(order.payment_status, "No invoice")
        self.assertEqual(order.invoice_state, "draft")
        self.assertEqual(order.amount_due, 0.0)
        self.assertFalse(order.payment_details)

    def test_posted_unpaid_invoice_marks_order_not_paid(self):
        order = self._create_sale_order(price_unit=275.0)
        invoice = self._create_posted_invoice(order)
        order.invalidate_recordset()

        self.assertEqual(order.invoice_state, "posted")
        self.assertEqual(order.payment_status, "Not Paid")
        self.assertEqual(order.amount_due, invoice.amount_total)
        self.assertFalse(order.payment_details)

    def test_partial_payment_updates_status_amount_due_and_details(self):
        order = self._create_sale_order(price_unit=300.0)
        invoice = self._create_posted_invoice(order)

        payment = self._register_payment(
            invoice, amount=invoice.amount_total / 2.0
        )
        order.invalidate_recordset()
        invoice.invalidate_recordset()

        self.assertEqual(invoice.payment_state, "partial")
        self.assertEqual(order.payment_status, "Partially Paid")
        self.assertAlmostEqual(order.amount_due, invoice.amount_residual, places=2)
        self.assertTrue(order.payment_details)
        self.assertEqual(len(order.payment_details["content"]), 1)
        self.assertEqual(
            order.payment_details["content"][0]["account_payment_id"],
            payment.id,
        )

    def test_full_payment_marks_order_paid(self):
        order = self._create_sale_order(price_unit=325.0)
        invoice = self._create_posted_invoice(order)

        self._register_payment(invoice)
        order.invalidate_recordset()
        invoice.invalidate_recordset()

        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        self.assertEqual(
            order.payment_status,
            "Paid" if invoice.payment_state == "paid" else "In Payment",
        )
        self.assertAlmostEqual(order.amount_due, 0.0, places=2)
        self.assertTrue(order.payment_details)

    def test_action_register_payment_targets_related_invoices(self):
        order = self._create_sale_order()
        invoice = self._create_posted_invoice(order)

        action = order.action_register_payment()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.payment.register")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"]["active_model"], "account.move")
        self.assertEqual(action["context"]["active_ids"], invoice.ids)
