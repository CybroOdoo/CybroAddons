# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install", "order_invoice_manual_link")
class TestAccountMove(TestSaleCommon):

    def test_action_unlink_invoice_removes_sale_line_links(self):
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [
                Command.create({
                    "product_id": self.product_a.id,
                    "product_uom_qty": 2.0,
                    "price_unit": 100.0,
                    "tax_ids": [Command.clear()],
                }),
            ],
        })
        sale_line = sale_order.order_line
        invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            products=self.product_a,
            taxes=[],
        )
        invoice.invoice_line_ids.sale_line_ids = sale_line

        invoice.action_unlink_invoice()

        self.assertFalse(invoice.invoice_line_ids.sale_line_ids)
