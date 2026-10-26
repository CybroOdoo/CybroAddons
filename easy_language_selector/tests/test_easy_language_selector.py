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
from unittest.mock import patch

from odoo.addons.easy_language_selector.controllers.easy_language_selector import (
    EasyLanguageSelector,
)
from odoo.tests import TransactionCase, tagged


class FakeRequest:

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestEasyLanguageSelector(TransactionCase):

    def _call_get_activated_languages(self, controller):
        endpoint = getattr(controller.get_activated_languages,
                           'original_endpoint', None)
        if endpoint:
            return endpoint(controller)
        return controller.get_activated_languages()

    def _call_change_active_languages(self, controller, **kwargs):
        endpoint = getattr(controller.change_active_languages,
                           'original_endpoint', None)
        if endpoint:
            return endpoint(controller, **kwargs)
        return controller.change_active_languages(**kwargs)

    def test_get_activated_languages_returns_names_and_codes(self):
        controller = EasyLanguageSelector()
        active_languages = self.env['res.lang'].sudo().search([])
        expected_languages = [{
            'name': language.name,
            'code': language.code,
        } for language in active_languages]

        with patch(
                'odoo.addons.easy_language_selector.controllers.'
                'easy_language_selector.request',
                FakeRequest(self.env),
        ):
            result = self._call_get_activated_languages(controller)

        self.assertEqual(result, expected_languages)
        self.assertIn('en_US', [language['code'] for language in result])

    def test_change_active_languages_updates_current_user_language(self):
        controller = EasyLanguageSelector()
        language = self.env['res.lang'].sudo().search([], limit=1)
        original_lang = self.env.user.lang

        try:
            with patch(
                    'odoo.addons.easy_language_selector.controllers.'
                    'easy_language_selector.request',
                    FakeRequest(self.env),
            ):
                result = self._call_change_active_languages(
                    controller,
                    code=language.code,
                )

            self.assertTrue(result)
            self.assertEqual(self.env.user.lang, language.code)
        finally:
            self.env.user.sudo().write({'lang': original_lang})
