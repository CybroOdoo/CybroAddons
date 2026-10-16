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

import base64
import binascii
import copy
import io
import re

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .ai_chat_creator import _replace_placeholder, _resolve_steps

MAX_QUESTION_LENGTH = 1000
MAX_LISTED_CONVERSATIONS = 50


class AiChatConversation(models.Model):
    _name = 'ai.chat.conversation'
    _description = "AI Chat Conversation"
    _order = 'write_date desc, id desc'

    name = fields.Char(required=True, default=lambda self: self.env._("New chat"))
    user_id = fields.Many2one(
        'res.users', string="User", required=True, index=True, ondelete='cascade',
        default=lambda self: self.env.user,
    )
    message_ids = fields.One2many('ai.chat.message', 'conversation_id', string="Messages")
    message_count = fields.Integer(compute='_compute_totals')
    prompt_tokens = fields.Integer(compute='_compute_totals')
    completion_tokens = fields.Integer(compute='_compute_totals')
    cost = fields.Float(compute='_compute_totals', digits=(16, 6))

    @api.depends('message_ids.prompt_tokens', 'message_ids.completion_tokens', 'message_ids.cost')
    def _compute_totals(self):
        for conversation in self:
            messages = conversation.message_ids
            conversation.message_count = len(messages)
            conversation.prompt_tokens = sum(messages.mapped('prompt_tokens'))
            conversation.completion_tokens = sum(messages.mapped('completion_tokens'))
            conversation.cost = sum(messages.mapped('cost'))

    # ------------------------------------------------------------
    # Chat API, called by the web client
    # ------------------------------------------------------------

    @api.model
    def get_chat_data(self, conversation_id=False):
        """ The conversations of the current user, the messages of one of them, and the
        usage of the assistant. """
        self._check_chat_access()
        conversations = self.search([('user_id', '=', self.env.uid)], limit=MAX_LISTED_CONVERSATIONS)
        conversation = conversations.filtered(lambda c: c.id == conversation_id)[:1] if conversation_id else self
        return {
            'conversations': [c._get_conversation_summary() for c in conversations],
            'conversation': conversation._get_chat_values() if conversation else False,
            'usage': self.get_usage(),
            'voice': self._is_voice_enabled(),
            'deep_analysis': self.env['ai.chat.assistant']._is_deep_analysis_enabled(),
            # example questions on the data of the apps of the user
            'examples': self.env['ai.chat.assistant']._get_example_questions(),
            # reports download as PDF when the server can print them, else open to be printed
            'pdf_engine': self.env['ai.chat.message']._has_pdf_engine(),
        }

    @api.model
    def get_voice_assistant_state(self):
        """ What the voice assistant of the systray needs: whether voice questions are
        enabled. Without them, the systray opens the chat. """
        self._check_chat_access()
        return {'voice': self._is_voice_enabled()}

    @api.model
    def transcribe_audio(self, audio):
        """ The text of a question recorded by the current user, given in base64 as
        16 kHz mono 16-bit PCM, and the usage of the assistant with it. The text is
        empty when nobody speaks: the recording is paid for all the same, and kept in
        the usage, which an error would roll back. """
        self._check_chat_access()
        if not self._is_voice_enabled():
            raise UserError(self.env._("Voice questions are not enabled."))
        try:
            audio = base64.b64decode(audio or '', validate=True)
        except (binascii.Error, ValueError):
            raise UserError(self.env._("The recording could not be read. Please try again."))
        text = self.env['ai.chat.assistant']._transcribe(audio)
        return {'text': text[:MAX_QUESTION_LENGTH], 'usage': self.get_usage()}

    @api.model
    def create_draft_record(self, message_id):
        """ Create the record of a draft answer, as the current user. For a plan of
        several records, create the record of its current step, link it to the next
        steps, and move on to the next one.

        :return: the values of the answer, updated
        """
        message = self._get_draft_message(message_id, lock=True)
        result = copy.deepcopy(message.result)
        Assistant = self.env['ai.chat.assistant']
        if result['type'] == 'import':
            result, content = self._import_draft_values(message, result)
        elif result['type'] == 'draft':
            record = Assistant._create_from_draft(result)
            result.update(state='created', res_id=record.id, record_name=record.display_name)
            content = self.env._("%(label)s \"%(name)s\" created.", label=result['model_label'],
                                 name=record.display_name)
        else:
            steps, index = result['steps'], result['current']
            step = steps[index]
            record = Assistant._create_from_draft({**step, 'values': _resolve_steps(step['values'], steps, self.env)})
            step.update(state='created', res_id=record.id, record_name=record.display_name)
            # the next steps show the record instead of the name it was drafted with
            for next_step in steps[index + 1:]:
                _replace_placeholder(next_step, step.get('placeholder'), record.display_name)
            if index + 1 < len(steps):
                result['current'] = index + 1
                content = self.env._(
                    "%(label)s \"%(name)s\" created (step %(step)s of %(count)s). Check the next step.",
                    label=step['model_label'], name=record.display_name, step=index + 1, count=len(steps),
                )
            else:
                result.update(state='created', res_id=record.id, record_name=record.display_name)
                if result.get('several'):
                    content = self.env._("All %(count)s records created: %(names)s.", count=len(steps), names=", ".join(
                        f"\"{step.get('record_name') or ''}\"" for step in steps if step.get('state') == 'created'))
                else:
                    content = self.env._("%(label)s \"%(name)s\" created, with the %(count)s records it needed.",
                                         label=step['model_label'], name=record.display_name, count=len(steps) - 1)
        message.sudo().write({'content': content, 'result': result})
        return message._get_chat_values()

    @api.model
    def discard_draft(self, message_id):
        """ Discard a draft answer. For a plan, its steps still to create are discarded,
        the records already created are kept. """
        message = self._get_draft_message(message_id, lock=True)
        result = copy.deepcopy(message.result)
        result['state'] = 'discarded'
        for step in result.get('steps') or []:
            if step['state'] == 'draft':
                step['state'] = 'discarded'
        message.sudo().write({
            'content': self.env._("%(label)s discarded.", label=result['model_label']),
            'result': result,
        })
        return message._get_chat_values()

    @api.model
    def get_draft_form_action(self, message_id):
        """ The form of a new record filled with the values of a draft (or of the
        current step of a plan), to complete it before saving it. """
        message = self._get_draft_message(message_id)
        result = message.result
        draft = result
        if result['type'] == 'import':
            raise UserError(self.env._("An import has no form: import the file, or discard it."))
        if result['type'] == 'plan':
            draft = result['steps'][result['current']]
            draft = {**draft, 'values': _resolve_steps(draft['values'], result['steps'], self.env)}
        Assistant = self.env['ai.chat.assistant']
        if not Assistant._can_create(draft['model']):
            raise AccessError(self.env._("You are not allowed to create %s records.", draft['model_label']))
        values = draft.get('values') or {}
        if draft.get('copy_of'):
            values = Assistant._get_copy_form_values(draft)
        return {
            'type': 'ir.actions.act_window',
            'name': draft['title'],
            'res_model': draft['model'],
            'views': [[False, 'form']],
            'target': 'current',
            'context': {**(draft.get('context') or {}), **{f"default_{name}": value for name, value in values.items()}},
        }

    @api.model
    def _get_draft_message(self, message_id, lock=False):
        """ A draft answer of the current user, still to be created. """
        self._check_chat_access()
        message = self.env['ai.chat.message'].browse(message_id).exists()
        if not message or message.conversation_id.user_id != self.env.user:
            raise AccessError(self.env._("This message does not exist or is not yours."))
        if lock:
            # a draft is created once, even if confirmed twice at the same time
            self.env.cr.execute("SELECT id FROM ai_chat_message WHERE id = %s FOR UPDATE", [message.id])
            message.invalidate_recordset(['result'])
        draft = message.result or {}
        if draft.get('type') not in ('draft', 'plan', 'import'):
            raise UserError(self.env._("This answer is no record to create."))
        if lock and draft.get('state') != 'draft':
            raise UserError(self.env._("This record was already created or discarded."))
        return message

    @api.model
    def _is_voice_enabled(self):
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        return IrConfigParameter.get_bool('ai_chat_pro.voice') and bool(
            IrConfigParameter.get_str('ai_chat_pro.openrouter_api_key'))

    @api.model
    def get_usage(self, refresh_balance=False):
        """ Tokens and amount spent by the current user. Administrators of the assistant
        also get the spending of all users, and the balance of the OpenRouter account. """
        self._check_chat_access()
        Message = self.env['ai.chat.message']

        def totals(domain):
            [(prompt, completion, cost, count)] = Message._read_group(
                [('role', '=', 'assistant'), *domain],
                aggregates=['prompt_tokens:sum', 'completion_tokens:sum', 'cost:sum', '__count'],
            )
            return {'tokens': (prompt or 0) + (completion or 0), 'cost': cost or 0.0, 'questions': count}

        Assistant = self.env['ai.chat.assistant']
        usage = {
            'user': totals([('user_id', '=', self.env.uid)]),
            'is_manager': False,
            # voice questions turned into text, apart from the answers
            'voice': {'user': Assistant._get_voice_usage([('user_id', '=', self.env.uid)])},
        }
        if self.env.user.has_group('ai_chat_pro.group_ai_chat_manager'):
            usage['voice']['company'] = Assistant._get_voice_usage([])
            usage.update({
                'is_manager': True,
                'company': totals([]),
                'balance': self.env['ai.chat.assistant']._get_openrouter_balance(refresh=refresh_balance),
            })
        return usage

    @api.model
    def ask_question(self, conversation_id, question, deep=False, attachment_ids=None, mentions=None):
        """ Answer a question in a conversation of the current user, created when not given.

        :param bool deep: answer with a deep analysis, when enabled in the settings
        :param list attachment_ids: files sent with the question (see ``upload_chat_attachment``)
        :param list mentions: records the question mentions with @, as ``{model, id}``
        """
        self._check_chat_access()
        question = (question or '').strip()
        if not question:
            raise UserError(self.env._("Please type a question."))
        if len(question) > MAX_QUESTION_LENGTH:
            raise UserError(self.env._("Your question is too long. Try to say it in fewer words."))
        if conversation_id:
            conversation = self.browse(conversation_id).exists()
            if not conversation or conversation.user_id != self.env.user:
                raise AccessError(self.env._("This conversation does not exist or is not yours."))
        else:
            conversation = self.create({'name': question[:60]})

        attachments = self._get_question_attachments(attachment_ids)
        mentions = self._get_question_mentions(mentions, question)
        previous_plan = conversation.message_ids.filtered(lambda m: m.role == 'assistant' and m.plan)[-1:].plan
        # what the conversation said so far, read before the question joins it
        memory = conversation._get_memory()
        question_message = self.env['ai.chat.message'].create({
            'conversation_id': conversation.id,
            'role': 'user',
            'content': question,
            'attachment_ids': [(6, 0, attachments.ids)],
            'mentions': mentions or False,
        })
        if attachments:
            # the files now belong to the question: readable by whoever can read it
            attachments.sudo().write({'res_model': 'ai.chat.message', 'res_id': question_message.id})
        # the records mentioned are exact references, read by the answer from its context
        Assistant = self.env['ai.chat.assistant'].with_context(ai_chat_mentions=mentions, ai_chat_memory=memory)
        answer = Assistant._answer(
            question, previous_plan=previous_plan, deep=bool(deep) and Assistant._is_deep_analysis_enabled(),
            attachments=attachments,
        )
        answer_message = self.env['ai.chat.message'].create({
            'conversation_id': conversation.id,
            'role': 'assistant',
            **answer,
        })
        result = answer.get('result') or {}
        # the files an answer makes: the repaired rows of an import, a report printed
        for key in ('plan_attachment_id',) + (('attachment_id',) if result.get('type') == 'print' else ()):
            if file_id := result.get(key):
                self.env['ir.attachment'].browse(file_id).sudo().write(
                    {'res_model': 'ai.chat.message', 'res_id': answer_message.id})
        return {
            'conversation': conversation._get_conversation_summary(),
            'messages': [question_message._get_chat_values(), answer_message._get_chat_values()],
            'usage': self.get_usage(),
        }

    def _check_chat_access(self):
        if not self.env.user.has_group('ai_chat_pro.group_ai_chat_user'):
            raise AccessError(self.env._("You are not allowed to use the AI assistant."))

    def _get_conversation_summary(self):
        self.ensure_one()
        return {'id': self.id, 'name': self.name, 'date': fields.Datetime.to_string(self.write_date)}

    def _get_chat_values(self):
        self.ensure_one()
        return {
            **self._get_conversation_summary(),
            'messages': [message._get_chat_values() for message in self.message_ids],
        }


class AiChatMessage(models.Model):
    _name = 'ai.chat.message'
    _description = "AI Chat Message"
    _order = 'id'

    conversation_id = fields.Many2one('ai.chat.conversation', required=True, index=True, ondelete='cascade')
    user_id = fields.Many2one(related='conversation_id.user_id', store=True)
    role = fields.Selection([('user', "User"), ('assistant', "Assistant")], required=True)
    content = fields.Text()
    result = fields.Json(help="Data shown with the answer: a table or a key figure.")
    plan = fields.Json(help="Query plan written by the AI, reused to understand follow-up questions.")
    is_error = fields.Boolean()
    source = fields.Selection([
        ('local', "No AI call"),
        ('openrouter', "OpenRouter"),
        ('openrouter_olg', "OpenRouter + Odoo AI"),
        # answers of earlier versions, taken from a cache that no longer exists
        ('cache', "Cache"),
        ('cache_olg', "Cache + Odoo AI"),
        ('olg', "Odoo AI"),
        ('deep', "Deep analysis"),
    ], help="What produced the answer.")
    decision_model = fields.Char(
        string="Decision Model", help="Model of OpenRouter's Decisions API (Jev) that chose the data of the answer.",
    )
    used_olg = fields.Boolean(string="Odoo AI", help="Whether Odoo's AI service wrote a part of the answer.")
    thoughts = fields.Json(help="How the agent worked the answer out: its thoughts and the questions it asked.")
    suggestions = fields.Json(help="Clearer questions the user may click, offered with an answer the assistant is "
                                   "unsure of.")
    text_model = fields.Char(
        string="Text Model", help="Model of OpenRouter that wrote the text of the answer instead of Odoo's AI service.",
    )
    prompt_tokens = fields.Integer()
    completion_tokens = fields.Integer()
    cost = fields.Float(digits=(16, 6), help="Cost reported by OpenRouter, in credits (USD).")

    def _export_xlsx(self):
        """ The table of an answer as an Excel file, read as the current user: only the
        users who can read the message (its author, administrators) can export it.

        :return: ``(file name, content)``
        """
        self.ensure_one()
        self.check_access('read')
        result = self.result
        if self.role != 'assistant' or not result:
            raise UserError(self.env._("This message has no data to export."))
        columns = result.get('columns') or [{'label': result.get('label') or '', 'numeric': False}]
        rows = result.get('rows') or [{'cells': [result.get('value') or ''], 'raw': [None]}]
        heading = result.get('heading') or result.get('title') or self.env._("Answer")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # a sheet name has at most 31 characters, and none of []:*?/\
        sheet = workbook.add_worksheet(re.sub(r'[\[\]:*?/\\]', ' ', heading)[:31] or "Answer")
        title = workbook.add_format({'bold': True, 'font_size': 14})
        muted = workbook.add_format({'font_color': '#6c757d'})
        header = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'bottom': 1})
        number = workbook.add_format({'num_format': '#,##0.00'})
        sheet.write(0, 0, heading, title)
        if result.get('tags'):
            sheet.write(1, 0, ", ".join(result['tags']), muted)
        first_row = 3
        widths = [len(str(column['label'])) for column in columns]
        for index, column in enumerate(columns):
            sheet.write(first_row, index, column['label'], header)
        for row_index, row in enumerate(rows, start=first_row + 1):
            raw = row.get('raw') or []
            for index, cell in enumerate(row['cells']):
                value = raw[index] if index < len(raw) else None
                if columns[index].get('numeric') and isinstance(value, (int, float)):
                    # the number itself, to compute with it
                    sheet.write_number(row_index, index, value, number)
                else:
                    sheet.write(row_index, index, cell)
                widths[index] = max(widths[index], len(str(cell)))
        for index, width in enumerate(widths):
            sheet.set_column(index, index, min(max(width + 2, 10), 60))
        sheet.freeze_panes(first_row + 1, 0)
        workbook.close()
        date = fields.Date.to_string(fields.Date.context_today(self))
        name = re.sub(r'[^\w-]+', '_', heading).strip('_')[:60] or 'answer'
        return f"{name}_{date}.xlsx", output.getvalue()

    def _get_chat_values(self):
        self.ensure_one()
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content or '',
            'result': self.result or False,
            'is_error': self.is_error,
            'source': self.source or False,
            'text_model': self.text_model or False,
            'suggestions': self.suggestions or [],
            'thoughts': self.thoughts or [],
            'decision_model': self.decision_model or False,
            'used_olg': self.used_olg,
            'tokens': self.prompt_tokens + self.completion_tokens,
            'cost': self.cost,
        }
