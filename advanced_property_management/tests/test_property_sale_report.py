# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPropertySaleReport(TransactionCase):

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

    def test_action_create_report_returns_report_action_with_filtered_data(self):
        sale = self._create_sale()
        report = self.env.ref(
            "advanced_property_management.property_sale_report_action_report"
        )
        captured = {}

        def _fake_report_action(report_self, docids, data=None, config=True):
            captured["data"] = data
            return {"type": "ir.actions.report", "data": data}

        wizard = self.env["property.sale.report"].create({
            "from_date": fields.Date.today(),
            "to_date": fields.Date.today(),
            "partner_id": self.customer.id,
            "property_id": sale.property_id.id,
        })

        with patch.object(type(report), "report_action", _fake_report_action):
            action = wizard.action_create_report()

        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(captured["data"]["partner_name"], self.customer.name)
        self.assertEqual(captured["data"]["property_name"], sale.property_id.name)
        self.assertEqual(captured["data"]["datas"][0]["customer"], self.customer.name)
        self.assertEqual(captured["data"]["datas"][0]["name"], sale.property_id.name)
