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
from datetime import date, datetime, timedelta
import logging
import requests

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


class AiChatController(http.Controller):

    @http.route('/ai_chat/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, **kwargs):
        """Handle chat message and return AI response"""
        try:
            # Extract parameters
            message_content = kwargs.get('message')
            try:
                ai_agent_id = int(kwargs.get('ai_agent_id') or 0)
                ai_model_id = int(kwargs.get('ai_model_id') or 0)
            except (TypeError, ValueError):
                _logger.warning("Invalid ID parameters: agent=%s, model=%s", kwargs.get('ai_agent_id'), kwargs.get('ai_model_id'))
                return {'error': 'Invalid agent or model ID'}

            session_id = kwargs.get('session_id')

            if not all([message_content, ai_agent_id, ai_model_id]):
                _logger.warning("Missing parameters: msg=%s, agent=%s, model=%s", bool(message_content), ai_agent_id, ai_model_id)
                return {'error': 'Missing required parameters'}

            _logger.info("Sending message to agent %s, model %s", ai_agent_id, ai_model_id)

            # Get or create session
            chat_session_model = request.env['ai.chat.session']
            session = None
            if session_id:
                try:
                    s_record = chat_session_model.browse(int(session_id))
                    if s_record.exists() and (s_record.user_id == request.env.user or request.env.user.has_group('base.group_system')):
                        session = s_record
                    else:
                        return {'error': 'Session not found or access denied'}
                except (TypeError, ValueError):
                    return {'error': 'Invalid session ID'}

            if not session or not session.exists():
                session = chat_session_model.get_or_create_session(ai_agent_id, ai_model_id)

            if not session or not session.exists():
                return {'error': 'Failed to create or find chat session'}

            # Create user message record
            user_msg_vals = {
                'session_id': session.id,
                'message_type': 'user',
                'content': message_content,
            }

            # Handle attachments
            attachments = kwargs.get('attachments', [])
            attachment_ids = []
            if attachments:
                attachment_model = request.env['ir.attachment']
                for attach in attachments:
                    try:
                        name = attach.get('name', 'attachment')
                        data = attach.get('data')  # Base64
                        if data:
                            # Remove data:image/...;base64, prefix if present
                            if ',' in data:
                                data = data.split(',')[1]

                            new_attach = attachment_model.create({
                                'name': name,
                                'datas': data,
                                'res_model': 'ai.chat.message',
                            })
                            attachment_ids.append(new_attach.id)
                    except Exception as e:
                        _logger.error("Failed to create attachment: %s", str(e))

            if attachment_ids:
                user_msg_vals['attachment_ids'] = [(6, 0, attachment_ids)]

            user_message = request.env['ai.chat.message'].create(user_msg_vals)

            # Link attachments to the message record
            if attachment_ids:
                request.env['ir.attachment'].browse(attachment_ids).write({
                    'res_id': user_message.id
                })

            # Get AI response
            if not session.ai_agent_id or not session.ai_model_id:
                return {'error': 'Session is missing agent or model configuration'}

            ai_response = self._get_ai_response(
                message_content,
                session.ai_agent_id,
                session.ai_model_id,
                session,
                user_message
            )

            # Create AI message record
            ai_message = request.env['ai.chat.message'].create({
                'session_id': session.id,
                'message_type': 'ai',
                'content': ai_response,
            })

            return {
                'success': True,
                'session_id': session.id,
                'user_message': {
                    'id': user_message.id,
                    'type': 'user',
                    'content': user_message.content,
                    'timestamp': user_message.timestamp.isoformat() + 'Z',
                    'attachments': [{
                        'id': a.id,
                        'name': a.name,
                        'url': f'/web/content/{a.id}',
                        'mimetype': a.mimetype
                    } for a in user_message.attachment_ids]
                },
                'ai_message': {
                    'id': ai_message.id,
                    'type': 'ai',
                    'content': ai_message.content,
                    'timestamp': ai_message.timestamp.isoformat() + 'Z',
                }
            }

        except AccessError:
            return {'error': 'Access denied'}
        except Exception as e:
            _logger.error("Error in send_message: %s", str(e))
            return {'error': str(e)}

    @http.route('/ai_chat/get_messages', type='json', auth='user', methods=['POST'])
    def get_messages(self, **kwargs):
        """Get all messages for a session"""
        try:
            ai_agent_id = kwargs.get('ai_agent_id')
            ai_model_id = kwargs.get('ai_model_id')
            session_id = kwargs.get('session_id')

            if not ai_agent_id or not ai_model_id:
                return {'error': 'Missing required parameters'}

            # Get or create session
            chat_session_model = request.env['ai.chat.session']
            try:
                ai_agent_id = int(ai_agent_id or 0)
                ai_model_id = int(ai_model_id or 0)
                s_id = int(session_id or 0) if session_id else None
            except (TypeError, ValueError):
                return {'error': 'Invalid agent, model, or session ID'}

            if s_id:
                session = chat_session_model.browse(s_id)
                if not session.exists() or (session.user_id != request.env.user and not request.env.user.has_group('base.group_system')):
                    return {'error': 'Session not found or access denied'}
            else:
                session = chat_session_model.get_or_create_session(ai_agent_id, ai_model_id)

            if not session or not session.exists():
                return {'error': 'Session not found'}

            # Get messages
            messages = []
            for message in session.message_ids:
                attachments = []
                for attach in message.attachment_ids:
                    attachments.append({
                        'id': attach.id,
                        'name': attach.name,
                        'url': f'/web/content/{attach.id}',
                        'mimetype': attach.mimetype
                    })
                messages.append({
                    'id': message.id,
                    'type': message.message_type,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat() + 'Z',
                    'attachments': attachments
                })

            return {
                'success': True,
                'session_id': session.id,
                'session_name': session.name,
                'messages': messages
            }

        except AccessError:
            return {'error': 'Access denied'}
        except Exception as e:
            _logger.error("Error in get_messages: %s", str(e))
            return {'error': str(e)}

    @http.route('/ai_chat/get_active_provider', type='json', auth='user', methods=['POST'])
    def get_active_provider(self, **kwargs):
        """Find the default/active AI provider and model for global chat"""
        try:
            user = request.env.user
            provider = user.active_ai_agent_id
            model = user.active_ai_model_id

            # Fallback to defaults if no preference or if preference is invalid
            if not provider or not provider.exists():
                provider = request.env['ai.providers'].search([], limit=1)
                model = provider.ai_model_ids[:1] if provider else None

            if not provider:
                return {'success': False, 'error': 'No AI Provider configured'}

            # Ensure model belongs to the provider
            if not model or not model.exists() or model not in provider.ai_model_ids:
                model = provider.ai_model_ids[:1]

            if not model:
                return {'success': False, 'error': 'No Models found for provider'}

            return {
                'success': True,
                'agent_id': provider.id,
                'agent_name': provider.name,
                'model_id': model.id,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/ai_chat/save_active_config', type='json', auth='user', methods=['POST'])
    def save_active_config(self, **kwargs):
        """Save the user's active AI agent and model preference"""
        try:
            agent_id = kwargs.get('ai_agent_id')
            model_id = kwargs.get('ai_model_id')

            vals = {}
            if agent_id:
                vals['active_ai_agent_id'] = int(agent_id)
            if model_id:
                vals['active_ai_model_id'] = int(model_id)

            if vals:
                request.env.user.write(vals)
                return {'success': True}
            return {'success': False, 'error': 'No data provided'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/ai_chat/get_all_providers', type='json', auth='user', methods=['POST'])
    def get_all_providers(self, **kwargs):
        """Return all providers and models for selection"""
        try:
            providers = request.env['ai.providers'].search([])
            data = []
            for p in providers:
                data.append({
                    'id': p.id,
                    'name': p.name,
                    'models': [{'id': m.id, 'name': m.model_id} for m in p.ai_model_ids]
                })
            return {'success': True, 'providers': data}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/ai_chat/get_sessions', type='json', auth='user', methods=['POST'])
    def get_sessions(self, **kwargs):
        """Return all sessions for the current user grouped by date"""
        try:
            sessions = request.env['ai.chat.session'].search([
                ('user_id', '=', request.env.user.id),
                ('is_active', '=', True),
            ], order='create_date desc', limit=50)

            today = date.today()
            yesterday = today - timedelta(days=1)
            last_week_start = today - timedelta(days=7)

            result = {'today': [], 'yesterday': [], 'last_week': [], 'older': []}
            for s in sessions:
                # Get last user message for preview
                last_user_msg = s.message_ids.filtered(lambda m: m.message_type == 'user')[-1:]
                preview = last_user_msg.content[:50] if last_user_msg else ''
                entry = {
                    'id': s.id,
                    'name': s.name,
                    'preview': preview,
                    'ai_agent_id': s.ai_agent_id.id,
                    'ai_model_id': s.ai_model_id.id,
                    'ai_agent_name': s.ai_agent_id.name,
                    'ai_model_name': s.ai_model_id.model_id,
                }
                session_date = s.create_date.date() if s.create_date else today
                if session_date == today:
                    result['today'].append(entry)
                elif session_date == yesterday:
                    result['yesterday'].append(entry)
                elif session_date >= last_week_start:
                    result['last_week'].append(entry)
                else:
                    result['older'].append(entry)

            return {'success': True, 'sessions': result}
        except Exception as e:
            _logger.error("Error in get_sessions: %s", str(e))
            return {'error': str(e)}

    @http.route('/ai_chat/delete_session', type='json', auth='user', methods=['POST'])
    def delete_session(self, **kwargs):
        """Delete a chat session and all its messages"""
        try:
            session_id = kwargs.get('session_id')
            if not session_id:
                return {'error': 'Missing session_id'}

            session = request.env['ai.chat.session'].browse(int(session_id))
            if session.exists():
                if session.user_id != request.env.user and not request.env.user.has_group('base.group_system'):
                    return {'error': 'Access denied'}
                session.unlink()
                return {'success': True}
            return {'error': 'Session not found'}
        except AccessError:
            return {'error': 'Access denied'}
        except Exception as e:
            _logger.error("Error in delete_session: %s", str(e))
            return {'error': str(e)}

    def _get_ai_response(self, message, ai_agent, ai_model, session, user_message=None):
        """
        Get AI response from the configured AI service
        """
        try:
            if not ai_agent or not ai_agent.exists():
                return "Error: AI Agent not found."

            agent_name = (ai_agent.name or "").lower()
            base_url = (ai_agent.api_base_url or "").lower()

            if 'openai' in agent_name or 'chatgpt' in agent_name or 'openai' in base_url:
                return self._call_openai_api(message, ai_model, session, user_message)
            elif 'anthropic' in agent_name or 'anthropic' in base_url:
                return self._call_anthropic_api(message, ai_model, session, user_message)
            else:
                # Default to Gemini
                return self._call_gemini_api(message, ai_agent, ai_model, session, user_message)

        except Exception as e:
            _logger.error("Error getting AI response: %s", str(e))
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

    def _call_gemini_api(self, message, ai_agent, ai_model, session, user_message=None):
        """Integrate with Google Gemini API"""
        api_key = ai_agent.sudo().api_key
        base_url = ai_agent.api_base_url or "https://generativelanguage.googleapis.com"
        model_name = ai_model.model_id or "gemini-pro"

        # The endpoint for gemini generateContent
        endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model_name}:generateContent"
        params = {"key": api_key}

        # Current date/time so the model gives accurate date answers
        now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")

        # Prepare context from history (last 10 messages)
        history = []
        for msg in session.message_ids[-11:-1]:  # Exclude current user msg which is already in DB
            role = "user" if msg.message_type == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg.content}]})

        user_parts = [{"text": message}]
        if user_message and user_message.attachment_ids:
            for attach in user_message.attachment_ids:
                if attach.mimetype and attach.mimetype.startswith('image/'):
                    data = attach.datas
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    user_parts.append({
                        "inline_data": {
                            "mime_type": attach.mimetype,
                            "data": data
                        }
                    })

        payload = {
            "contents": history + [{"role": "user", "parts": user_parts}]
        }

        # systemInstruction is only supported by gemini-1.5+, gemini-2.0+, and experimental models
        if "gemini-1.5" in model_name or "gemini-2.0" in model_name or "gemini-exp" in model_name:
            payload["systemInstruction"] = {
                "parts": [{"text": f"The current date and time is {now_str}. Use this as the authoritative current date whenever the user asks about today's date or time."}]
            }

        try:
            response = requests.post(endpoint, params=params, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        return candidate['content']['parts'][0]['text']
                return "I received an empty response from Gemini."
            elif response.status_code == 429:
                _logger.warning("Gemini rate limit hit for model %s: %s", model_name, response.text)
                try:
                    err_data = response.json()
                    # Extract retry delay if available
                    retry_delay = None
                    for detail in err_data.get('error', {}).get('details', []):
                        if detail.get('@type', '').endswith('RetryInfo'):
                            retry_delay = detail.get('retryDelay', '').replace('s', '')
                    if retry_delay:
                        return (
                            f"⚠️ The model **{model_name}** has reached its free-tier quota limit. "
                            f"Please wait {retry_delay} seconds and try again, or select a different model "
                            f"(e.g. gemini-2.5-flash)."
                        )
                except Exception:
                    pass
                return (
                    f"⚠️ Quota exceeded for **{model_name}**. This model has hit its free-tier rate limit. "
                    f"Please try a different model or wait a moment before retrying."
                )
            else:
                _logger.error("Gemini API error: %s - %s", response.status_code, response.text)
                try:
                    msg = response.json().get('error', {}).get('message', '')
                    return f"Gemini API Error ({response.status_code}): {msg}" if msg else f"Gemini API Error: {response.status_code}"
                except Exception:
                    return f"Gemini API Error: {response.status_code}"
        except Exception as e:
            _logger.error("Failed to call Gemini API: %s", str(e))
            return "Failed to connect to Gemini API."

    def _call_openai_api(self, message, ai_model, session, user_message=None):
        """Integrate with OpenAI API"""
        api_key = session.ai_agent_id.sudo().api_key
        base_url = (session.ai_agent_id.api_base_url or "https://api.openai.com").rstrip('/')
        if not base_url.endswith('/v1'):
            base_url += '/v1'

        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        history = []
        for msg in session.message_ids[-11:-1]:
            role = "user" if msg.message_type == "user" else "assistant"
            history.append({"role": role, "content": msg.content})

        user_content = [{"type": "text", "text": message}]
        if user_message and user_message.attachment_ids:
            for attach in user_message.attachment_ids:
                if attach.mimetype and attach.mimetype.startswith('image/'):
                    data = attach.datas
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{attach.mimetype};base64,{data}"}
                    })

        history.append({"role": "user", "content": user_content})

        payload = {
            "model": ai_model.model_id,
            "messages": history
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    return data['choices'][0].get('message', {}).get('content', '')
                return "I received an empty response from OpenAI."
            else:
                _logger.error("OpenAI API error: %s - %s", response.status_code, response.text)
                try:
                    msg = response.json().get('error', {}).get('message', '')
                    return f"OpenAI API Error ({response.status_code}): {msg}" if msg else f"OpenAI Error: {response.status_code}"
                except Exception:
                    return f"OpenAI API Error: {response.status_code}"
        except Exception as e:
            _logger.error("Failed to call OpenAI API: %s", str(e))
            return "Failed to connect to OpenAI API."

    def _call_anthropic_api(self, message, ai_model, session, user_message=None):
        """Integrate with Anthropic API"""
        api_key = session.ai_agent_id.sudo().api_key
        base_url = (session.ai_agent_id.api_base_url or "https://api.anthropic.com").rstrip('/')

        endpoint = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        history = []
        for msg in session.message_ids[-11:-1]:
            role = "user" if msg.message_type == "user" else "assistant"
            history.append({"role": role, "content": msg.content})

        user_content = [{"type": "text", "text": message}]
        if user_message and user_message.attachment_ids:
            for attach in user_message.attachment_ids:
                if attach.mimetype and attach.mimetype.startswith('image/'):
                    data = attach.datas
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    user_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": attach.mimetype,
                            "data": data
                        }
                    })

        history.append({"role": "user", "content": user_content})

        payload = {
            "model": ai_model.model_id,
            "max_tokens": 4096,
            "messages": history
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'content' in data and data['content']:
                    return data['content'][0].get('text', '')
                return "I received an empty response from Anthropic."
            else:
                _logger.error("Anthropic API error: %s - %s", response.status_code, response.text)
                try:
                    msg = response.json().get('error', {}).get('message', '')
                    return f"Anthropic API Error ({response.status_code}): {msg}" if msg else f"Anthropic Error: {response.status_code}"
                except Exception:
                    return f"Anthropic API Error: {response.status_code}"
        except Exception as e:
            _logger.error("Failed to call Anthropic API: %s", str(e))
            return "Failed to connect to Anthropic API."
