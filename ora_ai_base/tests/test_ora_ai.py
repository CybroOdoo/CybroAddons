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
import base64
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, AccessError


@tagged('post_install', '-at_install')
class TestOraAi(TransactionCase):
    """Unit tests for Ora AI Voice Assistant model and workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.name = "Test Voice Corp"

        # Set up API keys and public base URL in config settings
        icp = cls.env['ir.config_parameter'].sudo()
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', 'test_private_key_12345')
            icp.set_str('ora_ai_base.vapi_public_api_key', 'test_public_key_67890')
            icp.set_str('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', 'test_private_key_12345')
            icp.set_param('ora_ai_base.vapi_public_api_key', 'test_public_key_67890')
            icp.set_param('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')

        # Retrieve or create test models
        cls.provider_model = cls.env['provider.model'].search([('provider', '=', 'openai')], limit=1)
        if not cls.provider_model:
            cls.provider_model = cls.env['provider.model'].create({
                'name': 'gpt-4o-mini',
                'provider': 'openai',
            })

        cls.transcriber_model = cls.env['transcriber.model'].search([('provider', '=', 'deepgram')], limit=1)
        if not cls.transcriber_model:
            cls.transcriber_model = cls.env['transcriber.model'].create({
                'name': 'nova-2',
                'provider': 'deepgram',
            })

        cls.language = cls.env['ora.language'].search([('code', '=', 'en')], limit=1)
        if not cls.language:
            cls.language = cls.env['ora.language'].create({
                'name': 'English',
                'code': 'en',
                'first_msg': 'Hello! How may I assist your business today?',
                'voice': 'eleven_voice_en_1',
            })

        # Create sample product and category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Voice Category'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Acoustic Headphones',
            'list_price': 150.0,
            'categ_id': cls.category.id,
        })

        # Create basic assistant record
        cls.assistant = cls.env['ora.ai'].create({
            'name': 'Test Voice Assistant',
            'provider': 'openai',
            'provider_model_id': cls.provider_model.id,
            'transcriber_provider': 'deepgram',
            'transcriber_model_id': cls.transcriber_model.id,
            'language_id': cls.language.id,
            'is_sale_order_creation': True,
            'is_customer_creation': True,
            'is_invoice_creation': True,
            'is_product_creation': True,
            'is_lang_switch': True,
        })

    def setUp(self):
        super().setUp()
        icp = self.env['ir.config_parameter'].sudo()
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', 'test_private_key_12345')
            icp.set_str('ora_ai_base.vapi_public_api_key', 'test_public_key_67890')
            icp.set_str('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', 'test_private_key_12345')
            icp.set_param('ora_ai_base.vapi_public_api_key', 'test_public_key_67890')
            icp.set_param('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')

    def test_01_assistant_initialization_and_defaults(self):
        """Test default values and computed tool descriptions."""
        self.assertEqual(self.assistant.name, 'Test Voice Assistant')
        self.assertEqual(self.assistant.provider, 'openai')
        self.assertEqual(self.assistant.transcriber_provider, 'deepgram')
        self.assertTrue(self.assistant.is_sale_order_creation)
        self.assertTrue(self.assistant.is_customer_creation)
        self.assertTrue(self.assistant.is_invoice_creation)
        self.assertTrue(self.assistant.is_product_creation)
        self.assertTrue(self.assistant.is_lang_switch)

    def test_02_get_assistant_tools(self):
        """Verify dynamic tool definitions generated for Vapi."""
        tools = self.assistant._get_assistant_tools("https://test.example.com", "?db=test", "secret")
        tool_names = [t.get('function', {}).get('name') for t in tools]

        self.assertIn('GetFinalOrderDetails', tool_names)
        self.assertIn('CheckCustomerExists', tool_names)
        self.assertIn('CreateCustomer', tool_names)
        self.assertIn('CreateInvoice', tool_names)
        self.assertIn('CreateProduct', tool_names)
        self.assertIn('SetUserLanguagePreference', tool_names)

        # Disable features and verify tools removed
        self.assistant.is_invoice_creation = False
        self.assistant.is_customer_creation = False
        self.assistant.is_product_creation = False
        tools_reduced = self.assistant._get_assistant_tools("https://test.example.com", "?db=test", "secret")
        reduced_names = [t.get('function', {}).get('name') for t in tools_reduced]
        self.assertNotIn('CreateInvoice', reduced_names)
        self.assertNotIn('CreateCustomer', reduced_names)
        self.assertNotIn('CreateProduct', reduced_names)

        self.assistant.is_invoice_creation = True
        self.assistant.is_customer_creation = True
        self.assistant.is_product_creation = True

    def test_03_prompt_generation(self):
        """Verify computed system prompt contains all expected instructions."""
        self.assistant._compute_prompt()
        prompt = self.assistant.prompt

        self.assertIn('Test Voice Corp', prompt)
        self.assertIn('Test Acoustic Headphones', prompt)
        self.assertIn('Customer', prompt)
        self.assertIn('Invoice', prompt)

    def test_04_vapi_base_url_and_transcriber_language(self):
        """Test URL retrieval and ISO language mapping."""
        base_url = self.assistant._get_vapi_base_url()
        self.assertTrue(base_url.startswith('https://'))

        lang_code = self.assistant._get_transcriber_language('en')
        self.assertEqual(lang_code, 'en')

        # Test ngrok tunnel auto-detection fallback on localhost
        icp = self.env['ir.config_parameter'].sudo()
        set_val = getattr(icp, 'set_str', getattr(icp, 'set_param', None))
        with patch('requests.get') as mock_ngrok:
            mock_ngrok_resp = MagicMock()
            mock_ngrok_resp.ok = True
            mock_ngrok_resp.json.return_value = {
                'tunnels': [{'public_url': 'https://abcd-1234.ngrok-free.app'}]
            }
            mock_ngrok.return_value = mock_ngrok_resp
            set_val('ora_ai_base.vapi_webhook_base_url', 'http://localhost:8069')
            url = self.assistant._get_vapi_base_url()
            self.assertEqual(url, 'https://abcd-1234.ngrok-free.app')

        # Test localhost UserError when ngrok is offline
        with patch('requests.get') as mock_ngrok_err:
            mock_ngrok_err.side_effect = Exception("No ngrok running")
            set_val('ora_ai_base.vapi_webhook_base_url', 'http://127.0.0.1:8069')
            with self.assertRaises(UserError):
                self.assistant._get_vapi_base_url()

        # Restore valid base url for subsequent tests
        set_val('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')

    @patch('requests.request')
    def test_05_action_create_assistant_success(self, mock_req):
        """Test successful Vapi assistant creation via API mock."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'vapi_asst_mock_9999',
            'name': 'Test Voice Assistant',
            'createdAt': '2026-11-09T10:00:00Z',
        }
        mock_req.return_value = mock_response

        self.assistant.action_create_assistant()
        self.assertEqual(self.assistant.id_assistant, 'vapi_asst_mock_9999')
        self.assertEqual(self.assistant.state, 'done')

    @patch('requests.request')
    def test_06_write_triggers_vapi_sync(self, mock_req):
        """Test updating assistant synchronizes changes with Vapi API."""
        self.assistant.id_assistant = 'vapi_asst_mock_9999'

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'vapi_asst_mock_9999',
            'name': 'Updated Assistant Name'
        }
        mock_req.return_value = mock_response

        self.assistant.write({'name': 'Updated Assistant Name'})
        self.assertEqual(self.assistant.name, 'Updated Assistant Name')
        self.assertTrue(mock_req.called)

    @patch('requests.request')
    def test_07_unlink_deletes_remote_assistant(self, mock_req):
        """Test deleting assistant record removes it from Vapi."""
        asst = self.env['ora.ai'].create({
            'name': 'Temporary Assistant to Delete',
            'id_assistant': 'vapi_delete_target_123',
            'provider': 'openai',
            'provider_model_id': self.provider_model.id,
            'transcriber_provider': 'deepgram',
            'transcriber_model_id': self.transcriber_model.id,
        })
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_req.return_value = mock_response

        asst.unlink()
        self.assertTrue(mock_req.called)

    def test_08_assistant_testing_action(self):
        """Test testing action validation and launch."""
        self.assistant.id_assistant = False
        with self.assertRaises(UserError):
            self.assistant.action_assistant_testing()

        self.assistant.id_assistant = 'vapi_asst_mock_9999'
        action = self.assistant.action_assistant_testing()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'action_voice_assistant')

    def test_09_get_available_assistants(self):
        """Test fetching configured assistants for the systray widget."""
        self.assistant.id_assistant = 'vapi_active_test_123'
        self.assistant.state = 'done'
        assistants = self.env['ora.ai'].get_available_assistants()
        self.assertIsInstance(assistants, list)
        asst_ids = [a['id'] for a in assistants]
        self.assertIn(self.assistant.id, asst_ids)

    def test_10_res_config_settings_vapi_keys(self):
        """Test configuration settings reader and open action."""
        settings = self.env['res.config.settings'].create({
            'vapi_private_api_key': 'key_private_abc',
            'vapi_public_api_key': 'key_public_xyz',
            'voice_order_auto_confirm': True,
        })
        # Execute settings while shielding against view validation errors from missing optional enterprise addons
        with patch.object(self.env['ir.ui.view'].__class__, '_check_xml', lambda s: True):
            settings.execute()

        icp = self.env['ir.config_parameter'].sudo()
        get_val = getattr(icp, 'get_str', getattr(icp, 'get_param', lambda k: ''))
        self.assertEqual(get_val('ora_ai_base.vapi_private_api_key'), 'key_private_abc')
        self.assertEqual(get_val('ora_ai_base.vapi_public_api_key'), 'key_public_xyz')

        open_action = settings.action_open_vapi()
        self.assertEqual(open_action.get('type'), 'ir.actions.act_url')
        self.assertIn('vapi.ai', open_action.get('url'))

    def test_11_provider_and_transcriber_model_restrictions(self):
        """Test that non-superuser cannot manually create or modify AI/Transcriber models."""
        test_user = self.env['res.users'].create({
            'name': 'Standard Demo User',
            'login': 'std_demo_user',
            'email': 'std_demo@example.com',
        })

        with self.assertRaises(UserError):
            self.env['provider.model'].with_user(test_user).create({
                'name': 'Unauthorized Model',
                'provider': 'openai'
            })

        with self.assertRaises(UserError):
            self.provider_model.with_user(test_user).write({'name': 'Tampered Name'})

        with self.assertRaises(UserError):
            self.env['transcriber.model'].with_user(test_user).create({
                'name': 'Unauthorized Transcriber',
                'provider': 'deepgram'
            })

        with self.assertRaises(UserError):
            self.transcriber_model.with_user(test_user).write({'name': 'Tampered Name'})

    def test_12_onchange_and_reset_assistant(self):
        """Test onchange helper handlers and reset assistant action."""
        self.assistant.provider = 'openai'
        self.assistant._onchange_provider()
        self.assertEqual(self.assistant.provider_model_id, self.provider_model)

        self.assistant.transcriber_provider = 'deepgram'
        self.assistant._onchange_transcriber_provider()
        self.assertEqual(self.assistant.transcriber_model_id, self.transcriber_model)

        # Test reset assistant
        temp_asst = self.env['ora.ai'].create({
            'name': 'Asst To Reset',
            'id_assistant': 'vapi_test_id_to_clear',
            'provider': 'openai',
            'provider_model_id': self.provider_model.id,
            'transcriber_provider': 'deepgram',
            'transcriber_model_id': self.transcriber_model.id,
        })
        self.env['ora.ai'].reset_assistant('vapi_test_id_to_clear')
        self.assertTrue(temp_asst.exists())

    def test_13_action_launch_voice_assistant(self):
        """Test action to launch assistant client action."""
        self.assistant.id_assistant = 'vapi_active_test_123'
        self.assistant.state = 'done'
        action = self.assistant.action_launch_voice_assistant()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'action_voice_assistant')

    def test_14_runtime_config_and_helpers(self):
        """Test runtime config tuple and translation fallbacks."""
        lang, voice, first_msg, end_msg = self.assistant._get_assistant_runtime_config()
        self.assertEqual(lang, 'en')
        self.assertTrue(voice)
        self.assertTrue(first_msg)

        # Empty translate test
        empty_tr = self.assistant._translate_text("", "es")
        self.assertEqual(empty_tr, "")

    def test_15_vapi_error_handling_and_translations(self):
        """Test _handle_vapi_error branching and prompt generation with attached files."""
        # Test error handling when response mentions transcriber
        resp_transcriber = MagicMock()
        resp_transcriber.json.return_value = {'message': 'transcriber deepgram model failed'}
        with self.assertRaises(UserError) as cm:
            self.assistant._handle_vapi_error(resp_transcriber, is_update=False)
        self.assertIn("Transcriber Model Unavailable", str(cm.exception))

        # Test error handling when response mentions model
        resp_model = MagicMock()
        resp_model.json.return_value = {'error': 'model gpt-4 is invalid'}
        with self.assertRaises(UserError) as cm:
            self.assistant._handle_vapi_error(resp_model, is_update=True)
        self.assertIn("AI Model Unavailable", str(cm.exception))

        # Test general error handling
        resp_gen = MagicMock()
        resp_gen.json.return_value = {'message': 'Generic authorization error'}
        with self.assertRaises(UserError) as cm:
            self.assistant._handle_vapi_error(resp_gen, is_update=False)
        self.assertIn("Generic authorization error", str(cm.exception))

        # Test attached file prompt generation
        with patch('requests.post') as mock_post:
            mock_post_resp = MagicMock()
            mock_post_resp.ok = True
            mock_post_resp.json.return_value = {'id': 'vapi_doc_99'}
            mock_post.return_value = mock_post_resp
            test_file = self.env['ora.file'].create({
                'name': 'Warranty Guide',
                'file': base64.b64encode(b"Dummy warranty content").decode('utf-8'),
                'filename': 'warranty.pdf',
            })
            self.assistant.file_ids = [(4, test_file.id)]
            self.assistant._compute_prompt()
            self.assertIn("KNOWLEDGE BASE & SCOPE INSTRUCTIONS", self.assistant.prompt)
            self.assertIn("Warranty Guide", self.assistant.prompt)

        # Test language switch first message
        self.assistant.is_lang_switch = True
        lang_ml = self.env['ora.language'].search([('code', '=', 'ml')], limit=1)
        lang_es = self.env['ora.language'].search([('code', '=', 'es')], limit=1)
        if lang_ml and lang_es:
            self.assistant.language_ids = [(6, 0, [lang_ml.id, lang_es.id])]
            self.assistant._compute_first_message()
            self.assertIn("Which language would you prefer?", self.assistant.first_message)

        # Test compute provider & transcriber models without selection and with selection
        self.assistant.provider = False
        self.assistant._compute_provider_models()
        self.assertTrue(len(self.assistant.provider_model_ids) > 0)
        self.assistant.provider = 'openai'
        self.assistant._compute_provider_models()
        self.assertTrue(len(self.assistant.provider_model_ids) > 0)

        self.assistant.transcriber_provider = False
        self.assistant._compute_transcriber_models()
        self.assertTrue(len(self.assistant.transcriber_model_ids) > 0)
        self.assistant.transcriber_provider = 'deepgram'
        self.assistant._compute_transcriber_models()
        self.assertTrue(len(self.assistant.transcriber_model_ids) > 0)

    def test_16_translate_text_branches(self):
        """Test translation fallbacks and handlers in _translate_text."""
        # Empty text and english pass through
        self.assertEqual(self.assistant._translate_text("", "es"), "")
        self.assertEqual(self.assistant._translate_text("Hello", "en"), "Hello")

        # Mock urllib success
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = b'[[["Hola", "Hello"]]]'
        with patch('urllib.request.urlopen', return_value=mock_resp):
            res = self.assistant._translate_text("Hello", "es")
            self.assertEqual(res, "Hola")

        # Mock urllib failure with fallback
        with patch('urllib.request.urlopen', side_effect=Exception("Net error")):
            with patch('odoo.addons.ora_ai_base.models.ora_ai.Translator') as mock_t_cls:
                mock_translator = MagicMock()
                mock_res = MagicMock()
                mock_res.text = "Hola Amigo"
                mock_translator.translate.return_value = mock_res
                mock_t_cls.return_value = mock_translator
                res = self.assistant._translate_text("Hello friend", "es")
                self.assertEqual(res, "Hola Amigo")

        # Mock total failure returns original text
        with patch('urllib.request.urlopen', side_effect=Exception("Net error")):
            with patch('odoo.addons.ora_ai_base.models.ora_ai.Translator', side_effect=Exception("Lib missing")):
                res = self.assistant._translate_text("Untranslated", "fr")
                self.assertEqual(res, "Untranslated")

    def test_17_language_description_and_onchanges(self):
        """Test dynamic language function descriptions and onchange model pickers."""
        # Onchange provider
        self.assistant.provider = 'groq'
        self.assistant.provider_model_id = False
        self.assistant._onchange_provider()
        if self.assistant.provider_model_id:
            self.assertEqual(self.assistant.provider_model_id.provider, 'groq')

        # Onchange transcriber provider
        self.assistant.transcriber_provider = 'talkscriber'
        self.assistant.transcriber_model_id = False
        self.assistant._onchange_transcriber_provider()
        if self.assistant.transcriber_model_id:
            self.assertEqual(self.assistant.transcriber_model_id.provider, 'talkscriber')

        # Language function description
        self.assistant.is_lang_switch = True
        self.assistant.language_ids = [(6, 0, [self.language.id])]
        self.assistant._compute_language_function_description()
        self.assertIn("English", self.assistant.language_function_description)
        self.assertIn("en", self.assistant.language_function_description)

        self.assistant.is_lang_switch = False
        self.assistant._compute_language_function_description()
        self.assertEqual(self.assistant.language_function_description, "")

    def test_18_capabilities_prohibited_prompt_branches(self):
        """Test prompt instructions when capabilities are prohibited."""
        self.assistant.write({
            'is_sale_order_creation': False,
            'is_customer_creation': False,
            'is_invoice_creation': False,
            'is_product_creation': False,
        })
        self.assistant._compute_prompt()
        prompt = self.assistant.prompt
        self.assertIn("Strictly prohibited: decline placing or confirming sale orders", prompt)
        self.assertIn("Strictly prohibited: customer creation is disabled", prompt)
        self.assertIn("Strictly prohibited: invoice creation is disabled", prompt)
        self.assertIn("Strictly prohibited: product creation is disabled", prompt)

        # Restore
        self.assistant.write({
            'is_sale_order_creation': True,
            'is_customer_creation': True,
            'is_invoice_creation': True,
            'is_product_creation': True,
        })

    def test_19_webhook_secret_generation_and_access_error(self):
        """Test auto-generation of webhook secret and protocol checks."""
        icp = self.env['ir.config_parameter'].sudo()
        set_val = getattr(icp, 'set_str', getattr(icp, 'set_param', None))
        set_val('ora_ai_base.vapi_webhook_secret', '')
        secret = self.assistant._get_or_create_webhook_secret()
        self.assertTrue(secret)
        self.assertGreaterEqual(len(secret), 32)

        # Non-https base url raises AccessError
        with patch.object(type(icp), 'get_str', return_value='ftp://non-https-url.com'):
            with self.assertRaises(AccessError):
                self.assistant._get_vapi_base_url()

    def test_20_runtime_config_and_malayalam(self):
        """Test runtime configuration computation for English and Malayalam."""
        self.assistant.is_lang_switch = True
        self.assistant.language_ids = [(6, 0, [self.language.id])]
        lang, voice, first_msg, end_msg = self.assistant._get_assistant_runtime_config()
        self.assertEqual(lang, "en")
        self.assertEqual(voice, "qgj3VahzWaAK300v6H27")

        # Test Malayalam
        lang_ml = self.env['ora.language'].search([('code', '=', 'ml')], limit=1)
        if lang_ml:
            self.assistant.is_lang_switch = False
            self.assistant.language_id = lang_ml
            self.assistant.first_message = False
            lang, voice, first_msg, end_msg = self.assistant._get_assistant_runtime_config()
            self.assertEqual(lang, "ml")
            self.assertIn("നമസ്കാരം", first_msg)

    def test_21_handle_vapi_error_branches(self):
        """Test error parsing and formatted UserError exceptions from Vapi responses."""
        mock_err_resp = MagicMock()
        mock_err_resp.json.side_effect = ValueError("Invalid JSON")
        mock_err_resp.text = "transcriber model unsupported"
        with self.assertRaises(UserError) as err:
            self.assistant._handle_vapi_error(mock_err_resp)
        self.assertIn("Transcriber Model", str(err.exception))

        # List-based error message
        mock_err_resp2 = MagicMock()
        mock_err_resp2.json.return_value = {'message': ['General model validation error', 'Line 2']}
        with self.assertRaises(UserError) as err2:
            self.assistant._handle_vapi_error(mock_err_resp2)
        self.assertIn("AI Model Unavailable", str(err2.exception))

    @patch('requests.request')
    def test_22_write_sync_404_and_assistant_testing_validations(self, mock_req):
        """Test 404 response on write resets state, and action_assistant_testing validations."""
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.ok = False
        mock_req.return_value = mock_404

        self.assistant.with_context(skip_vapi_sync=True).write({
            'id_assistant': 'vapi_asst_mock_9999',
            'state': 'done'
        })
        self.assistant.write({'name': 'Updated Assistant 404'})
        self.assertEqual(self.assistant.state, 'draft')
        self.assertFalse(self.assistant.id_assistant)

        # Validation errors on action_assistant_testing
        with self.assertRaises(UserError):
            self.assistant.action_assistant_testing()

        self.assistant.with_context(skip_vapi_sync=True).write({'id_assistant': 'valid_id'})
        icp = self.env['ir.config_parameter'].sudo()
        set_val = getattr(icp, 'set_str', getattr(icp, 'set_param', None))
        set_val('ora_ai_base.vapi_public_api_key', '')
        with self.assertRaises(UserError):
            self.assistant.action_assistant_testing()
        set_val('ora_ai_base.vapi_public_api_key', 'test_public_key_67890')

    def test_23_action_launch_and_systray_assistants(self):
        """Test global launcher and systray available assistants dropdown."""
        # Unset all done assistants
        done_assistants = self.env['ora.ai'].search([('state', '=', 'done')])
        done_assistants.write({'state': 'draft'})

        action = self.env['ora.ai'].action_launch_voice_assistant()
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action.get('params', {}).get('type'), 'warning')

        # Restore assistant and verify dropdown items
        self.assistant.state = 'done'
        self.assistant.id_assistant = 'vapi_test_id_done'
        assistants_list = self.env['ora.ai'].get_available_assistants()
        self.assertTrue(any(a['id'] == self.assistant.id for a in assistants_list))


