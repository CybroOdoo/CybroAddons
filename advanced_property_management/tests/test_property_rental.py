# -*- coding: utf-8 -*-

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPropertyRental(TransactionCase):

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
            "sale_rent": "for_tenancy",
            "rent_month": 1500.0,
        }
        vals.update(extra_vals)
        return self.env["property.property"].create(vals)

    def _create_rental(self, **extra_vals):
        property_id = extra_vals.pop("property_id", None) or self._create_property(
            sale_rent="for_tenancy",
            state="available",
        )
        vals = {
            "property_id": property_id.id,
            "renter_id": self.customer.id,
            "start_date": fields.Date.today(),
            "end_date": fields.Date.add(fields.Date.today(), months=2),
        }
        vals.update(extra_vals)
        return self.env["property.rental"].create(vals)

    def test_create_assigns_sequence(self):
        rental = self._create_rental()

        self.assertNotEqual(rental.name, "New")

    def test_compute_next_invoice(self):
        rental = self._create_rental(
            invoice_date=fields.Date.today(),
            end_date=fields.Date.add(fields.Date.today(), months=2),
        )

        self.assertEqual(
            rental.next_invoice,
            fields.Date.add(fields.Date.today(), months=1),
        )

    def test_action_cancel_releases_property(self):
        rental = self._create_rental()
        rental.property_id.state = "rented"

        rental.action_cancel()

        self.assertEqual(rental.state, "cancel")
        self.assertEqual(rental.property_id.state, "available")

    def test_action_create_contract_rejects_blacklisted_renter(self):
        rental = self._create_rental()
        rental.renter_id.action_add_blacklist()

        with self.assertRaises(ValidationError):
            rental.action_create_contract()

    def test_action_view_invoice(self):
        rental = self._create_rental()

        action = rental.action_view_invoice()

        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["domain"], [
            ("property_rental_id", "=", rental.id),
            ("move_type", "=", "out_invoice"),
        ])

    def test_action_check_rental_expires_records_without_next_invoice(self):
        rental = self._create_rental(state="in_contract", invoice_date=False)

        self.env["property.rental"].action_check_rental()

        self.assertEqual(rental.state, "expired")
