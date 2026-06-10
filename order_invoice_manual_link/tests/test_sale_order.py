# -*- coding: utf-8 -*-

from odoo import Command
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSaleOrder(TestSaleCommon):

    def test_action_open_invoices_returns_link_wizard_with_unlinked_partner_invoices(self):
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [
                Command.create({
                    "product_id": self.product_a.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 100.0,
                    "tax_ids": [Command.clear()],
                }),
            ],
        })
        unlinked_invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            products=self.product_a,
            taxes=[],
        )
        linked_invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            products=self.product_a,
            taxes=[],
        )
        linked_invoice.invoice_line_ids.sale_line_ids = sale_order.order_line
        other_partner_invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_b,
            products=self.product_a,
            taxes=[],
        )

        action = sale_order.action_open_invoices()
        invoice_ids = action["context"]["default_invoice_ids"][0][2]

        self.assertEqual(action["res_model"], "link.invoice")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"]["default_sale_order_id"], sale_order.id)
        self.assertIn(unlinked_invoice.id, invoice_ids)
        self.assertNotIn(linked_invoice.id, invoice_ids)
        self.assertNotIn(other_partner_invoice.id, invoice_ids)
