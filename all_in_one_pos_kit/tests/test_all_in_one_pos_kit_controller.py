# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.all_in_one_pos_kit.controllers import (
    all_in_one_pos_kit as controller_module,
)


class TestPosScreenController(TransactionCase):

    def test_login_redirect_returns_super_url_without_pos_config(self):
        controller = controller_module.PosScreen()
        user = self.env["res.users"].create({
            "name": "No POS User",
            "login": "no_pos_user",
        })

        with patch.object(controller_module, "request",
                          SimpleNamespace(env=self.env)), \
                patch.object(controller_module.Home, "_login_redirect",
                             return_value="/web"):
            result = controller._login_redirect(user.id)

        self.assertEqual(result, "/web")

    def test_pos_qrcode_returns_png_response(self):
        controller = controller_module.PosScreen()
        captured = {}

        def _make_response(body, headers=None):
            captured["body"] = body
            captured["headers"] = headers
            return captured

        with patch.object(controller_module, "request",
                          SimpleNamespace(make_response=_make_response)):
            result = controller.pos_qrcode.__wrapped__(controller, "POS-QR")

        self.assertEqual(result["body"][:8], b"\x89PNG\r\n\x1a\n")
        self.assertIn(("Content-Type", "image/png"), result["headers"])

    def test_pos_qrcode_without_value_returns_not_found(self):
        controller = controller_module.PosScreen()

        with patch.object(controller_module, "request",
                          SimpleNamespace(not_found=lambda: "not-found")):
            self.assertEqual(
                controller.pos_qrcode.__wrapped__(controller, ""),
                "not-found",
            )
