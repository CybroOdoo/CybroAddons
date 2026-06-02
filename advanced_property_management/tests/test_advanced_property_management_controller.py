# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from odoo.addons.advanced_property_management.controllers import (
    advanced_property_management as controller_module,
)


class TestPropertyController(TransactionCase):

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
            "sale_rent": "for_sale",
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

    def test_property_route_renders_property_list(self):
        property_id = self._create_property()
        controller = controller_module.PropertyController()

        def _render(template, qcontext):
            return {"template": template, "qcontext": qcontext}

        with patch.object(controller_module, "request",
                          SimpleNamespace(env=self.env, render=_render)):
            result = controller.property.__wrapped__(controller)

        self.assertEqual(
            result["template"],
            "advanced_property_management.property_view",
        )
        self.assertIn(property_id, result["qcontext"]["property_ids"])

    def test_property_item_route_renders_single_property(self):
        property_id = self._create_property()
        controller = controller_module.PropertyController()

        def _render(template, qcontext):
            return {"template": template, "qcontext": qcontext}

        with patch.object(controller_module, "request",
                          SimpleNamespace(env=self.env, render=_render)):
            result = controller.property_item.__wrapped__(
                controller,
                property_id.id,
            )

        self.assertEqual(
            result["template"],
            "advanced_property_management.property_view_item",
        )
        self.assertEqual(result["qcontext"]["property_id"], property_id)

    def test_redirect_map_returns_google_maps_redirect(self):
        controller = controller_module.PropertyController()

        response = controller.redirect_map("10.0", "20.0")

        self.assertEqual(response.status_code, 302)
        self.assertIn("https://www.google.com/maps/@10.0,20.0", response.location)

    def test_auction_route_groups_auctions(self):
        auction = self._create_auction(participant_ids=[
            (0, 0, {"partner_id": self.customer.id, "bid_amount": 120000.0}),
            (0, 0, {"partner_id": self.bidder.id, "bid_amount": 125000.0}),
        ])
        auction.action_confirm()
        controller = controller_module.PropertyController()
        captured = {}

        class FakeResponse:
            def __init__(self, template=None, qcontext=None):
                captured["template"] = template
                captured["qcontext"] = qcontext

            def render(self):
                return captured

        with patch.object(controller_module, "request",
                          SimpleNamespace(env=self.env)), \
                patch.object(controller_module.http, "Response", FakeResponse):
            result = controller.auction()

        self.assertEqual(
            result["template"],
            "advanced_property_management.auction_view",
        )
        self.assertEqual(result["qcontext"]["confirmed"][0]["id"], auction.id)
        self.assertEqual(result["qcontext"]["confirmed"][0]["last"], 125000.0)

    def test_auction_bid_submit_creates_participant_line(self):
        auction = self._create_auction()
        controller = controller_module.PropertyController()

        with patch.object(controller_module, "request",
                          SimpleNamespace(env=self.env)):
            result = controller.auction_bid_submit(auction.id, bid_amount="155000")

        self.assertEqual(result, {"message": "success"})
        line = auction.participant_ids.filtered(
            lambda participant: participant.partner_id == self.env.user.partner_id
        )
        self.assertTrue(line)
        self.assertEqual(line.bid_amount, 155000.0)
        self.assertLessEqual(line.bid_time, fields.Datetime.now())
