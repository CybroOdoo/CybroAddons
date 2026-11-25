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
import asyncio
import concurrent.futures
import inspect
import json
import logging
import urllib.parse
import urllib.request
from googletrans import Translator
from odoo import api, fields, models
import requests
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

PROVIDER = [
    ('groq', 'Groq'),
    ('google', 'Google (Gemini)'),
    ('openai', 'OpenAI'),
    ('anthropic', 'Anthropic'),
]
TRANSCRIBER_PROVIDER = [
    ('deepgram', 'Deepgram'),
    ('gladia', 'Gladia'),
    ('talkscriber', 'Talkscriber'),
    ('speechmatics', 'Speechmatics'),
]
STATE = [('draft', 'Draft'),
         ('done', 'Done')]

DEFAULT_CLIENT_MESSAGES = [
    "conversation-update", "function-call", "hang", "model-output",
    "speech-update", "status-update", "transcript", "tool-calls",
    "user-interrupted", "voice-input"
]

DEFAULT_SERVER_MESSAGES = [
    "end-of-call-report", "status-update", "tool-calls", "hang"
]

DEFAULT_MESSAGE_PLAN = {
    "idleMessages": [
        "Feel free to ask whenever you're ready.",
        "I'm still here if you need assistance.",
        "How can I assist you further?",
        "Are you still there?",
        "Looking for something specific? I can assist with that!",
        "Need help choosing a product? I'm here to assist.",
        "I'm here if you need any assistance with your shopping."
    ],
    "idleTimeoutSeconds": 5,
    "idleMessageMaxSpokenCount": 10
}


class OraAi(models.Model):
    """Model for the order assistant."""
    _name = "ora.ai"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Order Assistant"

    name = fields.Char(required=True,
                       help="Name of the AI assistant configuration.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company, required=True,
                                 help="Company associated with this AI assistant.")
    id_assistant = fields.Char(string="Assistant id", readonly=True,
                               copy=False, help="Unique identifier of the"
                                                "assistant created via "
                                                "external API.")
    first_message = fields.Text(compute="_compute_first_message",
                                readonly=True,
                                help="The default initial greeting spoken by the assistant when the voice session starts.")
    provider = fields.Selection(selection=PROVIDER,
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
                                          string="Available Models",
                                          compute='_compute_provider_models',
                                          readonly=True,
                                          help="Filtered list of models "
                                               "available based on the "
                                               "selected provider.")
    transcriber_provider = fields.Selection(selection=TRANSCRIBER_PROVIDER,
                                            default='deepgram', required=True,
                                            help="Speech-to-text service "
                                                 "provider for transcribing "
                                                 "voice input.")
    transcriber_model_id = fields.Many2one('transcriber.model',
                                           required=True,
                                           domain="[('id', 'in', transcriber_model_ids)]",
                                           help="Choose the transcription "
                                                "model best suited for the "
                                                "conversation context.")
    transcriber_model_ids = fields.Many2many('transcriber.model',
                                             string="Available Transcriber Models",
                                             compute='_compute_transcriber_models',
                                             readonly=True,
                                             help="List of available "
                                                  "transcription models "
                                                  "filtered by selected "
                                                  "provider.")
    language_id = fields.Many2one('ora.language',
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
                             readonly=True,
                             help="Current lifecycle status of the assistant"
                                  " configuration.")
    date = fields.Date(default=fields.Date.today,
                       readonly=True,
                       help="Date when the assistant was created or"
                            " activated.")
    prompt = fields.Text(string="Contents",
                         compute="_compute_prompt",
                         readonly=True,
                         help="The Contents can be used to configure the"
                              " context, role, personality, instructions "
                              "and so on for the assistant.", )
    end_call_phrases = fields.Text(default="goodbye",
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
                                       readonly=True,
                                       help="Compact JSON representation of product catalog mappings used by LLM function calls.")
    language_function_description = fields.Char(
        string="language function description",
        compute="_compute_language_function_description",
        readonly=True,
        help="Generated function spec for language preference "
             "handling used by the assistant.")

    # Capabilities & Creation Operations
    is_sale_order_creation = fields.Boolean(
        string="Sale Order Creation", default=True,
        help="Enable the voice assistant to create sales orders.")
    is_invoice_creation = fields.Boolean(
        string="Invoice Creation", default=False,
        help="Enable the voice assistant to create invoices.")
    is_product_creation = fields.Boolean(
        string="Product Creation", default=False,
        help="Enable the voice assistant to create products.")
    is_customer_creation = fields.Boolean(
        string="Customer Creation", default=True,
        help="Enable the voice assistant to register and create new customers.")

    def _translate_text(self, text, target_lang):
        """Translates the given text into the specified language."""
        if not text or not target_lang or target_lang == 'en':
            return text or ""
        # 1. Try lightweight Google Translate endpoint
        try:
            url = ('https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl='
                   + urllib.parse.quote(target_lang) + '&dt=t&q=' + urllib.parse.quote(text))
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                translated = ''.join([item[0] for item in data[0] if item and item[0]])
                if translated:
                    return translated
        except Exception as err:
            _logger.debug("Google translate endpoint error, falling back: %s", err)

        # 2. Try googletrans library
        try:
            translator = Translator()
            translated = translator.translate(text, dest=target_lang)
            if inspect.iscoroutine(translated):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        translated = pool.submit(asyncio.run, translated).result()
                else:
                    translated = asyncio.run(translated)
            return translated.text if hasattr(translated, 'text') else str(translated)
        except Exception:
            return text

    @api.depends('provider')
    def _compute_provider_models(self):
        """Populate the list of available provider models based on the
         selected provider."""
        for rec in self:
            if rec.provider:
                rec.provider_model_ids = self.env['provider.model'].search([
                    ('provider', '=', rec.provider)
                ])
            else:
                rec.provider_model_ids = self.env['provider.model'].search([], limit=100)

    @api.depends('transcriber_provider')
    def _compute_transcriber_models(self):
        """Assign available transcriber models based on the selected
         transcriber provider"""
        for rec in self:
            if rec.transcriber_provider:
                rec.transcriber_model_ids = self.env['transcriber.model'].search([
                    ('provider', '=', rec.transcriber_provider)
                ])
            else:
                rec.transcriber_model_ids = self.env['transcriber.model'].search([], limit=100)

    @api.onchange('provider')
    def _onchange_provider(self):
        """Auto-select the first valid model when provider changes."""
        for rec in self:
            if rec.provider:
                first_model = self.env['provider.model'].search([
                    ('provider', '=', rec.provider)
                ], limit=1)
                if not rec.provider_model_id or rec.provider_model_id.provider != rec.provider:
                    rec.provider_model_id = first_model

    @api.onchange('transcriber_provider')
    def _onchange_transcriber_provider(self):
        """Auto-select the first valid transcriber model when provider changes."""
        for rec in self:
            if rec.transcriber_provider:
                first_model = self.env['transcriber.model'].search([
                    ('provider', '=', rec.transcriber_provider)
                ], limit=1)
                if not rec.transcriber_model_id or rec.transcriber_model_id.provider != rec.transcriber_provider:
                    rec.transcriber_model_id = first_model

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

    @api.depends('company_id', 'file_ids', 'file_ids.name', 'file_ids.state', 'file_ids.id_file',
                 'is_lang_switch', 'language_ids', 'language_id',
                 'is_sale_order_creation', 'is_invoice_creation',
                 'is_product_creation', 'is_customer_creation')
    def _compute_prompt(self):
        """Computes a detailed prompt for the voice assistant based on
         the current product catalog, capabilities, and availability."""
        for rec in self:
            company_name = rec.company_id.name or self.env.company.name or 'Our Store'
            currency_symbol = rec.company_id.currency_id.symbol or self.env.company.currency_id.symbol or '$'

            # Capability Rules
            allowed_ops = []
            disallowed_ops = []
            if rec.is_sale_order_creation:
                allowed_ops.append("Sale Order Creation (Allowed to place and confirm sales orders with GetFinalOrderDetails)")
            else:
                disallowed_ops.append("Sale Order Creation (Strictly prohibited: decline placing or confirming sale orders)")

            if rec.is_customer_creation:
                allowed_ops.append("Customer Creation (Allowed to create new customers/contacts with CreateCustomer)")
            else:
                disallowed_ops.append("Customer Creation (Strictly prohibited: customer creation is disabled)")

            if rec.is_invoice_creation:
                allowed_ops.append("Invoice Creation (Allowed to create draft customer invoices with CreateInvoice)")
            else:
                disallowed_ops.append("Invoice Creation (Strictly prohibited: invoice creation is disabled)")

            if rec.is_product_creation:
                allowed_ops.append("Product Creation (Allowed to create new products with CreateProduct)")
            else:
                disallowed_ops.append("Product Creation (Strictly prohibited: product creation is disabled)")

            ops_summary = "\n### CAPABILITIES & AUTHORIZED OPERATIONS:\n"
            if allowed_ops:
                ops_summary += "Authorized Operations:\n" + "\n".join(f"- {op}" for op in allowed_ops) + "\n"
            if disallowed_ops:
                ops_summary += "Prohibited Operations:\n" + "\n".join(f"- {op}" for op in disallowed_ops) + "\n"

            # Operation-specific workflows and instructions
            op_instructions = ""

            # 1. Customer Creation Workflow
            if rec.is_customer_creation:
                op_instructions += (
                    "\n### CUSTOMER CREATION WORKFLOW (Tool: CreateCustomer):\n"
                    "- When the user asks to create or register a customer/contact (e.g., 'Create a customer named Amal George with phone 9876543210 and email amal@gmail.com'):\n"
                    "  1. Collect the customer's Name (required), and any mentioned Phone, Email, Company Name, Street, City, State, Country, and Type (Company or Individual).\n"
                    "  2. First call `CheckCustomerExists` to check if a customer with that name already exists.\n"
                    "     * If they exist: inform the user that an account with that name already exists, and ask if they wish to create a duplicate or use the existing one.\n"
                    "     * If not found: call the `CreateCustomer` tool with the collected details.\n"
                    "  3. Confirm the created customer's name and details back to the user.\n"
                )
            else:
                op_instructions += (
                    "\n### CUSTOMER CREATION RESTRICTION:\n"
                    "- Customer creation is DISABLED. If the user asks to create a customer, politely inform them that customer creation is disabled.\n"
                )

            # 2. Product Creation Workflow
            if rec.is_product_creation:
                op_instructions += (
                    "\n### PRODUCT CREATION WORKFLOW (Tool: CreateProduct):\n"
                    "- When the user asks to create a product (e.g., 'Create a product named Samsung Galaxy S25 with a sales price of 50000'):\n"
                    "  1. Collect Product Name (required), Sales Price, Cost, Product Type (Goods/Service), Internal Reference/SKU, and Category.\n"
                    "  2. Ask for any missing key details if appropriate, then call `CreateProduct`.\n"
                    "  3. Once created, confirm the product name and price back to the user.\n"
                )
            else:
                op_instructions += (
                    "\n### PRODUCT CREATION RESTRICTION:\n"
                    "- Product creation is DISABLED. Decline any requests to create new products.\n"
                )

            # 3. Invoice Creation Workflow
            if rec.is_invoice_creation:
                op_instructions += (
                    "\n### INVOICE CREATION WORKFLOW (Tool: CreateInvoice):\n"
                    "- When the user asks to create an invoice (e.g., 'Create an invoice for Amal George for two Samsung phones'):\n"
                    "  1. Identify the Customer name, invoiced products, quantities, unit prices, and applicable taxes.\n"
                    "  2. Confirm the invoice lines and total with the user.\n"
                    "  3. Upon confirmation, call `CreateInvoice` with Customer name and the InvoiceLines array.\n"
                    "  4. Confirm the created draft invoice reference to the user.\n"
                )
            else:
                op_instructions += (
                    "\n### INVOICE CREATION RESTRICTION:\n"
                    "- Invoice creation is DISABLED. Decline any requests to create customer invoices.\n"
                )

            if rec.is_customer_creation:
                cust_not_found_prompt = (
                    "Say 'I couldn't find an existing customer under [Customer Name]. Would you like me to create a new customer account for them, or would you like to search with another name?'\n"
                    "     * If they want to create a new account: Say 'Understood, I will register [Customer Name] as a new customer upon order confirmation.' and proceed to order items.\n"
                    "     * If they provide another name: Call `CheckCustomerExists` again for the new name.\n"
                )
                new_cust_prompt = (
                    "If they say new customer, ask: 'What is the customer's name for the new account?'\n"
                    "   - Once provided, confirm: 'Understood, I will register [Customer Name] as a new customer upon order confirmation.' and proceed to order items.\n"
                )
            else:
                cust_not_found_prompt = (
                    "Say 'I couldn't find an existing customer under [Customer Name]. Customer creation is currently disabled, so please provide the name of an existing customer.'\n"
                    "     * Call `CheckCustomerExists` again for the new name provided.\n"
                )
                new_cust_prompt = (
                    "If they say new customer, state: 'Creating new customer accounts is disabled. Please specify an existing registered customer.'\n"
                )

            so_rules = ""
            if rec.is_sale_order_creation:
                so_rules = (
                    f"### MANDATORY CUSTOMER SELECTION BEFORE SALE ORDER CREATION:\n"
                    f"- STRICT REQUIREMENT: Only support sale order creation AFTER customer selection is completed. You MUST NOT accept product orders, take quantities, or create a sale order before the customer has been identified or selected.\n"
                    f"- If the salesperson mentions products, asks to add items, or asks to create a sale order before identifying the customer, immediately guide them to identify the customer first: 'Before we select products, let's identify the customer. Is this order for an existing customer or a new customer?'\n\n"
                    f"### CUSTOMER SELECTION & VERIFICATION WORKFLOW:\n"
                    f"1. Ask Existing vs. New Customer:\n"
                    f"   - When starting an order, ask the salesperson: 'Is this order for an existing customer or a new customer?'\n"
                    f"2. Existing Customer Path:\n"
                    f"   - If they say existing customer, ask: 'What is the customer's name?'\n"
                    f"   - Once they provide the name, you MUST immediately call the function tool `CheckCustomerExists` with `customer_name`.\n"
                    f"   - When the tool returns that the customer EXISTS: Confirm with the salesperson ('Found [Customer Name]. Let's proceed with their order.') and proceed to product and quantity selection.\n"
                    f"   - When the tool returns that the customer was NOT FOUND: {cust_not_found_prompt}"
                    f"3. New Customer Path:\n"
                    f"   - {new_cust_prompt}"
                    f"4. Critical Rules:\n"
                    f"   - ONLY support sale order creation AFTER the customer selection is completed.\n"
                    f"   - NEVER ask 'What is your name?' — always ask for the CUSTOMER's name.\n"
                    f"   - NEVER place or confirm an order without knowing the customer name and whether they are existing or new.\n"
                    f"   - When confirming the order with the salesperson, state: 'The order will be for customer [Customer Name] for [Quantity] [Product]. May I confirm this order?'.\n\n"
                )
            else:
                so_rules = (
                    "### SALE ORDER CREATION RESTRICTION:\n"
                    "- Sale order creation is DISABLED. You must not create, place, or confirm sale orders. If asked to place an order, inform the salesperson that order creation is not enabled.\n\n"
                )

            prompt = (
                f"You are the internal sales voice assistant of '{company_name}'. "
                f"You are speaking with a salesperson (the user in Odoo), NOT directly with the customer.\n\n"
                f"### CORE PERSPECTIVE & IDENTITY:\n"
                f"- The person talking to you is the SALESPERSON.\n"
                f"- The customer is the client or organization for whom the salesperson is creating the order.\n"
                f"- Always refer to the customer in the third person (e.g., 'the customer', 'their order', 'customer [Customer Name]').\n"
                f"- NEVER address the salesperson as if they were the customer.\n"
                f"- When an order is confirmed, NEVER say 'Thank you for ordering, [Customer Name]'. Instead, confirm to the salesperson: 'The sales order for customer [Customer Name] has been successfully created. Goodbye!'\n\n"
                f"{ops_summary}\n"
                f"{op_instructions}\n"
                f"{so_rules}"
                f"If the salesperson asks for product details, first explain all "
                f"the details by category. Then, mention the product name, "
                f"followed by its price, in that order.\n")
            out_of_stock_prompt = "."
            out_of_stock_prompt_2 = "."
            has_public_categ = (
                'product.public.category' in self.env
                and 'public_categ_ids' in self.env['product.template']._fields
            )
            if has_public_categ:
                cate_ids = self.env['product.public.category'].search([], limit=100)
                category_field = 'public_categ_ids'
                category_operator = 'in'
            else:
                cate_ids = self.env['product.category'].search([], limit=100)
                category_field = 'categ_id'
                category_operator = '='

            def _append_product_info(record):
                nonlocal out_of_stock_prompt, out_of_stock_prompt_2
                p_text = f"  • {record.name}, {currency_symbol}{record.list_price:.2f}\n"
                optional_products = getattr(record, 'optional_product_ids', self.env['product.template']).mapped('name')
                variants = record.product_variant_ids
                allow_out_of_stock = getattr(record, 'allow_out_of_stock_order', True)
                if getattr(record, 'type', '') == 'product' and not allow_out_of_stock:
                    p_text += f" -quantity available:{int(getattr(record, 'qty_available', 0))}\n"
                    out_of_stock_prompt = (", don't say the available quantity"
                                           " even if it is out of stock, say "
                                           "only when it asked.")
                    out_of_stock_prompt_2 = (" ,if the quantity is greater than"
                                             " available quantity just say the"
                                             " available quantity in the stock."
                                             " ")
                if len(variants) > 1:
                    p_text += f"    - {len(variants)} variants\n"
                    for variant in variants:
                        attribute_values = (
                            variant.product_template_variant_value_ids.mapped(
                                'name'))
                        variant_details = ", ".join(attribute_values)
                        p_text += (f"        * {variant_details}, "
                                   f"{currency_symbol}{variant.lst_price:.2f}\n")
                if len(optional_products) > 0:
                    p_text += (f"    - {len(optional_products)} "
                               f"Optional Products\n")
                    for opt_product in optional_products:
                        p_text += f"     • {opt_product} \n"
                return p_text

            for cate in cate_ids:
                products = self.env['product.template'].search(
                    [(category_field, category_operator, cate.id),
                     ('sale_ok', '=', True),
                     ('active', '=', True)],
                     limit=20)
                if products:
                    prompt += f"\n{cate.display_name}\n"
                    for record in products:
                        prompt += _append_product_info(record)

            none_categ_products = self.env['product.template'].search(
                [(category_field, "=", False), ('sale_ok', '=', True), ('active', '=', True)],
                limit=20)
            if none_categ_products:
                prompt += "\n None category \n"
                for p_rec in none_categ_products:
                    prompt += f"  • {p_rec.name}, {currency_symbol}{p_rec.list_price:.2f} \n"
            prompt += (
                "\n When the salesperson gives voice commands"
                " to place an order, \n you should proceed by listing out all "
                "product options available without excluding any mentioned"
                f" products {out_of_stock_prompt}\n"
                "if the product has variants ask for which variant do they need.\n"
                "After the product is selected, ask for How many quantity"
                f" do they need{out_of_stock_prompt_2}\n"
                f"if the product has optional products ask would they like to add them? \n"
                f"Before confirming the order, ask 'Would you like to add anything"
                f" else to this order before confirming?' \n"
                f"Once the order details are finalized, confirm: 'The order will be for customer [Customer Name], may I confirm the order?' If the salesperson responds "
                f"affirmatively, kindly repeat back the order details "
                f"for confirmation.\n Keep all your responses short and simple."
                f" Use casual language, phrases like Umm..., Well..., and I "
                f"mean are preferred.\n"
                f"CRITICAL CLOSING INSTRUCTION: Once the order is confirmed and created, remember you are talking to the salesperson, NOT the customer. Do NOT say 'Thank you for ordering, [Customer Name]'. Instead, confirm to the salesperson: 'The sales order for customer [Customer Name] has been successfully created. Goodbye!'\n"
                f" This is a voice conversation, "
                f"so keep your responses short, like in a real conversation. "
                f"Don't ramble for too long")

            if rec.is_lang_switch and rec.language_ids:
                languages = rec.language_ids.mapped('name')
                lang_instruction = (
                    f"\n\n### MULTI-LANGUAGE INSTRUCTIONS:\n"
                    f"- You support multiple languages: {', '.join(languages)}.\n"
                    f"- At the start of the call, greet the salesperson and ask which language they prefer.\n"
                    f"- Once a language is chosen, conduct the entire conversation in that language.\n"
                )
            elif rec.language_id and rec.language_id.code != 'en':
                lang_name = rec.language_id.name
                lang_code = rec.language_id.code
                lang_instruction = (
                    f"\n\n### CRITICAL LANGUAGE INSTRUCTION:\n"
                    f"- Your primary speaking language is {lang_name} ({lang_code}).\n"
                    f"- You MUST always speak, reply, take orders, describe products, and answer questions in {lang_name}.\n"
                    f"- All greetings, questions, recommendations, and order confirmations MUST be spoken in {lang_name}.\n"
                    f"- Never say you do not know or do not speak {lang_name}. You are completely fluent in {lang_name}.\n"
                    f"- If the salesperson speaks to you in {lang_name} or English, always reply politely in {lang_name} (unless they explicitly request another language).\n"
                )
            else:
                lang_instruction = ""
            if rec.file_ids:
                file_names = ", ".join(rec.file_ids.mapped('name') or [f.filename for f in rec.file_ids if f.filename])
                kb_instruction = (
                    f"\n\n### KNOWLEDGE BASE & SCOPE INSTRUCTIONS:\n"
                    f"- You are exclusively assigned the following Knowledge Base topic(s): {file_names}.\n"
                    f"- You MUST use your attached Knowledge Base to answer user questions regarding {file_names}.\n"
                    f"- STRICT DOMAIN BOUNDARY: Your expertise is strictly confined to company products/orders and {file_names}.\n"
                    f"- If a user asks questions about topics outside of '{file_names}' and outside of company products/orders "
                    f"(for example, asking about unrelated sports, other software, or general trivia not covered in '{file_names}'): "
                    f"you MUST politely decline to answer, stating that you only specialize in {file_names} and company product orders.\n"
                    f"- Do NOT use general internet knowledge to answer questions outside your assigned topic ({file_names}).\n"
                    f"- Keep all responses conversational, concise, and helpful within your domain.\n"
                )
                prompt += kb_instruction
            else:
                kb_instruction = (
                    "\n\n### DOMAIN SCOPE INSTRUCTIONS:\n"
                    "- You do not have any external knowledge base assigned.\n"
                    "- Your expertise is strictly limited to assisting with company product orders and questions about our product catalog.\n"
                    "- If asked about general knowledge, sports, software, or topics unrelated to our product catalog or orders, "
                    "politely explain that you only assist with company products and orders.\n"
                )
                prompt += kb_instruction

            rec.prompt = prompt + lang_instruction

    def _compute_function_description(self):
        """Computes a descriptive mapping of product names,
         variants, and their IDs."""
        for rec in self:
            function_description = ""
            domain = [('sale_ok', '=', True), ('active', '=', True)]
            if rec.company_id:
                domain.append(('company_id', 'in', [False, rec.company_id.id]))
            products = self.env['product.product'].search(domain, limit=100)
            for product in products:
                variant_values = ", ".join(
                    product.product_template_attribute_value_ids.mapped('name'))
                function_description += (f"{product.name} {variant_values} :"
                                         f" {product.id},  \n")
            rec.function_description = function_description

    @api.depends('name', 'language_id', 'language_ids', 'is_lang_switch')
    def _compute_first_message(self):
        """Computes the initial greeting message for the voice assistant."""
        for rec in self:
            if rec.language_ids and rec.is_lang_switch:
                languages = rec.language_ids.mapped('name')
                result = ', '.join(languages)
                rec.first_message = (f"Hey, I am {rec.name}. Which "
                                     f"language would you like to choose? "
                                     f"We have several languages available "
                                     f"such as {result}. Which language "
                                     f"would you prefer?")
            elif rec.language_id and rec.language_id.code != 'en':
                lang_code = rec.language_id.code
                if lang_code == 'ml':
                    rec.first_message = f"നമസ്കാരം, ഞാൻ {rec.name} ആണ്. {rec.language_id.first_msg or 'ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?'}"
                else:
                    rec.first_message = rec._translate_text(f"Hey, I am {rec.name}. How can I help you today?", lang_code)
            else:
                rec.first_message = f"Hey, I am {rec.name}. How can I help you today?"

    def _get_vapi_base_url(self):
        """Resolves the public HTTPS base URL for Vapi webhooks, auto-detecting active tunnels if on localhost."""
        ICP = self.env['ir.config_parameter'].sudo()
        base_url = (ICP.get_str('ora_ai_base.vapi_webhook_base_url') or
                    ICP.get_str('web.base.url') or '').strip().rstrip('/')

        # If base_url points to localhost or private network, attempt to retrieve public URL from ngrok
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            try:
                ngrok_res = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
                if ngrok_res.ok:
                    tunnels = ngrok_res.json().get('tunnels', [])
                    for t in tunnels:
                        p_url = t.get('public_url', '').strip().rstrip('/')
                        if p_url.startswith('https://'):
                            base_url = p_url
                            ICP.set_str('ora_ai_base.vapi_webhook_base_url', base_url)
                            ICP.set_str('web.base.url', base_url)
                            ICP.set_str('web.base.url.freeze', 'True')
                            break
            except Exception as err:
                _logger.debug("Failed checking ngrok tunnels: %s", err)

        if base_url.startswith('http://'):
            base_url = 'https://' + base_url[7:]
            try:
                ICP.set_str('web.base.url', base_url)
                ICP.set_str('web.base.url.freeze', 'True')
            except Exception as err:
                _logger.debug("Failed setting secure web.base.url: %s", err)

        if 'localhost' in base_url or '127.0.0.1' in base_url:
            raise UserError(
                self.env._(
                    "Vapi cloud servers require a public HTTPS URL (localhost/127.0.0.1 is not reachable from the internet). "
                    "Please configure a public HTTPS domain (such as your ngrok tunnel) in Settings > Voice Assistant > "
                    "Public Webhook Base URL, or access Odoo through your public domain."
                )
            )

        if not base_url.startswith('https://'):
            raise AccessError(self.env._("Vapi requires the webhook URL to use HTTPS protocol."))

        return base_url

    def _get_or_create_webhook_secret(self):
        """Retrieves the shared Vapi webhook secret, generating a secure one if missing."""
        icp = self.env['ir.config_parameter'].sudo()
        secret = icp.get_str('ora_ai_base.vapi_webhook_secret')
        if not secret:
            import secrets
            secret = secrets.token_hex(24)
            icp.set_str('ora_ai_base.vapi_webhook_secret', secret)
        return secret

    def _get_transcriber_language(self, language_code):
        """Maps an ISO language code to a valid language supported by the selected transcriber."""
        deepgram_languages = {
            'en', 'bg', 'ca', 'zh', 'zh-CN', 'zh-HK', 'zh-Hans', 'zh-TW', 'zh-Hant',
            'cs', 'da', 'da-DK', 'nl', 'en-US', 'en-AU', 'en-GB', 'en-NZ', 'en-IN',
            'et', 'fi', 'nl-BE', 'fr', 'fr-CA', 'de', 'de-CH', 'el', 'hi', 'hu',
            'id', 'it', 'ja', 'ko', 'ko-KR', 'lv', 'lt', 'ms', 'multi', 'no', 'pl',
            'pt', 'pt-BR', 'ro', 'ru', 'sk', 'es', 'es-419', 'sv', 'sv-SE', 'th',
            'th-TH', 'tr', 'uk', 'vi'
        }
        if self.transcriber_provider == 'deepgram':
            if language_code in deepgram_languages:
                return language_code
            return 'multi'
        return language_code or 'en'

    def _get_assistant_tools(self, base_url, db_query, secret):
        """Constructs the tools specification for Vapi assistant."""
        db_name = self.env.cr.dbname or ''
        headers = {"X-Odoo-Database": db_name} if db_name else {}

        def _make_server_dict(endpoint):
            srv = {
                "url": f"{base_url}/vapi_voice_assistant/{endpoint}{db_query}",
                "headers": headers,
            }
            if secret:
                srv["secret"] = secret
            return srv

        order_server = _make_server_dict("details")
        check_customer_server = _make_server_dict("check_customer")
        invoice_server = _make_server_dict("create_invoice")
        customer_server = _make_server_dict("create_customer")
        product_server = _make_server_dict("create_product")
        lang_server = _make_server_dict("language_details")

        tools = []
        if self.is_sale_order_creation:
            tools.append({
                "type": "function",
                "async": True,
                "function": {
                    "name": "GetFinalOrderDetails",
                    "description": (
                        "This function is designed to retrieve order details from a voice assistant, "
                        "with order confirmation being a prerequisite for providing the details. "
                        "The function will be triggered after confirming the order. "
                        "Upon asking a confirmation question and receiving a 'yes' response, "
                        "this function must be activated."
                    ),
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
                                                    "description": "Product quantity ordered by customer."
                                                },
                                                "Customer": {
                                                    "type": "string",
                                                    "description": "Customer name."
                                                },
                                                "Product": {
                                                    "type": "string",
                                                    "description": "Product name."
                                                },
                                                "Variant": {
                                                    "type": "string",
                                                    "description": "Product variant details or '-'."
                                                },
                                                "productId": {
                                                    "type": "number",
                                                    "description": f"Product ID based on mapping: {self.function_description}"
                                                }
                                            },
                                            "required": ["Quantity", "Customer", "Product", "Variant", "productId"]
                                        }
                                    }
                                },
                                "required": ["Products"]
                            }
                        },
                        "required": ["OrderDetails"]
                    }
                },
                "server": order_server
            })

        if self.is_customer_creation:
            tools.append({
                "type": "function",
                "async": False,
                "function": {
                    "name": "CreateCustomer",
                    "description": (
                        "Registers and creates a new customer or contact in Odoo. "
                        "Call this when the user asks to create or register a customer with their details."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Full name of the customer or contact."},
                            "phone": {"type": "string", "description": "Phone or mobile number."},
                            "email": {"type": "string", "description": "Email address."},
                            "company_name": {"type": "string", "description": "Associated company or employer name."},
                            "street": {"type": "string", "description": "Street address."},
                            "city": {"type": "string", "description": "City."},
                            "state": {"type": "string", "description": "State or province."},
                            "country": {"type": "string", "description": "Country."},
                            "is_company": {"type": "boolean", "description": "True if customer is a Company, False for Individual."}
                        },
                        "required": ["name"]
                    }
                },
                "server": customer_server
            })

        if self.is_product_creation:
            tools.append({
                "type": "function",
                "async": False,
                "function": {
                    "name": "CreateProduct",
                    "description": (
                        "Creates a new product in the Odoo product catalog. "
                        "Call this when the user asks to create a product with its details (e.g. name, price, category)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Product name."},
                            "default_code": {"type": "string", "description": "Internal Reference or SKU."},
                            "type": {"type": "string", "description": "Product type: 'consu' for Goods, 'service' for Service."},
                            "list_price": {"type": "number", "description": "Sales price."},
                            "standard_price": {"type": "number", "description": "Cost price."},
                            "categ_name": {"type": "string", "description": "Product category name."},
                            "uom_name": {"type": "string", "description": "Unit of Measure (e.g. Units)."},
                            "barcode": {"type": "string", "description": "Barcode or UPC."},
                            "sale_ok": {"type": "boolean", "description": "Can be Sold (default True)."},
                            "purchase_ok": {"type": "boolean", "description": "Can be Purchased (default True)."}
                        },
                        "required": ["name"]
                    }
                },
                "server": product_server
            })


        if self.is_invoice_creation:
            tools.append({
                "type": "function",
                "async": False,
                "function": {
                    "name": "CreateInvoice",
                    "description": (
                        "Creates a customer invoice in Odoo in draft state. "
                        "Call this after confirming customer name, invoice lines, quantities, and prices."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "Customer": {"type": "string", "description": "Customer name."},
                            "InvoiceLines": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "Product": {"type": "string", "description": "Product name."},
                                        "Quantity": {"type": "number", "description": "Quantity invoiced."},
                                        "UnitPrice": {"type": "number", "description": "Unit price."},
                                        "Tax": {"type": "number", "description": "Tax percentage (e.g. 15 or 0)."},
                                        "productId": {"type": "number", "description": "Product ID if available."}
                                    },
                                    "required": ["Product", "Quantity"]
                                }
                            }
                        },
                        "required": ["Customer", "InvoiceLines"]
                    }
                },
                "server": invoice_server
            })

        if self.is_sale_order_creation or self.is_customer_creation or self.is_invoice_creation:
            tools.append({
                "type": "function",
                "async": False,
                "function": {
                    "name": "CheckCustomerExists",
                    "description": (
                        "Check if a customer name exists in Odoo's customer database. "
                        "Call this function immediately when an existing customer name is mentioned "
                        "to verify if their account exists before placing an order."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "The full or partial name of the existing customer to search in the database."
                            }
                        },
                        "required": ["customer_name"]
                    }
                },
                "server": check_customer_server
            })

        if self.is_lang_switch:
            tools.append({
                "type": "function",
                "async": True,
                "function": {
                    "name": "SetUserLanguagePreference",
                    "description": "Retrieves the chosen language at the beginning of a voice assistance session.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "LanguagePreference": {
                                "type": "object",
                                "properties": {
                                    "LanguageCode": {
                                        "type": "string",
                                        "description": f"Language code chosen by user. Languages: {self.language_function_description}"
                                    }
                                },
                                "required": ["LanguageCode"]
                            }
                        },
                        "required": ["LanguagePreference"]
                    }
                },
                "server": lang_server
            })

        return tools

    def _get_assistant_runtime_config(self):
        """Computes runtime config (language, voice, first_message, end_message)."""
        self.ensure_one()
        if self.is_lang_switch and self.language_ids:
            return "en", "qgj3VahzWaAK300v6H27", self.first_message, self.end_call_phrases

        language = (self.language_id.code if (self.language_id and self.language_id.code) else "en") or "en"
        voice = (self.language_id.voice if (self.language_id and self.language_id.voice) else "vj2Y0u1NaT1ayH6VYkYu") or "vj2Y0u1NaT1ayH6VYkYu"
        if language == 'ml' and (not self.first_message or self.first_message.startswith("Hey")):
            first_message = f"നമസ്കാരം, ഞാൻ {self.name} ആണ്. {self.language_id.first_msg or 'ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?'}"
        else:
            first_message = self._translate_text(self.first_message, language)
        end_message = self._translate_text(self.end_call_phrases, language)
        return language, voice, first_message, end_message

    def _handle_vapi_error(self, response, is_update=False):
        """Formats and raises descriptive UserError for failed Vapi API calls."""
        try:
            err_json = response.json()
            error_raw = err_json.get('message') or err_json.get('error') or response.text
        except Exception:
            error_raw = response.text
        if isinstance(error_raw, list):
            error_msg = "\n".join(str(m) for m in error_raw)
        else:
            error_msg = str(error_raw)

        lower_err = error_msg.lower()
        if "transcriber" in lower_err:
            raise UserError(
                self.env._(
                    "Transcriber Model Unavailable / Unsupported:\n\n"
                    "The selected Transcriber model '%(model)s' under provider '%(provider)s' is unavailable or rejected by Vapi.\n\n"
                    "Details:\n%(details)s\n\n"
                    "Please choose an active Transcriber model (e.g. Nova-2 or Nova-3).",
                    model=self.transcriber_model_id.name or self.transcriber_model_id.key,
                    provider=self.transcriber_provider,
                    details=error_msg)
            )
        if "model" in lower_err:
            raise UserError(
                self.env._(
                    "AI Model Unavailable / Unsupported:\n\n"
                    "The selected model '%(model)s' under provider '%(provider)s' is unavailable or rejected by Vapi.\n\n"
                    "Details:\n%(details)s\n\n"
                    "Please choose an active, working model from the list.",
                    model=self.provider_model_id.name or self.provider_model_id.key,
                    provider=self.provider,
                    details=error_msg)
            )
        action_name = "updating" if is_update else "creating"
        raise UserError(self.env._("Vapi error while %(action)s assistant: %(error)s", action=action_name, error=error_msg))

    def action_create_assistant(self):
        """Creates a voice assistant instance using the Vapi.ai API based
         on the assistant configuration."""
        base_url = self._get_vapi_base_url()
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_private_api_key')
        secret = self._get_or_create_webhook_secret()

        url = "https://api.vapi.ai/assistant"
        db_name = self.env.cr.dbname
        db_query = f"?db={db_name}" if db_name else ""
        language, voice, first_message, end_message = self._get_assistant_runtime_config()

        transcriber_lang = self._get_transcriber_language(language)
        valid_file_ids = [f.id_file for f in self.file_ids if f.id_file and f.state == 'uploaded']
        model_payload = {
            "provider": self.provider,
            "model": self.provider_model_id.key,
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt
                }
            ],
            "tools": self._get_assistant_tools(base_url, db_query, secret),
        }
        if valid_file_ids:
            model_payload["knowledgeBase"] = {
                "provider": "canonical",
                "fileIds": valid_file_ids
            }
        payload = {
            "transcriber": {
                "provider": self.transcriber_provider,
                "model": self.transcriber_model_id.key,
                "language": transcriber_lang,
                "smartFormat": True
            },
            "voice": {
                "voiceId": voice,
                "provider": "11labs",
            },
            "model": model_payload,
            "clientMessages": DEFAULT_CLIENT_MESSAGES,
            "serverMessages": DEFAULT_SERVER_MESSAGES,
            "messagePlan": DEFAULT_MESSAGE_PLAN,
            "name": self.name,
            "firstMessage": first_message,
            "serverUrl": f"{base_url}/vapi_voice_assistant/status{db_query}",
            "server": {
                "url": f"{base_url}/vapi_voice_assistant/status{db_query}",
                "headers": {"X-Odoo-Database": self.env.cr.dbname} if self.env.cr.dbname else {},
            },
            "endCallPhrases": [
                end_message
            ],
        }
        if secret:
            payload["serverUrlSecret"] = secret
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload,
                                    headers=headers, timeout=15)
        if not response.ok:
            self._handle_vapi_error(response, is_update=False)
        try:
            json_response = response.json()
        except Exception:
            json_response = {}
        self.write({'date': json_response.get('createdAt'),
                    'state': 'done',
                    'id_assistant': json_response.get('id')
                        })

    def write(self, vals):
        """Update the external Vapi.ai assistant configuration when
         the record is modified."""
        res = super().write(vals)
        if self.env.context.get('skip_vapi_sync'):
            return res
        vapi_fields = {
            'name', 'prompt', 'first_message', 'end_call_phrases',
            'provider', 'provider_model_id', 'transcriber_provider',
            'transcriber_model_id', 'language_id', 'is_lang_switch',
            'language_ids', 'file_ids',
            'is_sale_order_creation', 'is_invoice_creation',
            'is_product_creation', 'is_customer_creation',
        }
        if not any(f in vals for f in vapi_fields):
            return res
        for rec in self:
            if not rec.id_assistant:
                continue
            base_url = rec._get_vapi_base_url()
            bearer = self.env['ir.config_parameter'].sudo().get_str(
                'ora_ai_base.vapi_private_api_key')
            secret = rec._get_or_create_webhook_secret()
            db_name = self.env.cr.dbname
            db_query = f"?db={db_name}" if db_name else ""
            url = f"https://api.vapi.ai/assistant/{rec.id_assistant}"
            language, voice, first_message, end_message = rec._get_assistant_runtime_config()
            transcriber_lang = rec._get_transcriber_language(language)
            valid_file_ids = [f.id_file for f in rec.file_ids if f.id_file and f.state == 'uploaded']
            model_payload = {
                "provider": rec.provider,
                "model": rec.provider_model_id.key,
                "messages": [{
                    "role": "system",
                    "content": rec.prompt}],
                "tools": rec._get_assistant_tools(base_url, db_query, secret),
            }
            if valid_file_ids:
                model_payload["knowledgeBase"] = {
                    "provider": "canonical",
                    "fileIds": valid_file_ids
                }
            else:
                model_payload["knowledgeBase"] = None
            payload = {
                "transcriber": {
                    "provider": rec.transcriber_provider,
                    "model": rec.transcriber_model_id.key,
                    "language": transcriber_lang,
                    "smartFormat": True},
                "voice": {
                    "voiceId": voice,
                    "provider": "11labs"},
                "model": model_payload,
                "clientMessages": DEFAULT_CLIENT_MESSAGES,
                "serverMessages": DEFAULT_SERVER_MESSAGES,
                "messagePlan": DEFAULT_MESSAGE_PLAN,
                "name": rec.name,
                "firstMessage": first_message,
                "serverUrl": f"{base_url}/vapi_voice_assistant/status{db_query}",
                "server": {
                    "url": f"{base_url}/vapi_voice_assistant/status{db_query}",
                    "headers": {"X-Odoo-Database": self.env.cr.dbname} if self.env.cr.dbname else {},
                },
                "endCallPhrases": [end_message],
            }
            if secret:
                payload["serverUrlSecret"] = secret
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json"}
            response = requests.request("PATCH", url, json=payload,
                                        headers=headers, timeout=15)
            if response.status_code == 404:
                _logger.warning("Assistant %s (%s) not found on Vapi. Resetting state.", rec.name, rec.id_assistant)
                rec.with_context(skip_vapi_sync=True).write({'state': 'draft', 'id_assistant': False})
            elif not response.ok:
                rec._handle_vapi_error(response, is_update=True)
        return res

    def unlink(self):
        """Ensure the corresponding assistant in the Vapi.ai platform is
        also deleted when the Odoo record is removed."""
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_private_api_key')
        for rec in self:
            if rec.id_assistant and bearer:
                url = f"https://api.vapi.ai/assistant/{rec.id_assistant}"
                headers = {
                    "Authorization": f"Bearer {bearer}"}
                requests.request("DELETE", url, headers=headers, timeout=15)
        return super().unlink()

    def action_assistant_testing(self):
        """Validates configuration and opens Test Assistant modal dialog in test mode."""
        self.ensure_one()
        if not self.id_assistant:
            raise UserError(self.env._("Please click 'Create Assistant' first before testing."))
        if not self.provider_model_id:
            raise UserError(self.env._("Please select an AI Model before testing the assistant."))
        if not self.transcriber_model_id:
            raise UserError(self.env._("Please select a Transcriber Model before testing the assistant."))

        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_public_api_key')
        if not bearer:
            raise UserError(self.env._("Vapi Public API Key is missing. Please configure it in Voice Assistant Settings."))

        return {
            'type': 'ir.actions.client',
            'tag': 'action_voice_assistant',
            'target': 'new',
            'name': self.env._("Test Assistant: %(name)s", name=self.name),
            'context': {'dialog_size': 'large'},
            'params': {
                'assistant_id': self.id_assistant,
                'api_key': bearer,
                'assistant_name': self.name,
                'test_mode': True,
                'provider': self.provider or '',
                'provider_model': self.provider_model_id.name if self.provider_model_id else '',
                'language': self.language_id.name if self.language_id else '',
                'transcriber': self.transcriber_model_id.name if self.transcriber_model_id else '',
            }}

    @api.model
    def reset_assistant(self, assistant_id):
        """ Reset Assistant with old values.
            After Assistant updated through js in the VAPI end."""
        if assistant_id:
            rec = self.search([('id_assistant', '=', assistant_id)])
            rec.write({})

    @api.model
    def action_launch_voice_assistant(self):
        """Finds the active voice assistant and returns the client action to launch it."""
        domain = [
            ('state', '=', 'done'),
            ('id_assistant', '!=', False),
        ]
        assistants = self.search(domain + [('company_id', 'in', [False, self.env.company.id])], order='write_date desc, id desc')
        if not assistants:
            assistants = self.search(domain, order='write_date desc, id desc')

        if not assistants:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._("No Voice Assistant Active"),
                    'message': self.env._("No active voice assistant found. Please create and configure an assistant first."),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return assistants[0].action_assistant_testing()

    @api.model
    def get_available_assistants(self):
        """Returns active assistants for the systray dropdown menu."""
        bearer = self.env['ir.config_parameter'].sudo().get_str(
            'ora_ai_base.vapi_public_api_key') or ''
        domain = [
            ('state', '=', 'done'),
            ('id_assistant', '!=', False),
        ]
        assistants = self.search(
            domain + [('company_id', 'in', [False, self.env.company.id])],
            order='write_date desc, id desc'
        )
        if not assistants:
            assistants = self.search(domain, order='write_date desc, id desc')

        return [{
            'id': ast.id,
            'name': ast.name,
            'assistant_id': ast.id_assistant,
            'api_key': bearer,
            'language': ast.language_id.name if ast.language_id else '',
            'provider': ast.provider or '',
            'provider_model': ast.provider_model_id.name if ast.provider_model_id else '',
            'transcriber': ast.transcriber_model_id.name if ast.transcriber_model_id else '',
        } for ast in assistants]
