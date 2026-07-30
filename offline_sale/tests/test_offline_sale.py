# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo.tests.common import TransactionCase


class TestOfflineSale(TransactionCase):

    def setUp(self):
        super().setUp()

        self.partner = self.env["res.partner"].create({
            "name": "Test Customer",
            "email": "test@test.com",
        })

        self.product = self.env["product.product"].create({
            "name": "Test Product",
            "list_price": 100,
            "sale_ok": True,
            "type": "consu",
        })

    def test_create_offline_partner(self):
        """Verify offline customer creation"""
        data = {
            "name": "Offline Customer",
            "email": "offline@test.com",
            "phone": "9999999999",
        }
        partner = self.env["sale.order"]._get_or_create_offline_partner(
            "OFF-1", data
        )
        self.assertTrue(partner)
        self.assertEqual(partner.name, "Offline Customer")
        self.assertEqual(partner.email, "offline@test.com")

    def test_create_sale_order_from_offline(self):
        """Verify offline order creation"""
        order_data = [{
            "uid": "OFF-ORDER-001",
            "partner_id": self.partner.id,
            "state": "draft",
            "lines": [{
                "product_id": self.product.id,
                "qty": 2,
                "price_unit": 100,
            }]
        }]
        result = self.env["sale.order"].create_from_offline(order_data)
        self.assertEqual(
            result["orders"][0]["status"],
            "created"
        )
        order = self.env["sale.order"].search([
            ("offline_uid", "=", "OFF-ORDER-001")
        ])
        self.assertTrue(order)
        self.assertEqual(len(order.order_line), 1)

    def test_duplicate_order_not_created(self):
        """Verify duplicate sync does not create duplicates"""
        order_data = [{
            "uid": "OFF-ORDER-002",
            "partner_id": self.partner.id,
            "state": "draft",
            "lines": [{
                "product_id": self.product.id,
                "qty": 1,
                "price_unit": 100,
            }]
        }]
        self.env["sale.order"].create_from_offline(order_data)
        self.env["sale.order"].create_from_offline(order_data)
        orders = self.env["sale.order"].search([
            ("offline_uid", "=", "OFF-ORDER-002")
        ])
        self.assertEqual(len(orders), 1)

    def test_confirmed_order_creation(self):
        """Verify confirmed offline order"""
        order_data = [{
            "uid": "OFF-ORDER-003",
            "partner_id": self.partner.id,
            "state": "confirmed",
            "lines": [{
                "product_id": self.product.id,
                "qty": 1,
                "price_unit": 100,
            }]
        }]
        self.env["sale.order"].create_from_offline(order_data)
        order = self.env["sale.order"].search([
            ("offline_uid", "=", "OFF-ORDER-003")
        ])
        self.assertEqual(order.state, "sale")

    def test_backend_note_creation(self):
        """Verify backend note posted in chatter"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
        })
        self.env["sale.order"]._post_offline_backend_note(
            order,
            {
                "backend_note": "Test Offline Note"
            }
        )
        message = order.message_ids.filtered(
            lambda m: "Offline Backend Note" in (m.subject or "")
        )
        self.assertTrue(message)

    def test_pending_sale_orders(self):
        """Verify pending order retrieval"""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100,
            })]
        })
        pending_orders = (
            self.env["sale.order"]
            .get_pending_sale_orders()
        )
        self.assertTrue(
            any(x["id"] == order.id for x in pending_orders)
        )

    def test_offline_uid_saved(self):
        """Verify offline UID stored correctly"""
        order_data = [{
            "uid": "OFF-ORDER-004",
            "partner_id": self.partner.id,
            "state": "draft",
            "lines": [{
                "product_id": self.product.id,
                "qty": 1,
                "price_unit": 100,
            }]
        }]
        self.env["sale.order"].create_from_offline(order_data)
        order = self.env["sale.order"].search([
            ("offline_uid", "=", "OFF-ORDER-004")
        ])
        self.assertEqual(
            order.offline_uid,
            "OFF-ORDER-004"
        )

    def test_existing_partner_match_by_email(self):
        """Verify existing partner reused"""
        data = {
            "name": "Duplicate Partner",
            "email": "test@test.com",
        }
        partner = self.env["sale.order"]._get_or_create_offline_partner(
            "OFF-5",
            data
        )
        self.assertEqual(partner.id, self.partner.id)

    def test_order_line_creation(self):
        """Verify order line values"""
        order_data = [{
            "uid": "OFF-ORDER-005",
            "partner_id": self.partner.id,
            "state": "draft",
            "lines": [{
                "product_id": self.product.id,
                "qty": 5,
                "price_unit": 50,
                "discount": 10,
            }]
        }]
        self.env["sale.order"].create_from_offline(order_data)
        order = self.env["sale.order"].search([
            ("offline_uid", "=", "OFF-ORDER-005")
        ])
        line = order.order_line[0]
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(line.price_unit, 50)
        self.assertEqual(line.discount, 10)

    def test_missing_partner_validation(self):
        """Verify missing partner handling"""
        order_data = [{
            "uid": "OFF-ORDER-006",
            "state": "draft",
            "lines": [{
                "product_id": self.product.id,
                "qty": 1,
                "price_unit": 100,
            }]
        }]
        result = self.env["sale.order"].create_from_offline(order_data)
        self.assertEqual(
            result["orders"][0]["status"],
            "error"
        )
