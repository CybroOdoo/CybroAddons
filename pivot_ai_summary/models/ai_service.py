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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from odoo.addons.iap.tools import iap_tools
from odoo import models, api

class PivotAISummary(models.AbstractModel):
    """Abstract model providing AI analysis and summarization
    logic for Pivot views."""
    _name = 'pivot.ai.summary'
    _description = 'Pivot AI Summary Service'

    @api.model
    def is_ai_enabled(self):
        """Check if the Pivot AI feature is enabled in the system
        parameters."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            'pivot_ai_summary.enable')
        return param in ['True', '1', True]

    @api.model
    def generate_summary(self, pivot_data, history=None):
        """Generate AI analysis for pivot data using the configured
        provider (Odoo OLG, Gemini, or OpenAI)."""
        if history is None:
            history = []

        icp = self.env['ir.config_parameter'].sudo()
        system = icp.get_param('pivot_ai_summary.system')
        api_key = icp.get_param('pivot_ai_summary.api_key')

        if system == 'odoo':
            olg_endpoint = icp.get_param(
                'html_editor.olg_api_endpoint',
                'https://olg.api.odoo.com')
            db_uuid = icp.get_param('database.uuid')
            formatted_history = []
            for msg in history:
                role = "assistant" if msg.get('role') == 'ai' else "user"
                formatted_history.append(
                    {'role': role, 'content': msg.get('content', '')})

            params = {
                'prompt': f"You are a business analyst. Use this "
                          f"Odoo pivot table data:\n\n{pivot_data}",
                'conversation_history': formatted_history,
                'database_id': db_uuid,
            }

            try:
                response = iap_tools.iap_jsonrpc(
                    olg_endpoint + "/api/olg/1/chat",
                    params=params, timeout=30)
                if response.get('status') == 'success':
                    return response.get('content')
                elif response.get('status') == 'limit_call_reached':
                    return "You have reached the maximum number of requests for Odoo AI. Try again later."
                else:
                    return f"Odoo AI Error: {response.get('status')}"
            except Exception as e:
                return f"Odoo AI Connection Error: {str(e)}"
        elif system == 'gemini':
            model_id = icp.get_param('pivot_ai_summary.gemini_model') or 'gemini-2.0-flash'
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"

            instruction = f"You are a business analyst. Use this Odoo pivot table data:\n\n{pivot_data}"
            contents = []

            if not history:
                contents.append({"role": "user", "parts": [{"text": instruction}]})
            else:
                for i, msg in enumerate(history):
                    role = "model" if msg.get('role') == 'ai' else "user"
                    text = msg.get('content', '')
                    if i == 0:
                        text = f"{instruction}\n\n{text}"
                    contents.append({"role": role, "parts": [{"text": text}]})

            try:
                response = requests.post(url, json={"contents": contents}, timeout=30)
                res_data = response.json()
                if response.status_code == 200 and 'candidates' in res_data:
                    return res_data['candidates'][0]['content']['parts'][0]['text']
                error_msg = res_data.get('error', {}).get('message', 'Unknown Error')
                return f"Gemini Error ({response.status_code}): {error_msg}"
            except Exception as e:
                return f"Gemini Connection Error: {str(e)}"

        else:
            if system == 'openai':
                url = "https://api.openai.com/v1/chat/completions"
                model = icp.get_param('pivot_ai_summary.openai_model') or 'gpt-4o-mini'
            else:
                url = "https://openrouter.ai/api/v1/chat/completions"
                model = icp.get_param('pivot_ai_summary.openrouter_model') or 'meta-llama/llama-3.1-8b-instruct:free'

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            messages = [{"role": "system",
                         "content": f"You are a business analyst. Use this Odoo pivot table data:\n\n{pivot_data}"}]
            for msg in history:
                role = "assistant" if msg.get('role') == 'ai' else "user"
                messages.append({"role": role, "content": msg.get('content', '')})

            try:
                response = requests.post(
                    url, headers=headers,
                    json={"model": model, "messages": messages, "max_tokens": 1000},
                    timeout=30
                )
                res_data = response.json()
                if response.status_code == 200:
                    return res_data['choices'][0]['message']['content']
                error_msg = res_data.get('error', {}).get('message', 'Unknown Error')
                return f"Error ({response.status_code}): {error_msg}"
            except Exception as e:
                return f"Connection Error: {str(e)}"