# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPropertyProperty(TransactionCase):

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

    def _create_sale(self, **extra_vals):
        property_id = extra_vals.pop("property_id", None) or self._create_property(
            sale_rent="for_sale",
            state="available",
            unit_price=300000.0,
        )
        vals = {
            "property_id": property_id.id,
            "partner_id": self.customer.id,
            "order_date": fields.Date.today(),
        }
        vals.update(extra_vals)
        return self.env["property.sale"].create(vals)

    def test_create_assigns_sequence(self):
        property_id = self._create_property()

        self.assertNotEqual(property_id.code, "New")

    def test_compute_total_sq_feet(self):
        property_id = self._create_property(area_measurement_ids=[
            (0, 0, {"name": "Room A", "length": 10.0, "width": 10.0}),
            (0, 0, {"name": "Room B", "length": 5.0, "width": 8.0}),
        ])

        self.assertEqual(property_id.total_sq_feet, 140.0)

    def test_onchange_address_sets_coordinates_from_geocoder(self):
        property_id = self._create_property()
        geocoder = self.env["base.geocoder"]

        with patch.object(type(geocoder), "geo_query_address",
                          return_value="test query"), \
                patch.object(type(geocoder), "geo_find",
                             return_value=(11.25, 75.78)):
            property_id._onchange_address()

        self.assertEqual(property_id.latitude, 11.25)
        self.assertEqual(property_id.longitude, 75.78)

    def test_action_get_map_returns_map_url(self):
        property_id = self._create_property(latitude=10.0, longitude=20.0)

        action = property_id.action_get_map()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], "/map/10.0/20.0")

    def test_action_available_sets_state(self):
        property_id = self._create_property(state="draft")

        property_id.action_available()

        self.assertEqual(property_id.state, "available")

    def test_sale_and_rental_view_actions(self):
        sale = self._create_sale()
        sale.property_id.sale_id = sale.id

        sale_action = sale.property_id.action_property_sale_view()
        rental_action = sale.property_id.action_property_rental_view()

        self.assertEqual(sale_action["res_model"], "property.sale")
        self.assertEqual(sale_action["res_id"], sale.id)
        self.assertEqual(rental_action["res_model"], "property.rental")
        self.assertEqual(rental_action["domain"], [
            ("property_id", "=", sale.property_id.id),
        ])
