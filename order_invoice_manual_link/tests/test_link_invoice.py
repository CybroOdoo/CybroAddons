# -*- coding: utf-8 -*-

from odoo import Command
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestLinkInvoice(TestSaleCommon):

    def _create_sale_order(self):
        return self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [
                Command.create({
                    "product_id": self.product_a.id,
                    "product_uom_qty": 3.0,
                    "price_unit": 100.0,
                    "tax_ids": [Command.clear()],
                }),
            ],
        })

    def _create_invoice(self, partner, product, link_invoice=True):
        invoice = self.init_invoice(
            "out_invoice",
            partner=partner,
            products=product,
            taxes=[],
        )
        invoice.link_invoice = link_invoice
        return invoice

    def test_action_add_invoices_links_selected_invoice_lines_to_sale_order(self):
        sale_order = self._create_sale_order()
        sale_line = sale_order.order_line
        invoice = self._create_invoice(self.partner_a, self.product_a)
        invoice_line = invoice.invoice_line_ids
        invoice_line.quantity = sale_line.product_uom_qty
        wizard = self.env["link.invoice"].create({
            "sale_order_id": sale_order.id,
            "invoice_ids": [Command.set([invoice.id])],
        })

        wizard.action_add_invoices()

        self.assertEqual(sale_line.qty_invoiced, sale_line.product_uom_qty)
        self.assertIn(invoice_line, sale_line.invoice_lines)
        self.assertIn(sale_line, invoice_line.sale_line_ids)

    def test_action_add_invoices_ignores_unselected_invoices(self):
        sale_order = self._create_sale_order()
        invoice = self._create_invoice(
            self.partner_a,
            self.product_a,
            link_invoice=False,
        )
        wizard = self.env["link.invoice"].create({
            "sale_order_id": sale_order.id,
            "invoice_ids": [Command.set([invoice.id])],
        })

        wizard.action_add_invoices()

        self.assertFalse(invoice.invoice_line_ids.sale_line_ids)

    def test_action_add_invoices_rejects_products_missing_from_sale_order(self):
        sale_order = self._create_sale_order()
        invoice = self._create_invoice(self.partner_a, self.product_b)
        wizard = self.env["link.invoice"].create({
            "sale_order_id": sale_order.id,
            "invoice_ids": [Command.set([invoice.id])],
        })

        with self.assertRaises(ValidationError):
            wizard.action_add_invoices()

    def test_invoice_ids_field_rejects_partner_mismatch(self):
        sale_order = self._create_sale_order()
        invoice = self._create_invoice(self.partner_b, self.product_a)

        with self.assertRaises(ValidationError):
            self.env["link.invoice"].create({
                "sale_order_id": sale_order.id,
                "invoice_ids": [Command.set([invoice.id])],
            })
