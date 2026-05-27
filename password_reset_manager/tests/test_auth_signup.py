from unittest.mock import patch

import odoo
from odoo import Command
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.password_reset_manager.controllers import auth_signup as auth_signup_controller


class FakeSession:
    def __init__(self, auth_result=None, auth_exception=None):
        self.auth_result = auth_result or {}
        self.auth_exception = auth_exception
        self.authenticate_calls = []
        self.logout_calls = []

    def authenticate(self, env, credential):
        self.authenticate_calls.append((env, credential))
        if self.auth_exception:
            raise self.auth_exception
        return self.auth_result

    def logout(self, keep_db=False):
        self.logout_calls.append(keep_db)


class FakeEnv:
    def __init__(self, env, user=None):
        self._env = env
        self.user = user or env.user

    def __getitem__(self, model):
        return self._env[model]


class FakeRequest:
    def __init__(self, env, session, user=None):
        self.env = FakeEnv(env, user=user)
        self.session = session
        self.render_calls = []
        self.redirect_calls = []

    def render(self, template, values=None):
        self.render_calls.append((template, values))
        return {"template": template, "values": values}

    def redirect(self, url):
        self.redirect_calls.append(url)
        return {"redirect": url}


@tagged("post_install", "-at_install")
class TestAuthSignupController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = auth_signup_controller.AuthSignupHomeInherit()
        cls.group_user = cls.env.ref("base.group_user")
        cls.public_user = cls.env.ref("base.public_user")
        cls.test_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Password Reset User",
            "login": "password.reset.user",
            "password": "initial_password",
            "email": "password.reset.user@example.com",
            "group_ids": [Command.set([cls.group_user.id])],
        })

    def test_forgot_password_renders_template(self):
        fake_request = FakeRequest(self.env, FakeSession())

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(
                self.controller,
                "get_auth_signup_qcontext",
                return_value={"token": "abc"},
            ):
                result = type(self.controller).forgot_password.__wrapped__(self.controller)

        self.assertEqual(result["template"], "password_reset_manager.forgot_password")
        self.assertEqual(result["values"], {"token": "abc"})

    def test_web_auth_reset_password_direct_renders_template(self):
        fake_request = FakeRequest(self.env, FakeSession())

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(
                self.controller,
                "get_auth_signup_qcontext",
                return_value={"login": self.test_user.login},
            ):
                result = type(self.controller).web_auth_reset_password_direct.__wrapped__(self.controller)

        self.assertEqual(result["template"], "password_reset_manager.reset_password_direct")
        self.assertEqual(result["values"], {"login": self.test_user.login})

    def test_change_password_updates_password_and_redirects(self):
        fake_session = FakeSession(auth_result={"uid": self.test_user.id})
        fake_request = FakeRequest(self.env, fake_session)

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(auth_signup_controller, "_", lambda message: message):
                result = type(self.controller).change_password.__wrapped__(
                    self.controller,
                    user_name=self.test_user.login,
                    old_password="initial_password",
                    new_password="new_secure_password",
                    confirm_new_password="new_secure_password",
                )

        self.assertEqual(result["redirect"], "/web/login?message=Password Changed")
        self.assertEqual(fake_session.logout_calls, [True])
        self.assertEqual(
            fake_session.authenticate_calls[0][1],
            {
                "login": self.test_user.login,
                "password": "initial_password",
                "type": "password",
            },
        )
        self.test_user.invalidate_recordset(["password"])
        auth_info = self.test_user.with_user(self.test_user).sudo()._check_credentials(
            {
                "login": self.test_user.login,
                "password": "new_secure_password",
                "type": "password",
            },
            {"interactive": True},
        )
        self.assertEqual(auth_info["uid"], self.test_user.id)

    def test_change_password_rejects_public_user(self):
        fake_session = FakeSession(auth_result={"uid": self.test_user.id})
        fake_request = FakeRequest(self.env, fake_session, user=self.public_user)

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(auth_signup_controller, "_", lambda message: message):
                result = type(self.controller).change_password.__wrapped__(
                    self.controller,
                    user_name=self.test_user.login,
                    old_password="initial_password",
                    new_password="public_password",
                    confirm_new_password="public_password",
                )

        self.assertEqual(result["template"], "password_reset_manager.reset_password_direct")
        self.assertEqual(result["values"]["error"], "Public users can't change their password")
        self.assertEqual(fake_session.logout_calls, [])

    def test_change_password_handles_invalid_credentials(self):
        fake_session = FakeSession(auth_exception=odoo.exceptions.AccessDenied())
        fake_request = FakeRequest(self.env, fake_session)

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(auth_signup_controller, "_", lambda message: message):
                result = type(self.controller).change_password.__wrapped__(
                    self.controller,
                    user_name=self.test_user.login,
                    old_password="wrong_password",
                    new_password="next_password",
                    confirm_new_password="next_password",
                )

        self.assertEqual(result["template"], "password_reset_manager.reset_password_direct")
        self.assertEqual(result["values"]["error"], "Login or Password Is Incorrect")

    def test_change_password_rejects_password_mismatch(self):
        fake_request = FakeRequest(self.env, FakeSession())

        with patch.object(auth_signup_controller, "request", fake_request):
            with patch.object(auth_signup_controller, "_", lambda message: message):
                result = type(self.controller).change_password.__wrapped__(
                    self.controller,
                    user_name=self.test_user.login,
                    old_password="initial_password",
                    new_password="first_password",
                    confirm_new_password="second_password",
                )

        self.assertEqual(result["template"], "password_reset_manager.reset_password_direct")
        self.assertEqual(result["values"]["error"], "Password Not Match")
