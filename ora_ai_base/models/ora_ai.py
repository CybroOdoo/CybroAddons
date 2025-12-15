# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from googletrans import Translator
from odoo import api, fields, models
import requests
from odoo.exceptions import AccessError, ValidationError

PROVIDER = [
    ('openai', 'openai'),
    ('together-ai', 'Together-AI'),
    ('anyscale', 'AnyScale'),
    ('openrouter', 'OpenRouter'),
    ('perplexity-ai', 'Perplexity-AI'),
    ('deepinfra', 'DeepInfra'),
    ('groq', 'Groq'),
    ('anthropic', 'Anthropic')
]
TRANSCRIBER_PROVIDER = [('deepgram', 'Deepgram'),
                        ('talkscriber', 'Talkscriber'),
                        ('gladia', 'Gladiya')]
STATE = [('draft', 'Draft'),
         ('done', 'Done')]


class OraAi(models.Model):
    """Model for the order assistant."""
    _name = "ora.ai"
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = "Order Assistant"

    name = fields.Char(string="Name", required=True,
                       help="Name of the AI assistant configuration.")
    id_assistant = fields.Char(string="Assistant id", readonly=True,
                               copy=False, help="Unique identifier of the"
                                                "assistant created via "
                                                "external API.")
    first_message = fields.Text(string="First Message",
                                compute="_compute_first_message",
                                help="The first message that the assistant"
                                     " will say.", )
    provider = fields.Selection(string="Provider", selection=PROVIDER,
                                default="openai", required=True,
                                help="Select the LLM provider for generating"
                                     " responses (e.g., OpenAI, Anthropic, "
                                     "Groq).")
    provider_model_id = fields.Many2one('provider.model',
                                        string="Model",
                                        domain="[('id', 'in',provider_model_ids)]",
                                        required=True,
                                        help="Select the specific AI model"
                                             "offered by the chosen provider.")
    provider_model_ids = fields.Many2many('provider.model',
                                          compute='_compute_provider_models',
                                          help="Filtered list of models "
                                               "available based on the "
                                               "selected provider.")
    transcriber_provider = fields.Selection(selection=TRANSCRIBER_PROVIDER,
                                            string="Transcriber Provider",
                                            default='deepgram', required=True,
                                            help="Speech-to-text service "
                                                 "provider for transcribing "
                                                 "voice input.")
    transcriber_model_id = fields.Many2one('transcriber.model',
                                           string="Transcriber Model",
                                           required=True,
                                           domain="[('id', 'in', transcriber_model_ids)]",
                                           help="Choose the transcription "
                                                "model best suited for the "
                                                "conversation context.")
    transcriber_model_ids = fields.Many2many('transcriber.model',
                                             compute='_compute_transcriber_models',
                                             help="List of available "
                                                  "transcription models "
                                                  "filtered  by selected "
                                                  "provider.")
    language_id = fields.Many2one('ora.language',
                                  string="Language",
                                  help="Select the default language "
                                       "used by the assistant.")
    is_lang_switch = fields.Boolean(string="Multi-Language",
                                    help="Enable support for multiple "
                                         "languages. Assistant will switch"
                                         " languages if needed.")
    language_ids = fields.Many2many('ora.language',
                                    string="Languages",
                                    help="List of available languages for "
                                         "dynamic language switching during "
                                         "the  session.")
    state = fields.Selection(selection=STATE, tracking=True,
                             default="draft", copy=False,
                             help="Current status of the assistant"
                                  " configuration")
    date = fields.Date(string="Date",
                       help="Date when the assistant was created or"
                            " activated.")
    prompt = fields.Text(string="Contents",
                         compute="_compute_prompt",
                         readonly=True,
                         help="The Contents can be used to configure the"
                              " context, role, personality, instructions "
                              "and so on for the assistant.", )
    end_call_phrases = fields.Text(string="End Call Phrases",
                                   default="goodbye",
                                   help="Enter phrases, separated by commas, "
                                        "that will trigger the Assistant to "
                                        "end the call when spoken.")
    file_ids = fields.Many2many('ora.file',
                                string="Knowledge Base",
                                help="Knowledge Base is a collection of"
                                     " custom documents that contain "
                                     "information on specific topics or"
                                     " domains.")
    function_description = fields.Char(string="Function",
                                       compute="_compute_function_description",
                                       help="Generated JSON-based function")
    language_function_description = fields.Char(
        string="language function description",
        compute="_compute_language_function_description",
        help="Generated function spec for language preference "
             "handling used by the assistant.")

    def _translate_text(self, text, target_lang):
        """Translates the given text into the specified language using
        Googletrans."""
        translator = Translator()
        translated = translator.translate(text, dest=target_lang)
        return translated.text

    @api.depends('provider')
    def _compute_provider_models(self):
        """Populate the list of available provider models based on the
         selected provider."""
        for rec in self:
            provider_model = rec.provider_model_id.search([])
            for provider in PROVIDER:
                if rec.provider == provider[0]:
                    filtered_model = provider_model.filtered(
                        lambda l: l.provider == provider[0])
                    rec.provider_model_ids = [fields.Command.link(res.id)
                                              for res in filtered_model]
                if not rec.provider:
                    rec.provider_model_ids = [fields.Command.link(res.id)
                                              for res in provider_model]

    @api.depends('transcriber_provider')
    def _compute_transcriber_models(self):
        """Assign available transcriber models based on the selected
         transcriber provider"""
        for rec in self:
            provider_model = rec.transcriber_model_id.search([])
            for provider in TRANSCRIBER_PROVIDER:
                if rec.transcriber_provider == provider[0]:
                    filtered_model = provider_model.filtered(
                        lambda l: l.provider == provider[0])
                    rec.transcriber_model_ids = [fields.Command.link(res.id)
                                                 for res in filtered_model]
                if not rec.transcriber_provider:
                    rec.transcriber_model_ids = [fields.Command.link(res.id)
                                                 for res in provider_model]

    @api.depends('language_ids')
    def _compute_language_function_description(self):
        """Computes a formatted description of available languages
         for the assistant."""
        for rec in self:
            language_function_description = ""
            if rec.language_ids and rec.is_lang_switch:
                for lang in rec.language_ids:
                    language_function_description += (f"{lang.name} : "
                                                      f"{lang.code},  \n")
                rec.language_function_description = (
                    language_function_description)
            else:
                rec.language_function_description = ""

    def _compute_prompt(self):
        """Computes a detailed prompt for the voice assistant based on
         the current product catalog and availability."""
        prompt = (
            f"You are the voice assistant of the 'My Company (San Francisco)' "
            f"Restaurant, responsible for taking customer orders. "
            f"Your primary task is to carefully listen to and process the "
            f"customer's order details.\n"
            f"Must ask for Customer Name.\n"
            f"If a customer asks for product details, first explain all "
            f"the details by category. Then, mention the product name, "
            f"followed by its price, in that order.\n")
        out_of_stock_prompt = "."
        out_of_stock_prompt_2 = "."
        cate_ids = self.env['product.public.category'].search([])
        for rec in cate_ids:
            prompt += f"\n{rec.display_name}\n"
            products = self.env['product.template'].search(
                [('public_categ_ids', 'in', rec.id),
                 ('is_published', '=', True)])
            for record in products:
                prompt += f"  • {record.name}, ${record.list_price}\n"
                optional_products = record.optional_product_ids.mapped('name')
                variants = record.product_variant_ids
                if (record.type == 'product' and
                        not record.allow_out_of_stock_order):
                    prompt += (f" -quantity available:"
                               f"{int(record.qty_available)}\n")
                    out_of_stock_prompt = (", don't say the available quantity"
                                           " even if it is out of stock, say "
                                           "only when it asked.")
                    out_of_stock_prompt_2 = (" ,if the quantity is greater than"
                                             " available quantity just say the"
                                             " available quantity in the stock."
                                             " ")
                if len(variants) > 1:
                    prompt += f"    - {len(variants)} variants\n"
                    for variant in variants:
                        attribute_values = (
                            variant.product_template_variant_value_ids.mapped(
                                'name'))
                        variant_details = ", ".join(attribute_values)
                        prompt += (f"        * {variant_details}, "
                                   f"${variant.lst_price}\n")
                if len(optional_products) > 0:
                    prompt += (f"    - {len(optional_products)} "
                               f"Optional Products\n")
                    for opt_product in optional_products:
                        prompt += f"     • {opt_product} \n"
        none_categ_products = self.env['product.template'].search(
            [("public_categ_ids", "=", False), ('is_published', '=', True)])
        prompt += f"\n None category \n"
        for rec in none_categ_products:
            prompt += f"  • {rec.name}, ${rec.list_price} \n"
        prompt += (
            f"\n When a customer interacts with you through a voice command"
            f" to place an order, \n you should proceed by listing out all "
            f"product options available without excluding any mentioned"
            f" products {out_of_stock_prompt}\n"
            f"if the product has variants ask for which variant do you need.\n"
            f"After customer select a product the ask for How many Quantity"
            f" do you need{out_of_stock_prompt_2}\n"
            f"if the product has optional products ask do you want to add ? \n"
            f"Before confirming the order, ask Would you like to add anything"
            f" else to your order before confirming? \n"
            f"Once the customer finalizes their order and informs you of their"
            f" selection, ask, 'May I confirm the order?' If they respond "
            f"affirmatively, kindly repeat back the order details "
            f"for confirmation.\n Keep all your responses short and simple."
            f" Use casual language, phrases like Umm..., Well..., and I "
            f"mean are preferred.\n If customer order confirmed. say thankyou"
            f" for ordering and goodbye.\n This is a voice conversation, "
            f"so keep your responses short, like in a real conversation. "
            f"Don't ramble for too long")
        self.prompt = prompt

    def _compute_function_description(self):
        """Computes a descriptive mapping of product names,
         variants, and their IDs."""
        function_description = ""
        products = self.env['product.product'].search([])
        for product in products:
            variant_values = ", ".join(
                product.product_template_attribute_value_ids.mapped('name'))
            function_description += (f"{product.name} {variant_values} :"
                                     f" {product.id},  \n")
        self.function_description = function_description

    def _compute_first_message(self):
        """Computes the initial greeting message for the voice assistant."""
        for rec in self:
            languages = rec.language_ids.mapped('name')
            result = ', '.join(languages)
            if rec.language_ids and rec.is_lang_switch:
                rec.first_message = (f"Hey iam your {self.name}, Which "
                                     f"language would you like to choose?"
                                     f" We have several languages available"
                                     f" such as {result}. Which Language "
                                     f"would you prefer?")
            else:
                rec.first_message = (f"Hey iam {self.name}, How can i "
                                     f"help you today?")

    def action_create_assistant(self):
        """Creates a voice assistant instance using the Vapi.ai API based
         on the assistant configuration."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        protocol = "https" if base_url.startswith("https") else "http"
        if protocol == 'http':
            raise AccessError("URL Must be HTTPS")
        if protocol == 'https':
            url = "https://api.vapi.ai/assistant"
            if self.is_lang_switch and self.language_ids:
                language = "en"
                voice = "qgj3VahzWaAK300v6H27"
                first_message = self.first_message
            else:
                language = self.language_id.code
                voice = self.language_id.voice
                first_message = self._translate_text(self.first_message,
                                                     language)
            payload = {
                "transcriber": {
                    "provider": self.transcriber_provider,
                    "model": self.transcriber_model_id.key,
                    "language": language,
                    "smartFormat": True
                },
                "voice": {
                    "voiceId": voice,
                    "provider": "11labs",
                },
                "model": {
                    "provider": self.provider,
                    "model": self.provider_model_id.key,
                    "knowledgeBase": {
                        "provider": "canonical",
                        "fileIds": self.file_ids.mapped('id_file')
                    },
                    "messages": [
                        {
                            "role": "system",
                            "content": self.prompt
                        }
                    ],
                    "tools": [
                        {
                            "type": "function",
                            "async": True,
                            "function": {
                                "name": "GetFinalOrderDetails",
                                "description": f"This function is designed to"
                                               f"retrieve order details from "
                                               f"a voice assistant, with order"
                                               f" confirmation being a "
                                               f"prerequisite for providing "
                                               f"the details. The function "
                                               f"will be triggered after "
                                               f"confirming the order. "
                                               f"Upon asking a confirmation "
                                               f"question and receiving a "
                                               f"'yes' response, this function"
                                               f" must be activated.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "OrderDetails": {
                                            "type": "object",
                                            "properties": {
                                                "Products": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "Quantity": {
                                                                "type": "number",
                                                                'description': f"This parameter is used to retrieve the product quantity. {{ quantities: customer ordered quantity }}"
                                                            },
                                                            "Customer": {
                                                                "type": "string",
                                                                'description': f"This parameter is used to retrieve the customer name. {{ customer: customer name }}"
                                                            },
                                                            "Product": {
                                                                "type": "string",
                                                                'description': f"This parameter is used to retrieve the Product name. {{ product: product name }}",
                                                            },
                                                            "Variant": {
                                                                "type": "string",
                                                                "description": f"This parameter is used to retrieve the Product variant details. For example, if a customer order is confirmed, then retrieve {{ Variant: product Variant }}",
                                                            },
                                                            "productId": {
                                                                "type": "number",
                                                                "description": f'Determine the Product ID of the product in the confirmed order. Fetch the correct ID based on the following product and ID mapping: , {self.function_description}',
                                                            }
                                                        },
                                                        "required": [
                                                            "Quantity",
                                                            "Customer",
                                                            "Product",
                                                            "Variant",
                                                            "productId"]
                                                    }
                                                }
                                            },
                                            "required": ["products"]
                                        }
                                    },
                                    "required": ["OrderDetails"]
                                }
                            },
                            "server": {
                                "url": f"{base_url}/vapi_voice_assistant/details",
                            }
                        },
                        {
                            "type": "function",
                            "async": True,
                            "function": {
                                "name": "SetUserLanguagePreference",
                                "description": "This custom function retrieves the selected languages at the beginning of a voice assistance session if the user chooses the languages at the start of the session. This function must achieve the LanguageCode",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "LanguagePreference": {
                                            "type": "object",
                                            "properties": {
                                                "LanguageCode": {
                                                    "type": "string",
                                                    "description": f"The code of the language chosen by the user. For example: en-IN for English (India), en-US for English (United States), es-LA for Spanish (Latin America).,our  lanagues and its code  is {self.language_function_description}"
                                                },
                                            },
                                            "required": [
                                                "LanguageCode",
                                            ]
                                        }
                                    },
                                    "required": ["LanguagePreference"]
                                }
                            },
                            "server": {
                                "url": f"{base_url}/vapi_voice_assistant/language_details"
                            }
                        },
                    ],
                },
                "clientMessages": ["conversation-update", "function-call",
                                   "hang", "model-output", "speech-update",
                                   "status-update", "transcript", "tool-calls",
                                   "user-interrupted", "voice-input"],
                "serverMessages": ["conversation-update", "end-of-call-report",
                                   "function-call", "hang", "speech-update",
                                   "status-update", "tool-calls",
                                   "transfer-destination-request",
                                   "user-interrupted"],
                "messagePlan": {
                    "idleMessages": ["Feel free to ask whenever you're ready.",
                                     "I'm still here if you need assistance.",
                                     "How can I assist you further?",
                                     "Are you still there?",
                                     "Looking for something specific? I can "
                                     "assist with that!",
                                     "Need help choosing a product? I'm here "
                                     "to assist.",
                                     "I'm here if you need any assistance with"
                                     "your shopping."],
                    "idleTimeoutSeconds": 5,
                    "idleMessageMaxSpokenCount": 10},
                "name": self.name,
                "firstMessage": first_message,
                "serverUrl": f"{base_url}/vapi_voice_assistant/status",
                "endCallPhrases": [
                    self.end_call_phrases
                ],
            }
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json"
            }
            response = requests.request("POST", url, json=payload,
                                        headers=headers)
            json_response = response.json()
            self.write({'date': json_response.get('createdAt'),
                        'state': 'done',
                        'id_assistant': json_response.get('id')
                        })

    def write(self, vals):
        """Update the external Vapi.ai assistant configuration when
         the record is modified."""
        res = super().write(vals)
        if self.id_assistant:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            bearer = self.env['ir.config_parameter'].sudo().get_param(
                'ora_ai_base.vapi_private_api_key')
            url = f"https://api.vapi.ai/assistant/{self.id_assistant}"
            if self.is_lang_switch and self.language_ids:
                language = "en"
                voice = "qgj3VahzWaAK300v6H27"
                first_message = self.first_message
                end_message = self.end_call_phrases
            else:
                language = self.language_id.code
                voice = self.language_id.voice
                first_message = self._translate_text(self.first_message,
                                                     language)
                end_message = self._translate_text(self.end_call_phrases,
                                                   language)
            payload = {
                "transcriber": {
                    "provider": self.transcriber_provider,
                    "model": self.transcriber_model_id.key,
                    "language": language,
                    "smartFormat": True},
                "voice": {
                    "voiceId": voice,
                    "provider": "11labs"},
                "model": {
                    "provider": self.provider,
                    "model": self.provider_model_id.key,
                    "knowledgeBase": {
                        "provider": "canonical",
                        "fileIds": self.file_ids.mapped('id_file')},
                    "messages": [{
                        "role": "system",
                        "content": self.prompt}],
                    "tools": [{
                        "type": "function",
                        "async": True,
                        "function": {
                            "name": "GetFinalOrderDetails",
                            "description": f"This function is designed to"
                                           f" retrieve order details from"
                                           f" a voice assistant, with "
                                           f"order confirmation being a "
                                           f"prerequisite for providing "
                                           f"the details. The function "
                                           f"will be triggered after "
                                           f"confirming the order. Upon"
                                           f" asking a confirmation "
                                           f"question and receiving a "
                                           f"'yes' response, this function"
                                           f" must be activated.",
                            "parameters": {"type": "object", "properties": {
                                "OrderDetails":
                                    {"type": "object", "properties":
                                        {"Products": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "Quantity": {
                                                        "type": "number",
                                                        'description': f"This parameter is used to retrieve the product quantity. {{ quantities: customer ordered quantity }}"},
                                                    "Customer": {
                                                        "type": "string",
                                                        'description': f"This parameter is used to retrieve the customer name. {{ customer: customer name }}"},
                                                    "Product": {
                                                        "type": "string",
                                                        'description': f"This parameter is used to retrieve the Product name. {{ product: product name }}"},
                                                    "Variant": {
                                                        "type": "string",
                                                        "description": f"This parameter is used to retrieve the Product variant details. For example, if a customer order is confirmed, then retrieve {{ Variant: product Variant }}"},
                                                    "productId": {
                                                        "type": "number",
                                                        "description": f'Determine the Product ID of the product in the confirmed order. Fetch the correct ID based on the following product and ID mapping: , {self.function_description}'}},
                                                "required": [
                                                    "Quantity",
                                                    "Customer",
                                                    "Product",
                                                    "Variant",
                                                    "productId"]}}},
                                     "required": ["products"]}},
                                           "required": ["OrderDetails"]}},
                        "server": {
                            "url": f"{base_url}/vapi_voice_assistant/details"}},
                        {"type": "function",
                         "async": True,
                         "function": {
                             "name": "SetUserLanguagePreference",
                             "description": "This custom function retrieves"
                                            "the selected languages at the "
                                            "beginning of a voice "
                                            "assistance session if the user"
                                            " chooses the languages at the "
                                            "start of the session. This "
                                            "function must achieve the "
                                            "LanguageCode",
                             "parameters": {
                                 "type": "object",
                                 "properties": {
                                     "LanguagePreference": {
                                         "type": "object",
                                         "properties": {
                                             "LanguageCode": {
                                                 "type": "string",
                                                 "description": f"The code of the language chosen by the user. For example: en-IN for English (India), en-US for English (United States), es-LA for Spanish (Latin America).,our  lanagues and its code  is {self.language_function_description}"}, },
                                         "required": [
                                             "LanguageCode", ]}},
                                 "required": ["LanguagePreference"]}},
                         "server": {
                             "url": f"{base_url}/vapi_voice_assistant/language_details"}}, ], },
                "clientMessages": ["conversation-update", "function-call",
                                   "hang", "model-output", "speech-update",
                                   "status-update", "transcript", "tool-calls",
                                   "user-interrupted", "voice-input"],
                "serverMessages": ["conversation-update", "end-of-call-report",
                                   "function-call", "hang", "speech-update",
                                   "status-update", "tool-calls",
                                   "transfer-destination-request",
                                   "user-interrupted"],
                "messagePlan": {
                    "idleMessages": ["Feel free to ask whenever you're ready.",
                                     "I'm still here if you need assistance.",
                                     "How can I assist you further?",
                                     "Are you still there?",
                                     "Looking for something specific? I can "
                                     "assist with that!",
                                     "Need help choosing a product? I'm here"
                                     " to assist.",
                                     "I'm here if you need any assistance with"
                                     " your shopping."],
                    "idleTimeoutSeconds": 5,
                    "idleMessageMaxSpokenCount": 10},
                "name": self.name,
                "firstMessage": first_message,
                "serverUrl": f"{base_url}/vapi_voice_assistant/status",
                "endCallPhrases": [
                    end_message], }
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json"}
            response = requests.request("PATCH", url, json=payload,
                                        headers=headers)
            if response.status_code != 200:
                raise ValidationError(
                    "Assistant Update Failed: %s" % response.text)
        return res

    def unlink(self):
        """Ensure the corresponding assistant in the Vapi.ai platform is
        also deleted when the Odoo record is removed."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        for rec in self:
            url = f"https://api.vapi.ai/assistant/{rec.id_assistant}"
            headers = {
                "Authorization": f"Bearer {bearer}"}
            requests.request("DELETE", url, headers=headers)
        return super().unlink()

    def action_assistant_testing(self):
        """Triggers the client-side action to initiate voice assistant
         testing."""
        bearer = self.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_public_api_key')
        return {
            'type': 'ir.actions.client',
            'tag': 'action_voice_assistant',
            'params': {
                'assistant_id': self.id_assistant,
                'api_key': bearer,
                'assistant_name': self.name}}

    @api.model
    def reset_assistant(self, assistant_id):
        """ Reset Assistant with old values.
            After Assistant updated through js in the VAPI end."""
        if assistant_id:
            rec = self.search([('id_assistant', '=', assistant_id)])
            rec.write({})
