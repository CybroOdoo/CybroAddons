# -*- coding: utf-8 -*-
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.website_extra_social_media.controllers import (
    website_extra_social_media as controller_module,
)
from odoo.addons.website_extra_social_media.controllers.website_extra_social_media import (
    WebsiteExtraSocialMedia,
)


class TestWebsiteExtraSocialMediaController(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = WebsiteExtraSocialMedia()
        self.params = self.env["ir.config_parameter"].sudo()

    def _fake_request(self):
        return SimpleNamespace(
            env=self.env,
            redirect=lambda location, local=False: {
                "location": location,
                "local": local,
            },
        )

    def _redirect_social(self, platform):
        with patch.object(controller_module, "request", self._fake_request()):
            return self.controller.redirect_social.__wrapped__(
                self.controller, platform
            )

    def test_get_config_param_reads_parameter_value(self):
        self.params.set_param(
            "website_extra_social_media.instagram_link",
            "https://instagram.example/test",
        )

        with patch.object(controller_module, "request", self._fake_request()):
            value = self.controller._get_config_param(
                "website_extra_social_media.instagram_link"
            )

        self.assertEqual(value, "https://instagram.example/test")

    def test_redirect_social_redirects_to_configured_platform_url(self):
        self.params.set_param(
            "website_extra_social_media.github_link",
            "https://github.example/test",
        )

        response = self._redirect_social("github")

        self.assertEqual(response["location"], "https://github.example/test")
        self.assertFalse(response["local"])

    def test_redirect_social_builds_whatsapp_send_url(self):
        self.params.set_param("website_extra_social_media.whatsapp_link", "919876543210")

        response = self._redirect_social("whatsapp")

        self.assertEqual(
            response["location"],
            "https://api.whatsapp.com/send?phone=919876543210",
        )
        self.assertFalse(response["local"])

    def test_redirect_social_falls_back_for_unknown_platform(self):
        response = self._redirect_social("unknown")

        self.assertEqual(response["location"], "/")
        self.assertFalse(response["local"])

    def test_redirect_social_falls_back_when_platform_is_not_configured(self):
        self.params.set_param("website_extra_social_media.youtube_link", False)

        response = self._redirect_social("youtube")

        self.assertEqual(response["location"], "/")
        self.assertFalse(response["local"])
