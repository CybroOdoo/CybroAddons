# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    def setUp(self):
        super().setUp()
        self.params = self.env["ir.config_parameter"].sudo()
        self.social_fields = [
            "instagram",
            "whatsapp",
            "github",
            "youtube",
            "google_plus",
            "snapchat",
            "flickr",
            "quora",
            "pinterest",
            "dribbble",
            "tumblr",
        ]

    def test_get_social_media_values_returns_configured_links(self):
        values_by_platform = {
            "instagram": "https://instagram.example/test",
            "whatsapp": "919876543210",
            "github": "https://github.example/test",
            "youtube": "https://youtube.example/test",
            "google_plus": "https://plus.example/test",
            "snapchat": "https://snapchat.example/test",
            "flickr": "https://flickr.example/test",
            "quora": "https://quora.example/test",
            "pinterest": "https://pinterest.example/test",
            "dribbble": "https://dribbble.example/test",
            "tumblr": "https://tumblr.example/test",
        }
        for platform, value in values_by_platform.items():
            self.params.set_param(
                f"website_extra_social_media.{platform}_link", value
            )

        settings = self.env["res.config.settings"].create({})

        self.assertEqual(settings.get_social_media_values(), values_by_platform)

    def test_get_social_media_values_includes_all_platforms_when_unset(self):
        for platform in self.social_fields:
            self.params.set_param(f"website_extra_social_media.{platform}_link", False)

        values = self.env["res.config.settings"].create({}).get_social_media_values()

        self.assertEqual(set(values), set(self.social_fields))
        self.assertTrue(all(value is False for value in values.values()))

    def test_social_media_fields_use_config_parameters(self):
        settings_model = self.env["res.config.settings"]

        for platform in self.social_fields:
            field = settings_model._fields[f"{platform}_link"]
            self.assertEqual(
                field.config_parameter,
                f"website_extra_social_media.{platform}_link",
            )
