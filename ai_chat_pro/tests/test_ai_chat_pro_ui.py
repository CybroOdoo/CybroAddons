# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch

from odoo import http
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_voice import AiChatAssistant as AiChatVoice

WAIT_FOR = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
"""

UI_TEST = """
(async () => {
    const waitFor = async (selector) => {
        for (let i = 0; i < 150; i++) {
            const el = document.querySelector(selector);
            if (el) {
                return el;
            }
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
        throw new Error(`Element not found: ${selector}`);
    };
    (await waitFor(".o_ai_chat_action .o_ai_chat_capability_export")).click();
    await waitFor(".o_ai_chat_action .o_ai_chat_table tbody tr");
    await waitFor(".o_ai_chat_action .o_ai_chat_conversation.active");
    await waitFor(".o_ai_chat_usage .o_ai_chat_tokens");
    await waitFor(".o_ai_chat_usage .o_ai_chat_balance_amount");
    console.log("test successful");
})().catch((error) => console.error(error.message));
"""


@tagged('post_install', '-at_install')
class TestAiChatProUi(HttpCase):

    def test_chat_action_and_systray(self):
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]

        def decide(self_, state, questions, usage, api_key=None, ai_model=None):
            usage['ai_called'] = True
            return {'mode': {'type': 'choice', 'choice': 'list'}, 'sort': {'type': 'choice', 'choice': 'name'}}

        with (
            patch.object(AiChatAssistant, '_decide', decide),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', UI_TEST, login='admin', timeout=90)

    def test_chart(self):
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        total = {
            'model': 'res.partner', 'label': 'Contact', 'score': 2, 'path': '', 'domain': '', 'context': '',
            'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
            'subject_label': 'Companies', 'measures': [],
        }
        self.env['res.partner'].create([
            {'name': "Chart Partner A", 'company_id': self.env.company.id},
            {'name': "Chart Partner B", 'company_id': self.env['res.company'].create({'name': "Chart Co"}).id},
        ])

        def decide(self_, state, questions, usage, api_key=None, ai_model=None):
            usage['ai_called'] = True
            return {'direction': {'type': 'choice', 'choice': 'desc'}}

        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            (await waitFor(".o_ai_chat_action .o_ai_chat_capability_export")).click();
            await waitFor(".o_ai_chat_result .o_ai_chat_chart canvas");
            [...document.querySelectorAll(".o_ai_chat_segmented .btn")].find((b) => b.textContent.includes("Table")).click();
            await waitFor(".o_ai_chat_result .o_ai_chat_table tbody tr");
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatAssistant, '_decide', decide),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [total]),
            patch.object(AiChatAssistant, '_choose_candidate', lambda self_, *args, **kwargs: total),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)

    def test_downloads(self):
        """ The table of an answer downloads as Excel, for its author only, and its chart
        as a PNG image. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        total = {
            'model': 'res.partner', 'label': 'Contact', 'score': 2, 'path': '', 'domain': '', 'context': '',
            'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
            'subject_label': 'Companies', 'measures': [],
        }
        self.env['res.partner'].create([
            {'name': "Download Partner A", 'company_id': self.env.company.id},
            {'name': "Download Partner B", 'company_id': self.env['res.company'].create({'name': "Download Co"}).id},
        ])

        def decide(self_, state, questions, usage, api_key=None, ai_model=None):
            usage['ai_called'] = True
            return {'direction': {'type': 'choice', 'choice': 'desc'}}

        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            const downloads = odoo.loader.modules.get("@web/core/network/download");
            let saved = null;
            downloads.downloadFile._download = (data, name, mimetype) => { saved = { data, name, mimetype }; };
            (await waitFor(".o_ai_chat_action .o_ai_chat_capability_export")).click();
            await waitFor(".o_ai_chat_result .o_ai_chat_chart canvas");
            await new Promise((resolve) => setTimeout(resolve, 500));
            (await waitFor(".o_ai_chat_download_image")).click();
            for (let i = 0; i < 50 && !saved; i++) {
                await new Promise((resolve) => setTimeout(resolve, 100));
            }
            if (!saved || saved.mimetype !== "image/png" || !(saved.data instanceof Blob) || !saved.data.size
                    || !saved.name.endsWith(".png")) {
                throw new Error("The chart was not downloaded as a PNG image: " + JSON.stringify(saved));
            }
            await waitFor(".o_ai_chat_download_xlsx");
            const pdfButton = await waitFor(".o_ai_chat_download_pdf");
            // no PDF engine on the test server: the report opens to be printed by the browser
            if (!pdfButton.title.includes("print")) {
                throw new Error("The report button does not say it opens the report to print: " + pdfButton.title);
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatAssistant, '_decide', decide),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [total]),
            patch.object(AiChatAssistant, '_choose_candidate', lambda self_, *args, **kwargs: total),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
            # a server without PDF engine: reports are printed by the browser
            patch.object(type(self.env['ir.actions.report']), 'get_wkhtmltopdf_state', lambda self_: 'install'),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)

        message = self.env['ai.chat.message'].search([('role', '=', 'assistant')], order='id desc', limit=1)
        self.authenticate('admin', 'admin')
        response = self.url_open('/ai_chat_pro/export/xlsx', data={
            'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response.headers['Content-Type'])
        self.assertTrue(response.content.startswith(b'PK'), "an xlsx file is a zip archive")
        # the PDF report, printed by the report engine of Odoo
        def render_qweb_pdf(self_, report_ref, res_ids=None, data=None):
            return b'%PDF-1.7 report', 'pdf'

        with patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf', render_qweb_pdf):
            response = self.url_open('/ai_chat_pro/report/pdf', data={
                'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response.headers['Content-Disposition'])
        self.assertEqual(response.content, b'%PDF-1.7 report')
        # without a PDF engine, the report opens as a page that prints itself
        response = self.url_open('/ai_chat_pro/report/html', data={
            'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers['Content-Type'])
        self.assertIn(b'window.print()', response.content)
        self.assertIn(b'o_ai_chat_report', response.content)
        # another user cannot download the answer
        new_test_user(self.env, login='ai_chat_stranger', password='ai_chat_stranger',
                      groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        self.authenticate('ai_chat_stranger', 'ai_chat_stranger')
        response = self.url_open('/ai_chat_pro/export/xlsx', data={
            'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertNotEqual(response.status_code, 200)
        response = self.url_open('/ai_chat_pro/report/pdf', data={
            'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertNotEqual(response.status_code, 200)
        response = self.url_open('/ai_chat_pro/report/html', data={
            'message_id': message.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertNotEqual(response.status_code, 200)

    def test_create_record(self):
        """ A record asked for is shown as a draft, and created once confirmed. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.allow_create', 'True')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]

        def olg_chat(self_, prompt):
            return '{"values": {"name": "Tour Contact", "email": "tour.contact@example.com"}}'

        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            const input = await waitFor(".o_ai_chat_action .o_ai_chat_input");
            input.value = "Create a contact Tour Contact, tour.contact@example.com";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            (await waitFor(".o_ai_chat_action .o_ai_chat_send:not([disabled])")).click();
            const fields = await waitFor(".o_ai_chat_draft_draft .o_ai_chat_draft_fields");
            if (!fields.textContent.includes("tour.contact@example.com")) {
                throw new Error("The draft does not show the values: " + fields.textContent);
            }
            (await waitFor(".o_ai_chat_draft_create")).click();
            await waitFor(".o_ai_chat_draft_created .o_ai_chat_draft_open");
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatAssistant, '_olg_chat', olg_chat),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)
        partner = self.env['res.partner'].search([('email', '=', "tour.contact@example.com")])
        self.assertEqual(partner.name, "Tour Contact")

    def test_answer_names_the_openrouter_model(self):
        """ An answer written by a model of OpenRouter names it, in place of Odoo AI. """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.allow_create', 'True')
        IrConfigParameter.set_param('ai_chat_pro.reasoning_openrouter', 'True')
        IrConfigParameter.set_param('ai_chat_pro.reasoning_model', 'openai/gpt-4o-mini')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]

        def openrouter_post(self_, endpoint, payload, usage, api_key=None):
            usage['ai_called'] = True
            return {
                'choices': [{'message': {'content': '{"values": {"name": "Model Contact"}}'}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 20, 'cost': 0.0001},
            }

        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            const input = await waitFor(".o_ai_chat_action .o_ai_chat_input");
            input.value = "Create a contact Model Contact";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            (await waitFor(".o_ai_chat_action .o_ai_chat_send:not([disabled])")).click();
            await waitFor(".o_ai_chat_draft_draft .o_ai_chat_draft_fields");
            const meta = await waitFor(".o_ai_chat_message_assistant .o_ai_chat_meta");
            if (!meta.textContent.includes("openai/gpt-4o-mini") || meta.textContent.includes("Odoo AI")) {
                throw new Error("The answer does not name the model: " + meta.textContent);
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatAssistant, '_openrouter_post', openrouter_post),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)

    def test_create_plan(self):
        """ A record needing a new one is shown as a plan, whose steps are created one
        after the other. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.allow_create', 'True')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]

        def olg_chat(self_, prompt):
            if 'Only the Contact "Tour Company"' in prompt:
                return '{"values": {"name": "Tour Company"}}'
            return '{"values": {"name": "Tour Employee", "parent_id": "Tour Company"}}'

        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            const input = await waitFor(".o_ai_chat_action .o_ai_chat_input");
            input.value = "Create a contact Tour Employee at the new company Tour Company";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            (await waitFor(".o_ai_chat_action .o_ai_chat_send:not([disabled])")).click();
            const first = await waitFor(".o_ai_chat_plan .o_ai_chat_plan_current .o_ai_chat_draft_create");
            if (!first.textContent.includes("continue")) {
                throw new Error("The first step does not say the plan continues: " + first.textContent);
            }
            first.click();
            await waitFor(".o_ai_chat_plan .o_ai_chat_plan_step.o_ai_chat_draft_created");
            const current = await waitFor(".o_ai_chat_plan .o_ai_chat_plan_current");
            if (!current.textContent.includes("Tour Company") || current.textContent.includes("(new)")) {
                throw new Error("The next step does not show the record created: " + current.textContent);
            }
            current.querySelector(".o_ai_chat_draft_create").click();
            await waitFor(".o_ai_chat_plan.o_ai_chat_draft_created");
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatAssistant, '_olg_chat', olg_chat),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance',
                         lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}),
        ):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)
        employee = self.env['res.partner'].search([('name', '=', "Tour Employee")])
        self.assertEqual(employee.parent_id.name, "Tour Company")

    def test_voice_usage_in_sidebar(self):
        """ The speech to text is shown apart from the answers in the usage. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.voice', 'True')
        self.env['ai.chat.transcription'].create({
            'user_id': self.env.ref('base.user_admin').id, 'ai_model': 'google/gemini-2.5-flash-lite',
            'seconds': 75, 'prompt_tokens': 2400, 'completion_tokens': 20, 'cost': 0.00072,
        })
        code = """
        (async () => {
            const waitFor = async (selector) => {
                for (let i = 0; i < 150; i++) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return el;
                    }
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Element not found: ${selector}`);
            };
            const section = await waitFor(".o_ai_chat_voice_usage");
            const text = section.textContent;
            if (!text.includes("Speech to text") || section.querySelector(".o_ai_chat_voice_recordings").textContent !== "1"
                    || !text.includes("1 min 15 s") || !section.querySelector(".o_ai_chat_voice_spent").textContent.includes("0.00072")) {
                throw new Error("The speech to text usage is wrong: " + text);
            }
            await waitFor(".o_ai_chat_balance_amount");
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with patch.object(AiChatAssistant, '_get_openrouter_balance',
                          lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)

    def test_collapse_usage_and_sidebar(self):
        """ The usage card opens above the user and folds back, and the sidebar folds
        away to the left and comes back from the header; both are remembered. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        code = WAIT_FOR + """
            const panel = await waitFor(".o_ai_chat_action .o_ai_chat_panel");
            await waitFor(".o_ai_chat_usage .o_ai_chat_tokens");
            const pause = () => new Promise((resolve) => setTimeout(resolve, 400));

            // closed at first, under the user: a click opens it above, and it is remembered
            await waitFor(".o_ai_chat_usage_card.o_ai_chat_usage_collapsed .o_ai_chat_usage_toggle_summary");
            (await waitFor(".o_ai_chat_usage_toggle")).click();
            await pause();
            if (panel.querySelector(".o_ai_chat_usage_collapsed")) {
                throw new Error("The usage card is not unfolded");
            }
            if (localStorage.getItem("ai_chat_pro.usage_open") !== "1") {
                throw new Error("The unfolded usage card is not remembered");
            }
            document.querySelector(".o_ai_chat_usage_toggle").click();
            await waitFor(".o_ai_chat_usage_card.o_ai_chat_usage_collapsed");
            await pause();
            if (document.querySelector(".o_ai_chat_usage_body").getBoundingClientRect().height > 1) {
                throw new Error("The usage card is not folded");
            }

            (await waitFor(".o_ai_chat_sidebar_collapse")).click();
            await waitFor(".o_ai_chat_panel.o_ai_chat_sidebar_collapsed");
            await pause();
            if (document.querySelector(".o_ai_chat_sidebar").getBoundingClientRect().width > 1) {
                throw new Error("The sidebar is not folded away");
            }
            const toggle = await waitFor(".o_ai_chat_sidebar_toggle.o_ai_chat_toggle_visible");
            if (!toggle.offsetParent) {
                throw new Error("The button bringing back the sidebar is not shown");
            }
            const newChat = await waitFor(".o_ai_chat_header_new.o_ai_chat_toggle_visible");
            if (!newChat.offsetParent) {
                throw new Error("No new chat button while the sidebar is folded away");
            }
            toggle.click();
            await pause();
            if (panel.classList.contains("o_ai_chat_sidebar_collapsed")
                    || document.querySelector(".o_ai_chat_sidebar").getBoundingClientRect().width < 200) {
                throw new Error("The sidebar is not shown again");
            }
            if (localStorage.getItem("ai_chat_pro.sidebar_collapsed") !== "0") {
                throw new Error("The sidebar state is not remembered");
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with patch.object(AiChatAssistant, '_get_openrouter_balance',
                          lambda self_, refresh=False: {'amount': 4.5, 'kind': 'account', 'error': False}):
            self.browser_js('/odoo/action-ai_chat_pro.ai_chat_action_client', code, login='admin', timeout=90)

    def test_systray_without_voice_opens_the_chat(self):
        """ Without voice questions, the systray button opens the chat full screen. """
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.voice', False)
        code = WAIT_FOR + """
            (await waitFor(".o_ai_chat_systray_toggle")).click();
            await waitFor(".o_action .o_ai_chat_panel:not(.o_ai_chat_panel_compact)");
            if (document.querySelector(".o_ai_voice_panel")) {
                throw new Error("The voice assistant woke up although voice questions are disabled");
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with patch.object(AiChatAssistant, '_get_openrouter_balance', lambda self_, refresh=False: {}):
            self.browser_js('/odoo/action-base.action_res_users', code, login='admin', timeout=90)

    def test_voice_assistant(self):
        """ The systray button wakes the voice assistant: it listens, then opens the chat
        with the question heard asked in a new conversation. """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.voice', 'True')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]
        heard = []

        def transcribe(self_, audio):
            heard.append(len(audio))
            return "List me the contacts"

        def decide(self_, state, questions, usage, api_key=None, ai_model=None):
            usage['ai_called'] = True
            return {'mode': {'type': 'choice', 'choice': 'list'}, 'sort': {'type': 'choice', 'choice': 'name'}}

        code = WAIT_FOR + """
            // a microphone playing a tone, as headless browsers have none
            const audio = new AudioContext();
            const tone = audio.createOscillator();
            tone.start();
            // headless browsers start audio suspended, without a user gesture
            await audio.resume();
            // a new stream each time, as browsers do: the assistant ends the tracks it used
            navigator.mediaDevices.getUserMedia = async () => {
                const microphone = audio.createMediaStreamDestination();
                tone.connect(microphone);
                return microphone.stream;
            };

            // Escape cancels the assistant, without opening anything
            (await waitFor(".o_ai_chat_systray_toggle")).click();
            await waitFor(".o_ai_voice_panel.o_ai_voice_listening");
            (document.activeElement || document.body).dispatchEvent(
                new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true })
            );
            for (let i = 0; i < 50 && document.querySelector(".o_ai_voice_panel"); i++) {
                await new Promise((resolve) => setTimeout(resolve, 100));
            }
            if (document.querySelector(".o_ai_voice_panel") || document.querySelector(".o_ai_chat_action")) {
                throw new Error("Escape did not cancel the voice assistant");
            }

            (await waitFor(".o_ai_chat_systray_toggle")).click();
            const panel = await waitFor(".o_ai_voice_panel.o_ai_voice_listening");
            await waitFor(".o_ai_voice_glow");
            if (!panel.textContent.includes("Listening")) {
                throw new Error("The assistant does not say it listens: " + panel.textContent);
            }
            await new Promise((resolve) => setTimeout(resolve, 800));
            // tapping the orb ends the question
            panel.querySelector(".o_ai_voice_orb").click();
            await waitFor(".o_ai_voice_panel.o_ai_voice_heard");
            const question = await waitFor(".o_ai_chat_action .o_ai_chat_message_user .o_ai_chat_bubble");
            if (question.textContent !== "List me the contacts") {
                throw new Error("The chat does not ask the question heard: " + question.textContent);
            }
            await waitFor(".o_ai_chat_action .o_ai_chat_table tbody tr");
            await waitFor(".o_ai_chat_action .o_ai_chat_conversation.active");
            if (document.querySelector(".o_ai_voice_panel")) {
                throw new Error("The voice assistant stays open over the chat");
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatVoice, '_transcribe', transcribe),
            patch.object(AiChatAssistant, '_decide', decide),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance', lambda self_, refresh=False: {}),
        ):
            self.browser_js('/odoo/action-base.action_res_users', code, login='admin', timeout=120)
        self.assertEqual(len(heard), 1, "the cancelled question is not sent")
        self.assertTrue(heard[0] > 0, "the recording is sent")
        conversation = self.env['ai.chat.conversation'].search([], order='id desc', limit=1)
        self.assertEqual(conversation.name, "List me the contacts", "the question is asked in a new chat")

    def test_voice_assistant_done(self):
        """ Background noise can keep the silence ending a question from coming: the
        Done button and Enter finish the question at once. """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.voice', 'True')
        candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]
        heard = []

        def transcribe(self_, audio):
            heard.append(len(audio))
            return "List me the contacts"

        def decide(self_, state, questions, usage, api_key=None, ai_model=None):
            usage['ai_called'] = True
            return {'mode': {'type': 'choice', 'choice': 'list'}, 'sort': {'type': 'choice', 'choice': 'name'}}

        code = WAIT_FOR + """
            // a microphone hearing constant noise: never silent, so never stopping by itself
            const audio = new AudioContext();
            const noise = audio.createOscillator();
            noise.start();
            await audio.resume();
            navigator.mediaDevices.getUserMedia = async () => {
                const microphone = audio.createMediaStreamDestination();
                noise.connect(microphone);
                return microphone.stream;
            };
            const waitGone = async (selector) => {
                for (let i = 0; i < 100 && document.querySelector(selector); i++) {
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
            };

            // the Done button sends the question although the noise goes on
            (await waitFor(".o_ai_chat_systray_toggle")).click();
            const panel = await waitFor(".o_ai_voice_panel.o_ai_voice_listening");
            // longer than the silence ending a question: the noise keeps it listening
            await new Promise((resolve) => setTimeout(resolve, 2500));
            if (!document.querySelector(".o_ai_voice_panel.o_ai_voice_listening")) {
                throw new Error("The assistant stopped listening although the noise goes on");
            }
            panel.querySelector(".o_ai_voice_done").click();
            await waitFor(".o_ai_chat_action .o_ai_chat_message_user .o_ai_chat_bubble");
            await waitGone(".o_ai_voice_panel");

            // and so does Enter
            (await waitFor(".o_ai_chat_systray_toggle")).click();
            await waitFor(".o_ai_voice_panel.o_ai_voice_listening .o_ai_voice_done");
            await new Promise((resolve) => setTimeout(resolve, 500));
            (document.activeElement || document.body).dispatchEvent(
                new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true })
            );
            await waitFor(".o_ai_voice_panel.o_ai_voice_heard");
            await waitGone(".o_ai_voice_panel");
            if (document.querySelector(".o_ai_voice_done")) {
                throw new Error("The Done button stays once the question is sent");
            }
            console.log("test successful");
        })().catch((error) => console.error(error.message));
        """
        with (
            patch.object(AiChatVoice, '_transcribe', transcribe),
            patch.object(AiChatAssistant, '_decide', decide),
            patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates),
            patch.object(AiChatAssistant, '_get_openrouter_balance', lambda self_, refresh=False: {}),
        ):
            self.browser_js('/odoo/action-base.action_res_users', code, login='admin', timeout=120)
        self.assertEqual(len(heard), 2, "both questions are sent, by the Done button and by Enter")
