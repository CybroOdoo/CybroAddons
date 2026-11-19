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
import json
from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.ora_ai_base.models.ora_ai import OraAi
from odoo.addons.ora_ai_base.models.ora_language import OraLanguage

# Assistants are synced with Vapi when they are written
VAPI_REQUEST = 'odoo.addons.ora_ai_base.models.ora_ai.requests.request'


# Plain functions: the ORM takes mock attributes of models for hooks
def fake_translate(_record, text, lang):
    return f'[{lang}] {text}' if text else ''


def failed_translate(_record, _text, _lang):
    error = 'offline'
    raise RuntimeError(error)


class OraAiWebsiteCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        vapi = cls.startClassPatcher(patch(VAPI_REQUEST))
        vapi.return_value.status_code = 200
        for model in (OraAi, OraLanguage):
            cls.startClassPatcher(patch.object(
                model, '_translate_text', fake_translate))
        cls.params = cls.env['ir.config_parameter'].sudo()
        cls.params.set_str('ora_ai_base.vapi_private_api_key', 'private-key')
        cls.params.set_str('ora_ai_base.vapi_public_api_key', 'public-key')
        cls.params.set_str(
            'ora_ai_base.vapi_webhook_base_url',
            'https://test-voice.example.com',
        )
        cls.startClassPatcher(
            patch.object(
                OraAi,
                '_get_vapi_base_url',
                return_value='https://test-voice.example.com',
            )
        )
        provider_model = (
            cls.env.ref(
                'ora_ai_base.model_openai_gpt_4o', raise_if_not_found=False
            )
            or cls.env['provider.model'].search(
                [('provider', '=', 'openai')], limit=1
            )
        )
        transcriber_model = (
            cls.env.ref(
                'ora_ai_base.transcriber_deepgram_nova_2',
                raise_if_not_found=False,
            )
            or cls.env['transcriber.model'].search(
                [('provider', '=', 'deepgram')], limit=1
            )
        )
        lang_en = cls.env.ref('ora_ai_base.lang_en', raise_if_not_found=False)
        lang_fr = cls.env.ref('ora_ai_base.lang_fr', raise_if_not_found=False)
        cls.assistant = cls.env['ora.ai'].create({
            'name': 'Burger Bot',
            'provider': 'openai',
            'provider_model_id': provider_model.id,
            'transcriber_provider': 'deepgram',
            'transcriber_model_id': transcriber_model.id,
            'end_call_phrases': 'goodbye',
            'is_lang_switch': True,
            'language_ids': [(6, 0, [lang.id for lang in (lang_en, lang_fr) if lang])],
            'state': 'done',
            'id_assistant': 'asst-1',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Ora Burger',
            'list_price': 12.5,
            'is_published': True,
            'sale_ok': True,
        })
        cls._enable_assistant(cls.assistant)

    @classmethod
    def _enable_assistant(cls, assistant):
        cls.env['res.config.settings'].create({
            'is_website_assistant': bool(assistant),
            'website_assistant_id': assistant.id,
        }).execute()


@tagged('post_install', '-at_install')
class TestOraAiWebsite(OraAiWebsiteCommon):

    def test_settings_saved(self):
        self.assertTrue(self.params.get_bool(
            'ora_ai_website.is_website_assistant'))
        self.assertEqual(self.params.get_int(
            'ora_ai_website.website_assistant_id'), self.assistant.id)
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.website_assistant_id, self.assistant)

    def test_website_assistant(self):
        self.assertEqual(self.env['ora.ai']._get_website_assistant(),
                         self.assistant)

    def test_website_assistant_disabled(self):
        self._enable_assistant(self.env['ora.ai'])
        self.assertFalse(self.env['ora.ai']._get_website_assistant())

    def test_website_assistant_not_on_vapi(self):
        self.assistant.state = 'draft'
        self.assertFalse(self.env['ora.ai']._get_website_assistant())
        self.assistant.unlink()
        self.assertFalse(self.env['ora.ai']._get_website_assistant())

    def test_language_overrides(self):
        voice = self.env.ref('ora_ai_base.lang_fr').voice
        self.assertEqual(self.assistant._get_language_overrides('fr'), {
            'transcriber': {'provider': 'deepgram', 'model': 'nova-2',
                            'language': 'fr'},
            'voice': {'provider': '11labs', 'voiceId': voice},
            'firstMessage': self.env.ref('ora_ai_base.lang_fr').first_msg,
            'endCallPhrases': ['[fr] goodbye'],
        })

    def test_language_overrides_without_end_call_phrases(self):
        self.assistant.with_context(skip_vapi_sync=True).write(
            {'end_call_phrases': False}
        )
        overrides = self.assistant._get_language_overrides('fr')
        self.assertNotIn('endCallPhrases', overrides)
        self.assistant.with_context(skip_vapi_sync=True).write(
            {'end_call_phrases': 'goodbye'}
        )

    def test_language_overrides_unknown_language(self):
        # Not a language of the assistant
        self.assertEqual(self.assistant._get_language_overrides('hi'), {})
        self.assistant.with_context(skip_vapi_sync=True).write(
            {'is_lang_switch': False}
        )
        self.assertEqual(self.assistant._get_language_overrides('fr'), {})
        self.assistant.with_context(skip_vapi_sync=True).write(
            {'is_lang_switch': True}
        )

    def test_language_overrides_translation_failure(self):
        with patch.object(OraLanguage, '_translate_text', failed_translate), \
                self.assertLogs('odoo.addons.ora_ai_website', 'WARNING'):
            overrides = self.assistant._get_language_overrides('fr')
        self.assertEqual(overrides['endCallPhrases'], ['goodbye'])


@tagged('post_install', '-at_install')
class TestOraAiWebsiteRoutes(HttpCase, OraAiWebsiteCommon):

    def _rpc(self, route, **params):
        response = self.url_open(route, data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call', 'params': params,
        }), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        return response.json()['result']

    def test_assistant_data(self):
        data = self._rpc('/ora_ai_website/assistant')
        self.assertEqual(data['public_api_key'], 'public-key')
        self.assertEqual(data['assistant'], 'asst-1')
        self.assertIn('Ora Burger', data['product_names'])
        self.assertNotIn('private-key', json.dumps(data),
                         'The private key must stay on the server')

    def test_assistant_data_disabled(self):
        self._enable_assistant(self.env['ora.ai'])
        self.assertEqual(self._rpc('/ora_ai_website/assistant'), {})
        self.assertEqual(self._rpc('/ora_ai_website/language', code='fr'), {})

    def test_language_route(self):
        overrides = self._rpc('/ora_ai_website/language', code='fr')
        self.assertEqual(overrides['transcriber']['language'], 'fr')

    def test_products_route(self):
        unpublished = self.env['product.product'].create({
            'name': 'Hidden Burger', 'is_published': False})
        result = self._rpc('/ora_ai_website/products', product_ids=[
            self.product.id, str(self.product.id), unpublished.id,
            999999999, 'made up'])
        self.assertEqual(result, {
            str(self.product.id): self.product.product_tmpl_id.id})

    def test_shop_button(self):
        response = self.url_open('/shop')
        self.assertIn('o_ora_website_assistant', response.text)
        self._enable_assistant(self.env['ora.ai'])
        response = self.url_open('/shop')
        self.assertNotIn('o_ora_website_assistant', response.text)

    def test_voice_order_tour(self):
        # Searched, so that the product is on the page with demo data too
        self.start_tour(f'/shop?search=Ora+Burger#product={self.product.id}',
                        'ora_ai_website_voice_order')
