# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged("post_install", "-at_install")
class TestRecNameManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_model = cls.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )

        cls.partner_name_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "res.partner"),
                ("name", "=", "name"),
            ],
            limit=1,
        )

        cls.company_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "res.partner"),
                ("name", "=", "company_type"),
            ],
            limit=1,
        )

    def test_config_creation(self):
        config = self.env["rec.name.config"].create({
            "model_id": self.partner_model.id,
            "field_id": self.partner_name_field.id,
        })

        self.assertTrue(config)
        self.assertEqual(
            config.model_name,
            "res.partner"
        )
        self.assertEqual(
            config.field_name,
            "name"
        )

    def test_compute_field_ttype(self):
        config = self.env["rec.name.config"].create({
            "model_id": self.partner_model.id,
            "field_id": self.partner_name_field.id,
        })

        self.assertEqual(
            config.field_ttype,
            self.partner_name_field.ttype
        )

    def test_onchange_model_id(self):
        config = self.env["rec.name.config"].new({
            "model_id": self.partner_model.id,
        })

        result = config._onchange_model_id()

        self.assertFalse(config.field_id)
        self.assertIn("domain", result)
        self.assertIn("field_id", result["domain"])

    def test_unique_model_constraint(self):
        self.env["rec.name.config"].create({
            "model_id": self.partner_model.id,
            "field_id": self.partner_name_field.id,
        })

        with self.assertRaises(Exception):
            self.env["rec.name.config"].create({
                "model_id": self.partner_model.id,
                "field_id": self.company_field.id,
            })

    def test_field_belongs_to_model_constraint(self):
        product_model = self.env["ir.model"].search(
            [("model", "=", "product.template")],
            limit=1,
        )

        product_field = self.env["ir.model.fields"].search(
            [
                ("model", "=", "product.template"),
                ("name", "=", "name"),
            ],
            limit=1,
        )

        with self.assertRaises(ValidationError):
            self.env["rec.name.config"].create({
                "model_id": self.partner_model.id,
                "field_id": product_field.id,
            })

    def test_write_configuration(self):
        config = self.env["rec.name.config"].create({
            "model_id": self.partner_model.id,
            "field_id": self.partner_name_field.id,
        })

        config.write({
            "active": False,
        })

        self.assertFalse(config.active)

    def test_unlink_configuration(self):
        config = self.env["rec.name.config"].create({
            "model_id": self.partner_model.id,
            "field_id": self.partner_name_field.id,
        })

        config.unlink()

        self.assertFalse(config.exists())
