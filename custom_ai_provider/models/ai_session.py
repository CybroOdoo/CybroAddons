# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import copy
import logging
import threading
import time
import uuid

from odoo import api, models, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError
from odoo.modules.registry import Registry
from odoo.sql_db import PG_CONCURRENCY_EXCEPTIONS_TO_RETRY

from ..utils.openai_client import ProviderError, get_completions, get_provider_config

_logger = logging.getLogger(__name__)

MAX_CONCURRENCY_RETRIES = 3


class AiSession(models.Model):
    _inherit = 'ai.session'

    def _get_completions(self, messages, instructions, tools=None, **options):
        """Synchronous path (AI fields, server actions, composer, ...)."""
        config = get_provider_config(self.env)
        if not config['enabled']:
            return super()._get_completions(messages, instructions, tools, **options)
        try:
            return get_completions(config, messages, instructions, tools, **options)
        except ProviderError as e:
            raise UserError(str(e)) from e

    def _save_and_submit_request(
        self, payload, *, callback_type,
        request_round, request_round_limit,
        state,
    ) -> None:
        """Asynchronous path (AI chat agents).

        The original implementation posts the request to Odoo's AI server, which
        later calls back /ai/completion_result_ready. Here the provider is called
        from a background thread after commit, and the result is fed to the same
        continuation the webhook controller would have used.
        """
        config = get_provider_config(self.env)
        if not config['enabled']:
            return super()._save_and_submit_request(
                payload, callback_type=callback_type,
                request_round=request_round, request_round_limit=request_round_limit,
                state=state,
            )
        self.ensure_one()
        guest = self.env.context.get("guest")
        vals = {
            "loop_state": "waiting_model",
            "request_uuid": str(uuid.uuid4()),
            "request_webhook_secret": uuid.uuid4().hex,
            "request_round": request_round,
            "request_round_limit": request_round_limit,
            "request_payload": payload,
            "request_user_id": self.env.uid,
            "request_guest_id": guest.id if guest else False,
            "request_context": self._get_request_context_snapshot(),
            "resume_token": False,
            "pending_tool_call": False,
        }
        state["callback_type"] = callback_type
        vals["state"] = state
        self.write(vals)
        self._publish_response_state()

        dbname = self.env.cr.dbname
        request_uuid = vals["request_uuid"]
        payload = copy.deepcopy(payload)

        @self.env.cr.postcommit.add
        def submit():
            threading.Thread(
                target=_run_completion,
                args=(dbname, config, request_uuid, payload),
                name=f"ai_custom_provider-{request_uuid}",
                daemon=True,
            ).start()


def _run_completion(dbname, config, request_uuid, payload):
    error_message = None
    try:
        options = {k: v for k, v in payload.items() if k not in ('messages', 'instructions', 'tools')}
        result = get_completions(
            config, payload['messages'], payload['instructions'], payload.get('tools'), **options,
        )
        completion_result = {'kind': 'success', 'message': result['result']}
    except Exception as e:  # noqa: BLE001
        _logger.exception("AI custom provider request %s failed", request_uuid)
        error_message = str(e) if isinstance(e, ProviderError) else "The AI provider request failed."
        completion_result = {'kind': 'failure', 'code': 'request_failed'}

    for attempt in range(1, MAX_CONCURRENCY_RETRIES + 1):
        try:
            with Registry(dbname).cursor() as cr:
                _deliver_result(cr, request_uuid, completion_result, error_message)
            return
        except PG_CONCURRENCY_EXCEPTIONS_TO_RETRY:
            if attempt == MAX_CONCURRENCY_RETRIES:
                _logger.exception("AI custom provider: could not store result of %s", request_uuid)
                return
            time.sleep(0.5 * attempt)
        except Exception:  # noqa: BLE001
            _logger.exception("AI custom provider: could not process result of %s", request_uuid)
            return


def _deliver_result(cr, request_uuid, completion_result, error_message):
    """Mirror of ai.controllers.thread.AIThreadController.completion_result_ready."""
    su_env = api.Environment(cr, SUPERUSER_ID, {})
    session = su_env['ai.session'].search([
        ('request_uuid', '=', request_uuid),
        ('loop_state', '=', 'waiting_model'),
    ], limit=1)
    if not session:
        return
    context = dict(session.request_context or {})
    if session.request_guest_id:
        context['guest'] = su_env['mail.guest'].browse(session.request_guest_id.id)
    context['discuss_channel'] = su_env['discuss.channel'].browse(session.channel_id.id)
    env = api.Environment(cr, session.request_user_id.id, context)
    session = session.with_env(env).sudo()

    accessible_company_ids = set(env.user.company_ids.ids)
    for key in ('allowed_company_ids', 'active_company_ids'):
        if any(cid not in accessible_company_ids for cid in context.get(key, ())):
            raise AccessError(env._("Your company access changed while this AI response was running."))

    match session.state['callback_type']:
        case 'agent_loop':
            if completion_result['kind'] == 'failure' and error_message:
                session._finish_exchange('failed', content=error_message)
            else:
                session._continue_agent_loop(completion_result)
        case 'channel_name':
            session._continue_channel_name(completion_result)
