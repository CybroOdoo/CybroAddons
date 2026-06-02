# -*- coding: utf-8 -*-

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPropertyAuction(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref("base.us")
        cls.landlord = cls.env["res.partner"].create({
            "name": "Property Test Landlord",
        })
        cls.customer = cls.env["res.partner"].create({
            "name": "Property Test Customer",
        })
        cls.bidder = cls.env["res.partner"].create({
            "name": "Property Test Bidder",
        })

    def _create_property(self, **extra_vals):
        vals = {
            "name": "Property Test Asset",
            "property_type": "residential",
            "street": "123 Test Street",
            "city": "Test City",
            "country_id": self.country.id,
            "landlord_id": self.landlord.id,
            "sale_rent": "for_auction",
            "unit_price": 250000.0,
            "rent_month": 1500.0,
        }
        vals.update(extra_vals)
        return self.env["property.property"].create(vals)

    def _create_auction(self, **extra_vals):
        property_id = extra_vals.pop("property_id", None) or self._create_property(
            sale_rent="for_auction",
            state="available",
        )
        now = fields.Datetime.now()
        vals = {
            "property_id": property_id.id,
            "responsible_id": self.env.user.id,
            "bid_start_price": 100000.0,
            "start_time": fields.Datetime.subtract(now, hours=1),
            "end_time": fields.Datetime.add(now, hours=1),
        }
        vals.update(extra_vals)
        return self.env["property.auction"].create(vals)

    def test_create_assigns_sequence(self):
        auction = self._create_auction()

        self.assertNotEqual(auction.auction_seq, "New")

    def test_constraint_rejects_end_before_start(self):
        now = fields.Datetime.now()

        with self.assertRaises(ValidationError):
            self._create_auction(
                start_time=fields.Datetime.add(now, hours=1),
                end_time=fields.Datetime.subtract(now, hours=1),
            )

    def test_state_actions(self):
        auction = self._create_auction()

        auction.action_confirm()
        self.assertEqual(auction.state, "confirmed")

        auction.action_start()
        self.assertEqual(auction.state, "started")

        auction.action_cancel()
        self.assertEqual(auction.state, "canceled")

    def test_action_end_selects_highest_bidder(self):
        auction = self._create_auction(participant_ids=[
            (0, 0, {"partner_id": self.customer.id, "bid_amount": 125000.0}),
            (0, 0, {"partner_id": self.bidder.id, "bid_amount": 130000.0}),
        ])

        auction.action_end()

        self.assertEqual(auction.state, "ended")
        self.assertEqual(auction.auction_winner_id, self.bidder)
        self.assertEqual(auction.final_price, 130000.0)

    def test_action_create_sale_order_creates_property_sale(self):
        auction = self._create_auction(participant_ids=[
            (0, 0, {"partner_id": self.bidder.id, "bid_amount": 130000.0}),
        ])
        auction.action_end()

        auction.action_create_sale_order()

        sale = self.env["property.sale"].search([
            ("property_id", "=", auction.property_id.id),
            ("partner_id", "=", self.bidder.id),
        ])
        self.assertTrue(sale)
        self.assertTrue(auction.sold)

    def test_action_view_sale_order(self):
        auction = self._create_auction()

        action = auction.action_view_sale_order()

        self.assertEqual(action["res_model"], "property.sale")
        self.assertEqual(action["domain"], [
            ("property_id", "=", auction.property_id.id),
        ])
