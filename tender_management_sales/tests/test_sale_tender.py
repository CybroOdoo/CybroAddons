# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
import logging

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleTender(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        _logger.info("Setting up tender_management_sales test data")

        cls.partner = cls.env["res.partner"].create({
            "name": "Tender Customer",
        })
        cls.alternative_partner = cls.env["res.partner"].create({
            "name": "Alternative Customer",
        })

        cls.product_1 = cls.env["product.product"].create({
            "name": "Tender Product 1",
            "type": "consu",
            "list_price": 100.0,
            "sale_ok": True,
        })
        cls.product_2 = cls.env["product.product"].create({
            "name": "Tender Product 2",
            "type": "consu",
            "list_price": 200.0,
            "sale_ok": True,
        })

        cls.tender_type_exclusive = cls.env["sale.tender.type"].create({
            "name": "Exclusive Type",
            "exclusive": "exclusive",
            "quantity_copy": "copy",
            "line_copy": "copy",
        })
        cls.tender_type_multiple = cls.env["sale.tender.type"].create({
            "name": "Multiple Type",
            "exclusive": "multiple",
            "quantity_copy": "copy",
            "line_copy": "copy",
        })
        cls.tender_type_no_qty = cls.env["sale.tender.type"].create({
            "name": "No Qty Copy Type",
            "exclusive": "multiple",
            "quantity_copy": "none",
            "line_copy": "copy",
        })
        cls.tender_type_no_lines = cls.env["sale.tender.type"].create({
            "name": "No Line Copy Type",
            "exclusive": "multiple",
            "quantity_copy": "copy",
            "line_copy": "none",
        })

    def _log_test(self, message):
        _logger.info("tender_management_sales test: %s", message)

    def _create_tender(self, tender_type, lines=None, description="Tender Note"):
        if lines is None:
            lines = [Command.create({
                "product_id": self.product_1.id,
                "product_qty": 10,
                "price_unit": 90.0,
            })]
        return self.env["sale.tender"].create({
            "type_id": tender_type.id,
            "customer_id": self.partner.id,
            "description": description,
            "line_ids": lines,
        })

    def _create_order_with_line(self, partner, product, qty=1.0, price=100.0, name=None):
        return self.env["sale.order"].create({
            "partner_id": partner.id,
            "order_line": [Command.create({
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "price_unit": price,
                "name": name or product.name,
            })],
        })

    def _create_tender_quotation(self, tender, partner=None):
        partner = partner or self.partner
        so = self.env["sale.order"].create({
            "partner_id": partner.id,
            "tender_id": tender.id,
        })
        so._onchange_tender_id()
        return so

    def test_01_confirm_tender_requires_lines_and_sets_sequence(self):
        self._log_test("test_01_confirm_tender_requires_lines_and_sets_sequence started")

        tender = self.env["sale.tender"].create({
            "type_id": self.tender_type_multiple.id,
            "customer_id": self.partner.id,
        })
        self.assertEqual(tender.state, "draft")

        with self.assertRaises(UserError):
            tender.action_in_progress()

        self.env["sale.tender.line"].create({
            "tender_id": tender.id,
            "product_id": self.product_1.id,
            "product_qty": 5,
            "price_unit": 100.0,
        })
        tender.action_in_progress()

        self.assertEqual(tender.state, "in_progress")
        self.assertNotEqual(tender.name, "New")

        self._log_test("test_01_confirm_tender_requires_lines_and_sets_sequence finished")

    def test_02_tender_open_cancel_and_reset_flow(self):
        self._log_test("test_02_tender_open_cancel_and_reset_flow started")

        tender = self._create_tender(self.tender_type_multiple)
        tender.action_in_progress()
        tender.action_open()
        self.assertEqual(tender.state, "open")

        tender.action_cancel()
        self.assertEqual(tender.state, "cancel")

        tender.action_reset_to_draft()
        self.assertEqual(tender.state, "draft")

        self._log_test("test_02_tender_open_cancel_and_reset_flow finished")

    def test_03_action_done_blocks_draft_sale_orders(self):
        self._log_test("test_03_action_done_blocks_draft_sale_orders started")

        tender = self._create_tender(self.tender_type_multiple)
        tender.action_in_progress()

        quotation = self._create_tender_quotation(tender)
        self.assertEqual(quotation.state, "draft")

        with self.assertRaises(UserError):
            tender.action_done()

        quotation.action_cancel()
        tender.action_done()
        self.assertEqual(tender.state, "done")

        self._log_test("test_03_action_done_blocks_draft_sale_orders finished")

    def test_04_onchange_tender_copies_core_values(self):
        self._log_test("test_04_onchange_tender_copies_core_values started")

        tender = self._create_tender(
            self.tender_type_multiple,
            description="Terms from Tender",
        )
        tender.action_in_progress()

        quotation = self._create_tender_quotation(tender)

        self.assertEqual(quotation.partner_id, self.partner)
        self.assertEqual(quotation.company_id, tender.company_id)
        self.assertEqual(quotation.currency_id, tender.currency_id)
        self.assertEqual(quotation.note, tender.description)
        self.assertIn(tender.name, quotation.origin or "")
        self.assertEqual(len(quotation.order_line), 1)
        self.assertEqual(quotation.order_line.product_id, self.product_1)
        self.assertEqual(quotation.order_line.product_uom_qty, 10.0)
        self.assertEqual(quotation.order_line.price_unit, 90.0)

        self._log_test("test_04_onchange_tender_copies_core_values finished")

    def test_05_onchange_tender_respects_quantity_copy_none(self):
        self._log_test("test_05_onchange_tender_respects_quantity_copy_none started")

        tender = self._create_tender(self.tender_type_no_qty)
        tender.action_in_progress()

        quotation = self._create_tender_quotation(tender)

        self.assertEqual(len(quotation.order_line), 1)
        self.assertEqual(quotation.order_line.product_uom_qty, 0.0)

        self._log_test("test_05_onchange_tender_respects_quantity_copy_none finished")

    def test_06_onchange_tender_respects_line_copy_none(self):
        self._log_test("test_06_onchange_tender_respects_line_copy_none started")

        tender = self._create_tender(self.tender_type_no_lines)
        tender.action_in_progress()

        quotation = self._create_tender_quotation(tender)

        self.assertFalse(quotation.order_line)
        self.assertEqual(quotation.note, tender.description)

        self._log_test("test_06_onchange_tender_respects_line_copy_none finished")

    def test_07_exclusive_tender_confirms_one_and_cancels_others(self):
        self._log_test("test_07_exclusive_tender_confirms_one_and_cancels_others started")

        tender = self._create_tender(self.tender_type_exclusive)
        tender.action_in_progress()

        so1 = self._create_tender_quotation(tender)
        so2 = self._create_tender_quotation(tender)

        so1.action_confirm()

        self.assertEqual(so1.state, "sale")
        self.assertEqual(so2.state, "cancel")
        self.assertEqual(tender.state, "done")

        self._log_test("test_07_exclusive_tender_confirms_one_and_cancels_others finished")

    def test_08_multiple_tender_keeps_tender_open_after_confirm(self):
        self._log_test("test_08_multiple_tender_keeps_tender_open_after_confirm started")

        tender = self._create_tender(self.tender_type_multiple)
        tender.action_in_progress()

        so1 = self._create_tender_quotation(tender)
        so1.action_confirm()

        self.assertEqual(so1.state, "sale")
        self.assertEqual(tender.state, "in_progress")

        self._log_test("test_08_multiple_tender_keeps_tender_open_after_confirm finished")

    def test_09_alternative_wizard_creates_grouped_quotation(self):
        self._log_test("test_09_alternative_wizard_creates_grouped_quotation started")

        origin_so = self._create_order_with_line(
            self.partner,
            self.product_1,
            qty=2.0,
            price=120.0,
            name="Origin Line",
        )

        wizard = self.env["sale.tender.create.alternative"].create({
            "origin_so_id": origin_so.id,
            "partner_id": self.alternative_partner.id,
            "copy_products": True,
        })
        action = wizard.action_create_alternative()
        alternative_so = self.env["sale.order"].browse(action["res_id"])

        self.assertTrue(alternative_so.exists())
        self.assertEqual(alternative_so.partner_id, self.alternative_partner)
        self.assertTrue(origin_so.sale_group_id)
        self.assertEqual(origin_so.sale_group_id, alternative_so.sale_group_id)
        self.assertEqual(len(origin_so.sale_group_id.order_ids), 2)
        self.assertEqual(len(alternative_so.order_line), 1)
        self.assertEqual(alternative_so.order_line.product_id, self.product_1)
        self.assertEqual(alternative_so.order_line.product_uom_qty, 2.0)
        self.assertEqual(alternative_so.order_line.name, "Origin Line")

        self._log_test("test_09_alternative_wizard_creates_grouped_quotation finished")

    def test_10_compare_action_contains_alternative_orders(self):
        self._log_test("test_10_compare_action_contains_alternative_orders started")

        origin_so = self._create_order_with_line(self.partner, self.product_1, qty=1.0, price=100.0)
        wizard = self.env["sale.tender.create.alternative"].create({
            "origin_so_id": origin_so.id,
            "partner_id": self.alternative_partner.id,
            "copy_products": True,
        })
        action = wizard.action_create_alternative()
        alternative_so = self.env["sale.order"].browse(action["res_id"])

        compare_action = origin_so.action_compare_alternative_lines()

        self.assertEqual(compare_action["res_model"], "sale.order.line")
        self.assertEqual(compare_action["view_mode"], "list")
        self.assertEqual(compare_action["context"]["sale_order_id"], origin_so.id)
        self.assertEqual(
            set(compare_action["domain"][0][2]),
            {origin_so.id, alternative_so.id},
        )

        self._log_test("test_10_compare_action_contains_alternative_orders finished")

    def test_11_get_tender_best_lines_returns_highest_priced_line(self):
        self._log_test("test_11_get_tender_best_lines_returns_highest_priced_line started")

        origin_so = self._create_order_with_line(
            self.partner,
            self.product_1,
            qty=1.0,
            price=100.0,
            name="Origin Best Line",
        )
        wizard = self.env["sale.tender.create.alternative"].create({
            "origin_so_id": origin_so.id,
            "partner_id": self.alternative_partner.id,
            "copy_products": False,
        })
        action = wizard.action_create_alternative()
        alternative_so = self.env["sale.order"].browse(action["res_id"])

        self.env["sale.order.line"].create({
            "order_id": alternative_so.id,
            "product_id": self.product_1.id,
            "product_uom_qty": 1.0,
            "product_uom": self.product_1.uom_id.id,
            "price_unit": 150.0,
            "name": "Alternative Best Line",
        })

        best_price_ids, best_unit_ids = origin_so.get_tender_best_lines()

        self.assertIn(alternative_so.order_line.id, best_price_ids)
        self.assertIn(alternative_so.order_line.id, best_unit_ids)
        self.assertNotIn(origin_so.order_line.id, best_price_ids)

        self._log_test("test_11_get_tender_best_lines_returns_highest_priced_line finished")

    def test_12_action_choose_clears_other_quantities(self):
        self._log_test("test_12_action_choose_clears_other_quantities started")

        origin_so = self._create_order_with_line(self.partner, self.product_1, qty=3.0, price=100.0)
        wizard = self.env["sale.tender.create.alternative"].create({
            "origin_so_id": origin_so.id,
            "partner_id": self.alternative_partner.id,
            "copy_products": True,
        })
        action = wizard.action_create_alternative()
        alternative_so = self.env["sale.order"].browse(action["res_id"])

        origin_so.order_line.action_choose()

        self.assertEqual(origin_so.order_line.product_uom_qty, 3.0)
        self.assertEqual(alternative_so.order_line.product_uom_qty, 0.0)

        self._log_test("test_12_action_choose_clears_other_quantities finished")

    def test_13_action_clear_quantities_returns_notification_for_confirmed_orders(self):
        self._log_test("test_13_action_clear_quantities_returns_notification_for_confirmed_orders started")

        sale_order = self._create_order_with_line(
            self.partner,
            self.product_2,
            qty=2.0,
            price=250.0,
            name="Confirmed Line",
        )
        sale_order.action_confirm()

        result = sale_order.order_line.action_clear_quantities()

        self.assertEqual(sale_order.order_line.product_uom_qty, 2.0)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["title"], "Some not cleared")

        self._log_test("test_13_action_clear_quantities_returns_notification_for_confirmed_orders finished")
