# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import hashlib
import re
import requests
from markupsafe import Markup
from openai import OpenAI
from odoo import http
from odoo.http import request


def preprocess_ai_output(text):
    """
    Preprocesses AI-generated text by carefully extracting and closing CSS rules.
    Args:
        text (str): Input text containing HTML and CSS
    Returns:
        str: Preprocessed text with properly closed CSS
    """
    text = re.sub(r'^```(html|css|plaintext)?\s*', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    # Check if style tags already exist
    style_match = re.search(r'<style>(.*?)</style>', text, re.DOTALL)
    if style_match:
        return text
    css_lines = []
    html_lines = []
    current_rule = []
    in_css_block = False
    for line in text.split('\n'):
        stripped_line = line.strip()
        if re.match(r'^(\.|#|[a-zA-Z])[\w\s,#>:.()-]+\s*{', stripped_line):
            in_css_block = True
            current_rule = [line]
        elif in_css_block:
            current_rule.append(line)
            if stripped_line.endswith('}'):
                css_lines.extend(current_rule)
                current_rule = []
                in_css_block = False
        else:
            if stripped_line:
                html_lines.append(line)
    if current_rule:
        if not current_rule[-1].strip().endswith('}'):
            current_rule[-1] = current_rule[-1] + '\n}'
        css_lines.extend(current_rule)
    if css_lines:
        css_output = "<style>\n" + "\n".join(css_lines) + "\n</style>"
    else:
        css_output = ""
    html_output = "\n".join(html_lines)
    final_output = f"{css_output}\n{html_output}" if css_output else html_output
    return final_output.strip()


class SnippetGenerator(http.Controller):


    def _generate_unique_id(self, snippet_name):
        """Generate a unique ID for the snippet to avoid CSS conflicts"""
        return hashlib.md5(f"{snippet_name}_{request.session.sid}".encode()).hexdigest()[
               :8]

    def _generate_openai_response(self, prompt, api_key, model_id, max_tokens,
                                  snippet_name):
        """Helper method for OpenAI API calls"""
        response = OpenAI(api_key=api_key).chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that generates website snippets similar to Odoo's inbuilt website snippets. "
                            "Create responsive snippets using Bootstrap classes, ensuring proper container and row/column structure. "
                            "Use placeholder images from 'https://via.placeholder.com/' with appropriate sizes. "
                            "Return only clean HTML and CSS without any wrapper divs or preview elements. "
                            "Do not include any code block markers (```). "
                            "Focus on creating functional, beautiful snippets that work well in Odoo's website builder. "
                            "Use modern design principles with good typography, spacing, and colors."
                 },
                {"role": "user", "content": prompt}
            ],
            max_tokens=int(max_tokens),
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def _generate_openrouter_response(self, prompt, api_key, model_id, max_tokens,
                                      snippet_name):
        """Helper method for OpenRouter API calls with improved error handling"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": request.env['ir.config_parameter'].sudo().get_param(
                'web.base.url', ''),
            "X-Title": "Odoo Integration"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system",
                 "content": "You are a helpful assistant that generates website snippets similar to Odoo's inbuilt website snippets. "
                            "Create responsive snippets using Bootstrap classes, ensuring proper container and row/column structure. "
                            "Use placeholder images from 'https://via.placeholder.com/' with appropriate sizes. "
                            "Return only clean HTML and CSS without any wrapper divs or preview elements. "
                            "Do not include any code block markers (```). "
                            "Focus on creating functional, beautiful snippets that work well in Odoo's website builder. "
                            "Use modern design principles with good typography, spacing, and colors."
                 },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": int(max_tokens),
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(
                f"OpenRouter API error: {response.status_code} - {response.text}")
        json_response = response.json()
        if 'choices' not in json_response or not json_response['choices']:
            raise Exception("Invalid response format from OpenRouter API")
        choice = json_response['choices'][0]
        if 'message' not in choice:
            raise Exception("No message in OpenRouter API response")
        message = choice['message']
        content = message.get('content', '')
        reasoning = message.get('reasoning', '')
        partial_content = content.strip() if content else reasoning.strip()
        if choice.get('finish_reason') == 'length' and partial_content:
            completion_prompt = f"""
            You previously started generating a website snippet but it was cut off.
            Please complete the snippet based on this partial content:
            {partial_content}
            Continue from where it was cut off and make sure the HTML/CSS is complete and valid.
            """
            completion_payload = {
                "model": model_id,
                "messages": [
                    {"role": "system",
                     "content": "You are completing a partially generated website snippet. "
                                "Return only HTML/CSS code to complete the snippet, don't start over."},
                    {"role": "user", "content": completion_prompt}
                ],
                "max_tokens": int(max_tokens),
                "temperature": 0.7
            }
            try:
                completion_response = requests.post(url, headers=headers,
                                                    json=completion_payload)
                completion_response.raise_for_status()
                completion_json = completion_response.json()
                if 'choices' in completion_json and completion_json['choices']:
                    completion_message = completion_json['choices'][0]['message']
                    completion_content = completion_message.get('content', '')
                    if completion_content:
                        cleaned_completion = re.sub(r"^```(html|css)?\s*", "",
                                                    completion_content.strip(),
                                                    flags=re.MULTILINE)
                        cleaned_completion = re.sub(r"\s*```$", "", cleaned_completion,
                                                    flags=re.MULTILINE)
                        combined_content = partial_content + "\n" + cleaned_completion
                        return combined_content
                return partial_content
            except Exception:
                return partial_content + "\n<!-- Note: This snippet is incomplete. The system attempted to complete it but encountered an error. -->"
        if content:
            return content.strip()
        elif reasoning:
            return reasoning.strip()
        else:
            raise Exception(
                "Empty response from AI model. Please try again with a "
                "different prompt or model.")

    @http.route('/website/generate_snippet', type='json', auth='user', website=True)
    def generate_snippet(self, **kwargs):
        """Single route to handle both OpenAI and OpenRouter snippet generation"""
        prompt = kwargs.get('prompt')
        snippet_name = kwargs.get('name')
        if not prompt:
            return {'error': "Prompt is required"}
        try:
            api_key = request.env['ir.config_parameter'].sudo().get_param('api_key')
            ai_system = request.env['ir.config_parameter'].sudo().get_param(
                'generative_ai_systems')
            max_tokens = request.env['ir.config_parameter'].sudo().get_param('max_token')
            if not api_key:
                return {'error': "API key not configured"}
            unique_id = self._generate_unique_id(snippet_name)
            try:
                if ai_system == 'openai':
                    model_id = request.env['ir.config_parameter'].sudo().get_param(
                        'model_id')
                    if not model_id:
                        return {'error': "No OpenAI model selected"}
                    snippet_text = self._generate_openai_response(prompt, api_key,
                                                                  model_id, max_tokens,
                                                                  snippet_name)
                elif ai_system == 'openrouter':
                    model_id = request.env['ir.config_parameter'].sudo().get_param(
                        'openrouter_model_id')
                    if not model_id or model_id == 'none':
                        return {'error': "No OpenRouter model selected"}
                    snippet_text = self._generate_openrouter_response(prompt, api_key,
                                                                      model_id,
                                                                      max_tokens,
                                                                      snippet_name)
                else:
                    return {'error': "Invalid AI system selected"}
            except Exception as api_error:
                return {'error': f"API Error: {str(api_error)}", 'retry': True}
            # Check if we got a valid response
            if not snippet_text or snippet_text.strip() == "":
                return {
                    'error': "AI did not generate any content. Please try again with a different prompt or model.",
                    'retry': True
                }
            processed_snippet_text = preprocess_ai_output(snippet_text)
            preview_style = f"""
<style>
.snippet-preview-{unique_id} {{
    position: relative !important;
    min-width: 600px !important;
    min-height: 400px !important;
    width: 100% !important;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
    overflow: visible !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 20px !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
}}

.snippet-preview-{unique_id}:hover {{
    transform: translateY(-5px) !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15) !important;
}}

.snippet-preview-{unique_id}::before {{
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    height: 4px !important;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    z-index: 1 !important;
}}

.snippet-name-{unique_id} {{
    position: absolute !important;
    top: -10px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    color: #2d3748 !important;
    padding: 12px 20px !important;
    border-radius: 25px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    opacity: 0 !important;
    visibility: hidden !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    z-index: 1000 !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    white-space: nowrap !important;
    pointer-events: none !important;
    min-width: 120px !important;
    text-align: center !important;
}}

.snippet-preview-{unique_id}:hover .snippet-name-{unique_id} {{
    opacity: 1 !important;
    visibility: visible !important;
    transform: translateX(-50%) translateY(-8px) !important;
    pointer-events: auto !important;
}}

/* Alternative hover trigger - also trigger on any child hover */
.snippet-preview-{unique_id} *:hover ~ .snippet-name-{unique_id},
.snippet-preview-{unique_id} .snippet-content-{unique_id}:hover ~ .snippet-name-{unique_id} {{
    opacity: 1 !important;
    visibility: visible !important;
    transform: translateX(-50%) translateY(-8px) !important;
}}

.snippet-content-{unique_id} {{
    width: 100% !important;
    max-width: 100% !important;
    z-index: 2 !important;
    position: relative !important;
    background: white !important;
    border-radius: 8px !important;
    padding: 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
    margin-top: 30px !important;
}}

/* Ensure content doesn't overflow */
.snippet-content-{unique_id} * {{
    max-width: 100% !important;
    box-sizing: border-box !important;
}}

/* Style for cards and common elements */
.snippet-content-{unique_id} .card {{
    border: none !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
    border-radius: 8px !important;
    transition: transform 0.2s ease !important;
}}

.snippet-content-{unique_id} .card:hover {{
    transform: translateY(-2px) !important;
}}

.snippet-content-{unique_id} .btn {{
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}}

.snippet-content-{unique_id} .btn-primary {{
    background: linear-gradient(45deg, #667eea, #764ba2) !important;
    border: none !important;
}}

.snippet-content-{unique_id} .btn-primary:hover {{
    background: linear-gradient(45deg, #5a67d8, #6b46c1) !important;
    transform: translateY(-1px) !important;
}}

/* Fallback JavaScript-free hover detection */
.snippet-preview-{unique_id}:focus-within .snippet-name-{unique_id} {{
    opacity: 1 !important;
    visibility: visible !important;
    transform: translateX(-50%) translateY(-8px) !important;
}}
</style>"""

            # Wrap content with unique scoped classes
            wrapped_content = f"""
{preview_style}
<div class="snippet-preview-{unique_id}" title="{snippet_name}">
    <div class="snippet-name-{unique_id}">{snippet_name}</div>
    <div class="snippet-content-{unique_id}">
        {processed_snippet_text}
    </div>
</div>
"""
            if not wrapped_content or wrapped_content.strip() == "":
                return {
                    'error': "Could not process AI output into a valid snippet. Please try again.",
                    'retry': True
                }
            snippet = request.env['website.snippet.data'].sudo().create({
                'name': snippet_name,
                'content': Markup(wrapped_content),
                'image_url': '/generative_ai/static/src/img/placeholder.png',
                'is_ai_generated': True,
            })
            request.env['ir.qweb'].clear_caches()
            request.env['ir.ui.view'].clear_caches()
            return {
                'success': True,
                'snippet': snippet,
                'snippet_id': snippet.id,
                'content': snippet.content,
                'image_url': '/generative_ai/static/src/img/placeholder.png'
            }
        except Exception as e:
            return {'error': str(e), 'retry': True}
