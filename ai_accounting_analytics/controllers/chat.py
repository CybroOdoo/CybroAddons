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
import json
import logging
import queue
import threading
import time

from werkzeug.exceptions import Forbidden

from odoo import api, http
from odoo.exceptions import AccessError, UserError
from odoo.http import Response, request
from odoo.modules.registry import Registry
from odoo.tools import config

_logger = logging.getLogger(__name__)

# Seconds without any event after which a "ping" line is sent: it keeps
# proxies (nginx closes silent connections after 60 s by default) from
# cutting the answer, and reveals a closed page so the answer stops.
HEARTBEAT_SECONDS = 10
# The answer must be finished this long before the server's limit_time_real
# (in multi-worker mode the request is killed when it is reached).
TIME_LIMIT_MARGIN = 15


def _ndjson(event):
    # Bytes: with ``direct_passthrough`` the chunks are written as they are.
    return (json.dumps(event, default=str) + '\n').encode()


def run_answer(dbname, uid, context, chat_id, message_id, events, cancel, deadline):
    """Answer a stored question in its own cursor and put the events in
    ``events`` (``None`` last). Runs in a thread of its own so the response
    can send heartbeats while the AI provider is silent. Each AI call is
    committed as soon as it is logged, so usage and the answer so far
    survive a closed page or a killed request."""
    thread = threading.current_thread()
    thread.dbname, thread.uid = dbname, uid
    try:
        with Registry(dbname).cursor() as cr:
            env = api.Environment(cr, uid, context)
            chat = env['ai.accounting.chat'].browse(chat_id)
            user_message = env['ai.accounting.message'].browse(message_id)
            events.put({'type': 'start', 'chat': {'id': chat.id, 'name': chat.name},
                        'user_message_id': message_id})
            for event in chat._ai_run_turn(user_message, cancel=cancel, deadline=deadline):
                if event['type'] == 'usage':
                    cr.commit()
                events.put(event)
    except Exception:
        _logger.exception("AI Analytics answer failed")
        events.put({'type': 'error', 'message': 'Unexpected server error.'})
    finally:
        events.put(None)


def relay_events(worker, events, cancel):
    """Response body: start ``worker`` (once the request transaction, which
    stored the question, is committed) and relay its events, with a ``ping``
    after HEARTBEAT_SECONDS of silence. However it ends, normally or because
    the browser went away (GeneratorExit on a failed write), the answer is
    told to stop."""
    worker.start()
    try:
        while True:
            try:
                event = events.get(timeout=HEARTBEAT_SECONDS)
            except queue.Empty:
                yield _ndjson({'type': 'ping'})
                continue
            if event is None:
                break
            yield _ndjson(event)
    finally:
        cancel.set()


class AiAccountingChatController(http.Controller):

    @http.route('/ai_accounting_analytics/chat/stream', type='http', auth='user',
                methods=['POST'])
    def chat_stream(self, question, chat_id=None, model_id=None, company_ids=None, **kwargs):
        """Answer a question, streaming newline-delimited JSON events.

        The question is validated and stored in the request transaction.
        The answer is then computed by ``run_answer`` in a thread, after the
        request is committed; this response relays its events and sends a
        ``ping`` when nothing happened for a while. When the page is closed or
        Stop is pressed, writing to the closed connection ends this generator,
        which tells the answer to stop.
        """
        started = time.monotonic()
        env = request.env
        if company_ids:
            try:
                allowed = [int(company_id) for company_id in company_ids.split(',')]
            except ValueError as error:
                raise Forbidden() from error
            if not set(allowed) <= set(env.user.company_ids.ids):
                raise Forbidden()
            env = env(context=dict(env.context, allowed_company_ids=allowed))
        try:
            chat, message = env['ai.accounting.chat']._ai_prepare_turn(
                question, chat_id=int(chat_id) if chat_id else None,
                model_id=int(model_id) if model_id else None)
        except (UserError, AccessError) as error:
            return self._stream_response(iter([_ndjson({'type': 'error', 'message': str(error)})]))

        limit = config['limit_time_real']
        deadline = started + limit - TIME_LIMIT_MARGIN if limit and limit > 0 else None
        events = queue.Queue()
        cancel = threading.Event()
        worker = threading.Thread(
            target=run_answer, name='ai_accounting_answer', daemon=True,
            args=(env.cr.dbname, env.uid, dict(env.context), chat.id, message.id, events, cancel, deadline))

        return self._stream_response(relay_events(worker, events, cancel))

    @staticmethod
    def _stream_response(body):
        return Response(body, direct_passthrough=True, headers=[
            ('Content-Type', 'application/x-ndjson; charset=utf-8'),
            ('Cache-Control', 'no-cache'),
            ('X-Accel-Buffering', 'no'),
        ])
