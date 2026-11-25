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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOraLanguage(TransactionCase):
    """Unit tests for multi-language configuration and voice mapping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lang_es = cls.env['ora.language'].search([('code', '=', 'es')], limit=1)
        if not cls.lang_es:
            cls.lang_es = cls.env['ora.language'].create({
                'name': 'Spanish',
                'code': 'es',
                'first_msg': '¡Hola! ¿Cómo puedo ayudarte hoy?',
                'voice': 'eleven_voice_es_1',
            })
        cls.provider_model = cls.env['provider.model'].search([], limit=1)
        if not cls.provider_model:
            cls.provider_model = cls.env['provider.model'].create({
                'name': 'Default OpenAI Model',
                'key': 'gpt-4o-mini',
                'provider': 'openai',
            })
        cls.transcriber_model = cls.env['transcriber.model'].search([], limit=1)
        if not cls.transcriber_model:
            cls.transcriber_model = cls.env['transcriber.model'].create({
                'name': 'Default Deepgram Transcriber',
                'key': 'nova-2',
                'provider': 'deepgram',
            })

    def test_01_language_fields(self):
        """Verify language model values."""
        self.assertEqual(self.lang_es.code, 'es')
        self.assertTrue(self.lang_es.voice)
        self.assertTrue(self.lang_es.first_msg)

    def test_02_translate_text_empty(self):
        """Test translating empty string returns empty string immediately."""
        self.assertEqual(self.lang_es._translate_text("", "es"), "")

    @patch('odoo.addons.ora_ai_base.models.ora_language.Translator')
    def test_03_translate_text_with_mock_translator(self, mock_trans_cls):
        """Test translating text with mocked Translator instance."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.text = "¡Hola Mundo!"
        mock_instance.translate.return_value = mock_result
        mock_trans_cls.return_value = mock_instance

        res = self.lang_es._translate_text("Hello World!", "es")
        self.assertEqual(res, "¡Hola Mundo!")

        # Coroutine branch
        async def dummy_coro():
            coro_res = MagicMock()
            coro_res.text = "¡Async Hola!"
            return coro_res

        mock_instance.translate.return_value = dummy_coro()
        res_coro = self.lang_es._translate_text("Hello", "es")
        self.assertEqual(res_coro, "¡Async Hola!")

    @patch('odoo.addons.ora_ai_base.models.ora_language.OraLanguage._translate_text', return_value="Pedido completado")
    def test_04_get_language(self, mock_trans):
        """Test retrieving language profile and greetings."""
        res = self.env['ora.language'].get_language('es')
        self.assertTrue(res.get('status'))
        self.assertEqual(res.get('first_msg'), self.lang_es.first_msg)
        self.assertEqual(res.get('voice'), self.lang_es.voice)

    def test_05_get_language_invalid(self):
        """Test retrieving non-existent language returns false status."""
        res = self.env['ora.language'].get_language(False)
        self.assertFalse(res.get('status'))

    @patch('odoo.addons.ora_ai_base.models.ora_language.OraLanguage._translate_text', return_value="Orden confirmada")
    def test_06_get_language_with_target_string_replacement(self, mock_trans):
        """Test target string replacement in assistant prompt during language retrieval."""
        asst = self.env['ora.ai'].create({
            'name': 'Target Prompt Asst',
            'is_lang_switch': True,
            'provider': self.provider_model.provider or 'openai',
            'provider_model_id': self.provider_model.id,
            'transcriber_provider': self.transcriber_model.provider or 'deepgram',
            'transcriber_model_id': self.transcriber_model.id,
        })
        asst.prompt = "The sales order for customer [Customer Name] has been successfully created. Goodbye!"
        res = self.env['ora.language'].get_language('es')
        self.assertTrue(res.get('status'))
        self.assertIn("Orden confirmada", res.get('assistant_prompt'))
        asst.unlink()
