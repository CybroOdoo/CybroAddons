from unittest.mock import patch

from odoo import Command
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.password_reset_manager.controllers import web as web_controller


class FakeRequest:
    def __init__(self, env):
        self.env = env
        self.render_calls = []
        self.redirect_calls = []

    def render(self, template, values=None):
        self.render_calls.append((template, values))
        return {"template": template, "values": values}

    def redirect(self, url):
        self.redirect_calls.append(url)
        return {"redirect": url}


@tagged("post_install", "-at_install")
class TestWebController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = web_controller.DatabaseInherit()
        cls.group_user = cls.env.ref("base.group_user")
        cls.test_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Master Reset User",
            "login": "master.reset.user",
            "password": "master_initial_password",
            "email": "master.reset.user@example.com",
            "group_ids": [Command.set([cls.group_user.id])],
        })

    def test_change_password_by_master_updates_password_and_redirects(self):
        fake_request = FakeRequest(self.env)

        with patch.object(web_controller, "request", fake_request):
            with patch.object(
                web_controller.odoo.tools.config,
                "verify_admin_password",
                return_value=True,
            ):
                with patch.object(web_controller, "_", lambda message: message):
                    result = type(self.controller).change_password_by_master.__wrapped__(
                        self.controller,
                        user_name=self.test_user.login,
                        master_password="admin_pass",
                        new_password="master_new_password",
                        confirm_new_password="master_new_password",
                    )

        self.assertEqual(result["redirect"], "/web/login?message=Password Changed")
        self.test_user.invalidate_recordset(["password"])
        auth_info = self.test_user.with_user(self.test_user).sudo()._check_credentials(
            {
                "login": self.test_user.login,
                "password": "master_new_password",
                "type": "password",
            },
            {"interactive": True},
        )
        self.assertEqual(auth_info["uid"], self.test_user.id)

    def test_change_password_by_master_rejects_unknown_user(self):
        fake_request = FakeRequest(self.env)

        with patch.object(web_controller, "request", fake_request):
            with patch.object(
                web_controller.odoo.tools.config,
                "verify_admin_password",
                return_value=True,
            ):
                with patch.object(web_controller, "_", lambda message: message):
                    result = type(self.controller).change_password_by_master.__wrapped__(
                        self.controller,
                        user_name="missing.user",
                        master_password="admin_pass",
                        new_password="master_new_password",
                        confirm_new_password="master_new_password",
                    )

        self.assertEqual(result["template"], "password_reset_manager.forgot_password")
        self.assertEqual(result["values"]["error"], "User Name Is Not Valid")

    def test_change_password_by_master_rejects_invalid_master_password(self):
        fake_request = FakeRequest(self.env)

        with patch.object(web_controller, "request", fake_request):
            with patch.object(
                web_controller.odoo.tools.config,
                "verify_admin_password",
                return_value=False,
            ):
                with patch.object(web_controller, "_", lambda message: message):
                    result = type(self.controller).change_password_by_master.__wrapped__(
                        self.controller,
                        user_name=self.test_user.login,
                        master_password="wrong_admin_pass",
                        new_password="master_new_password",
                        confirm_new_password="master_new_password",
                    )

        self.assertEqual(result["template"], "password_reset_manager.forgot_password")
        self.assertEqual(result["values"]["error"], "Master Password Is Incorrect")

    def test_change_password_by_master_rejects_password_mismatch(self):
        fake_request = FakeRequest(self.env)

        with patch.object(web_controller, "request", fake_request):
            with patch.object(web_controller, "_", lambda message: message):
                result = type(self.controller).change_password_by_master.__wrapped__(
                    self.controller,
                    user_name=self.test_user.login,
                    master_password="admin_pass",
                    new_password="first_password",
                    confirm_new_password="second_password",
                )

        self.assertEqual(result["template"], "password_reset_manager.forgot_password")
        self.assertEqual(result["values"]["error"], "Password Not Matched")
