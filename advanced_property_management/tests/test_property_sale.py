# -*- coding: utf-8 -*-

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPropertySale(TransactionCase):

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
        cls.broker = cls.env["res.partner"].create({
            "name": "Property Test Broker",
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
            "unit_price": 300000.0,
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
        sale = self._create_sale()

        self.assertNotEqual(sale.name, "New")

    def test_compute_fixed_commission(self):
        plan = self.env["property.commission"].create({
            "name": "Fixed Commission",
            "commission_type": "fixed",
            "commission": 2500.0,
        })
        sale = self._create_sale(commission_plan_id=plan.id)

        self.assertEqual(sale.commission_type, "fixed")
        self.assertEqual(sale.commission, 2500.0)

    def test_compute_percentage_commission(self):
        plan = self.env["property.commission"].create({
            "name": "Percentage Commission",
            "commission_type": "percentage",
            "commission": 5.0,
        })
        sale = self._create_sale(commission_plan_id=plan.id)

        self.assertEqual(sale.commission_type, "percentage")
        self.assertEqual(sale.commission, 15000.0)

    def test_create_invoice_returns_default_invoice_action(self):
        sale = self._create_sale()

        action = sale.create_invoice()

        self.assertTrue(sale.invoiced)
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["context"]["default_move_type"], "out_invoice")
        self.assertEqual(action["context"]["default_property_order_id"], sale.id)

    def test_commission_bill_returns_default_bill_action(self):
        plan = self.env["property.commission"].create({
            "name": "Broker Commission",
            "commission_type": "fixed",
            "commission": 1000.0,
        })
        sale = self._create_sale(
            any_broker=True,
            broker_id=self.broker.id,
            commission_plan_id=plan.id,
        )

        action = sale.commission_bill()

        self.assertTrue(sale.billed)
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["context"]["default_move_type"], "in_invoice")
        self.assertEqual(action["context"]["default_partner_id"], self.broker.id)

    def test_action_view_invoice_and_commission_bill(self):
        sale = self._create_sale()

        invoice_action = sale.action_view_invoice()
        bill_action = sale.action_view_commission_bill()

        self.assertEqual(invoice_action["domain"], [
            ("property_order_id", "=", sale.id),
            ("move_type", "=", "out_invoice"),
        ])
        self.assertEqual(bill_action["domain"], [
            ("property_order_id", "=", sale.id),
            ("move_type", "=", "in_invoice"),
        ])

    def test_action_confirm_marks_property_sold(self):
        sale = self._create_sale()

        sale.action_confirm()

        self.assertEqual(sale.state, "confirm")
        self.assertEqual(sale.property_id.state, "sold")
        self.assertEqual(sale.property_id.sale_id, sale)

    def test_action_confirm_rejects_blacklisted_customer(self):
        sale = self._create_sale()
        sale.partner_id.action_add_blacklist()

        with self.assertRaises(ValidationError):
            sale.action_confirm()
