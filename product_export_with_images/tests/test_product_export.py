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
import base64
from werkzeug.exceptions import Forbidden, NotFound

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import HttpCase, TransactionCase, tagged


SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@tagged("post_install", "-at_install")
class TestProductExportWizard(TransactionCase):
    """Test suite for product.export wizard logic and access permissions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export_group = cls.env.ref(
            "product_export_with_images.group_product_export_with_images"
        )

        cls.user_authorized = cls.env["res.users"].create({
            "name": "Export Authorized User",
            "login": "export_user_auth",
            "group_ids": [Command.set([cls.env.ref("base.group_user").id, cls.export_group.id])],
        })

        cls.user_unauthorized = cls.env["res.users"].create({
            "name": "Export Unauthorized User",
            "login": "export_user_unauth",
            "group_ids": [Command.set([cls.env.ref("base.group_user").id])],
        })

        cls.product_tmpl_1 = cls.env["product.template"].create({
            "name": "Test Template 1",
            "default_code": "TMP01",
            "list_price": 150.0,
            "standard_price": 90.0,
            "image_1920": SAMPLE_PNG_BASE64,
        })
        cls.product_tmpl_2 = cls.env["product.template"].create({
            "name": "Test Template 2",
            "default_code": "TMP02",
            "list_price": 200.0,
            "standard_price": 120.0,
        })

    def test_01_action_export_product_template(self):
        """Test wizard creation and URL action from product.template active_ids."""
        wizard_model = self.env["product.export"].with_user(self.user_authorized)
        context = {
            "active_model": "product.template",
            "active_ids": [self.product_tmpl_1.id, self.product_tmpl_2.id],
        }
        action = wizard_model.with_context(context).action_export_products()

        self.assertIsInstance(action, dict, "Expected an action dictionary")
        self.assertEqual(action.get("type"), "ir.actions.act_url")
        self.assertEqual(action.get("target"), "new")
        self.assertIn("/products_download/excel_report/", action.get("url", ""))

        # Verify wizard record created with selected templates
        wizard_id = int(action["url"].split("/")[-1])
        wizard = self.env["product.export"].browse(wizard_id)
        self.assertTrue(wizard.exists())
        self.assertEqual(set(wizard.product_tmp_ids.ids), {self.product_tmpl_1.id, self.product_tmpl_2.id})

    def test_02_action_export_product_variants(self):
        """Test wizard creation and URL action from product.product active_ids."""
        variant_1 = self.product_tmpl_1.product_variant_id
        variant_2 = self.product_tmpl_2.product_variant_id
        wizard_model = self.env["product.export"].with_user(self.user_authorized)
        context = {
            "active_model": "product.product",
            "active_ids": [variant_1.id, variant_2.id],
        }
        action = wizard_model.with_context(context).action_export_products()

        self.assertEqual(action.get("type"), "ir.actions.act_url")
        wizard_id = int(action["url"].split("/")[-1])
        wizard = self.env["product.export"].browse(wizard_id)
        self.assertTrue(wizard.exists())
        self.assertEqual(set(wizard.product_ids.ids), {variant_1.id, variant_2.id})

    def test_03_get_product_lines_prefers_high_res_image(self):
        """Verify get_product_lines extracts data and prioritizes image_1920."""
        wizard = self.env["product.export"].create({
            "product_tmp_ids": [(6, 0, [self.product_tmpl_1.id])],
        })
        lines = wizard.get_product_lines()
        self.assertEqual(len(lines), 1)

        line = lines[0]
        self.assertEqual(line["name"], "Test Template 1")
        self.assertEqual(line["internal_reference"], "TMP01")
        self.assertEqual(line["sales_price"], 150.0)
        self.assertEqual(line["cost"], 90.0)
        # Ensure image is present and matches the high-res 1920 image
        self.assertTrue(line["image"])
        raw_bytes = line["image"].content if hasattr(line["image"], "content") else base64.b64decode(line["image"])
        self.assertEqual(raw_bytes, base64.b64decode(SAMPLE_PNG_BASE64))

    def test_04_access_rights(self):
        """Verify unauthorized users cannot access product.export."""
        wizard_as_unauth = self.env["product.export"].with_user(self.user_unauthorized)
        with self.assertRaises(AccessError):
            wizard_as_unauth.create({"product_tmp_ids": [(6, 0, [self.product_tmpl_1.id])]})


@tagged("post_install", "-at_install")
class TestProductExportHttp(HttpCase):
    """Test suite for ExcelReportController HTTP route and security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.export_group = cls.env.ref(
            "product_export_with_images.group_product_export_with_images"
        )
        cls.user_owner = cls.env["res.users"].create({
            "name": "Owner Export User",
            "login": "owner_export_user",
            "password": "Password123!",
            "group_ids": [Command.set([cls.env.ref("base.group_user").id, cls.export_group.id])],
        })
        cls.user_other = cls.env["res.users"].create({
            "name": "Other Export User",
            "login": "other_export_user",
            "password": "Password123!",
            "group_ids": [Command.set([cls.env.ref("base.group_user").id, cls.export_group.id])],
        })
        cls.user_unauthorized = cls.env["res.users"].create({
            "name": "Unauthorized User",
            "login": "unauth_user",
            "password": "Password123!",
            "group_ids": [Command.set([cls.env.ref("base.group_user").id])],
        })

        cls.product_tmpl = cls.env["product.template"].create({
            "name": "Export Test Product",
            "list_price": 50.0,
            "standard_price": 25.0,
        })
        cls.wizard = cls.env["product.export"].with_user(cls.user_owner).create({
            "product_tmp_ids": [(6, 0, [cls.product_tmpl.id])],
        })

    def test_01_public_access_forbidden(self):
        """Unauthenticated requests must be redirected to login (not public download)."""
        url = f"/products_download/excel_report/{self.wizard.id}"
        response = self.url_open(url)
        # Odoo auth="user" redirects unauthenticated requests to web/login
        self.assertIn(
            response.status_code, [200, 302, 303],
            "Unauthenticated request should be redirected to login"
        )
        if response.status_code == 200:
            self.assertIn("login", response.url, "Must redirect to login page")

    def test_02_user_without_group_forbidden(self):
        """Authenticated users without export group receive 403 Forbidden."""
        self.authenticate(self.user_unauthorized.login, "Password123!")
        url = f"/products_download/excel_report/{self.wizard.id}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 403, "Users without group must get 403")

    def test_03_idor_protection_other_user_forbidden(self):
        """Another user cannot download an export created by user_owner (IDOR check)."""
        self.authenticate(self.user_other.login, "Password123!")
        url = f"/products_download/excel_report/{self.wizard.id}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 403, "Non-owner user must receive 403 Forbidden")

    def test_04_owner_download_success(self):
        """The creator with proper group successfully downloads XLSX report."""
        self.authenticate(self.user_owner.login, "Password123!")
        url = f"/products_download/excel_report/{self.wizard.id}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200, "Owner should download successfully")
        self.assertEqual(
            response.headers.get("Content-Type"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "MIME type must be standard XLSX"
        )
        self.assertTrue(len(response.content) > 0, "Response content must not be empty")
