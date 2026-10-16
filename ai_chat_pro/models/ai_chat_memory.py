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

import re

from odoo import api, models

from .ai_chat_assistant import _keywords, _similar

# what the agent remembers of a conversation: its last turns, shortly, and the records they showed
MAX_MEMORY_MESSAGES = 8
MAX_MEMORY_TEXT = 300
MAX_MEMORY_ROWS = 5
MAX_MEMORY_RECORDS = 25


def _short(text, size=MAX_MEMORY_TEXT):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    return text if len(text) <= size else text[:size - 1] + "…"


class AiChatConversation(models.Model):
    """ The memory of a conversation: each new message is understood with the last
    turns of its conversation (what was asked, what was answered, from which data) and
    the records they showed, mentioned or created, so that "him", "that order" or "the
    second one" name them. Built from the messages themselves: nothing more is stored,
    and nothing is shared between conversations. """
    _inherit = 'ai.chat.conversation'

    def _get_memory(self):
        """ The last turns of the conversation, and the records they hold.

        :return: ``{'turns': [{'role', 'text'}], 'records': [{model, id, name, label}]}``
        """
        if not self:
            return {'turns': [], 'records': []}
        self.ensure_one()
        messages = self.message_ids.sorted('id')[-MAX_MEMORY_MESSAGES:]
        turns, records = [], []  # records: one list per message
        for message in messages:
            if message.role == 'user':
                turns.append({'role': 'user', 'text': _short(message.content)})
                records.append([mention for mention in (message.mentions or []) if isinstance(mention, dict)])
                continue
            text, shown = self._describe_answer(message)
            turns.append({'role': 'assistant', 'text': text})
            records.append(shown)
        # those of the latest messages first (in the order each message shows them), once each, and only
        # those the user may still read
        unique, seen = [], set()
        for record in (record for shown in reversed(records) for record in shown):
            key = (record.get('model'), record.get('id'))
            if key in seen or not record.get('name') or not self._can_read_memory_record(*key):
                continue
            seen.add(key)
            unique.append({field: record[field] for field in ('model', 'id', 'name', 'label') if field in record})
        return {'turns': turns, 'records': unique[:MAX_MEMORY_RECORDS]}

    @api.model
    def _can_read_memory_record(self, model_name, record_id):
        Assistant = self.env['ai.chat.assistant']
        if not isinstance(record_id, int) or not Assistant._is_allowed_model(model_name):
            return False
        record = self.env[model_name].browse(record_id).exists()
        return bool(record) and record.has_access('read')

    @api.model
    def _describe_answer(self, message):
        """ An answer, as the agent remembers it: a short text, and the records it shows
        (the rows of its table, the record it explains, prints or created). """
        result = message.result or {}
        plan = message.plan or {}
        kind = result.get('type')
        parts = [_short(message.content, 160)]
        records = []
        model_name = result.get('row_model') or result.get('model')
        label = self.env[model_name]._description if model_name in self.env else ''
        if kind == 'table':
            rows = result.get('rows') or []
            names = [str((row.get('cells') or [''])[0]) for row in rows[:MAX_MEMORY_ROWS]]
            if names:
                parts.append("Shown: " + ", ".join(f"{index}. {name}" for index, name in enumerate(names, start=1)))
            if model_name and (result.get('openable') or result.get('row_model')):
                records += [
                    {'model': model_name, 'id': row['id'], 'name': name, 'label': label}
                    for row, name in zip(rows[:MAX_MEMORY_ROWS], names) if row.get('id')
                ]
        elif kind in ('record', 'explain', 'print') and result.get('id'):
            records.append({'model': result.get('model'), 'id': result['id'], 'name': result.get('title'),
                            'label': result.get('model_label') or label})
        elif kind == 'draft' and result.get('state') == 'created' and result.get('res_id'):
            parts.append(f"Created {result.get('model_label')} {result.get('record_name')}")
            records.append({'model': result.get('model'), 'id': result['res_id'], 'name': result.get('record_name'),
                            'label': result.get('model_label') or label})
        elif kind == 'plan':
            for step in result.get('steps') or []:
                if step.get('state') == 'created' and step.get('res_id'):
                    records.append({'model': step.get('model'), 'id': step['res_id'], 'name': step.get('record_name'),
                                    'label': step.get('model_label')})
        source = plan.get('source_label') or plan.get('menu_path') or (label if kind in ('table', 'value') else '')
        if source:
            parts.append(f"(data: {source})")
        return _short(" ".join(part for part in parts if part)), records


class AiChatAssistant(models.AbstractModel):
    _inherit = 'ai.chat.assistant'

    @api.model
    def _get_memory(self):
        """ The memory of the conversation of the question being answered. """
        return self.env.context.get('ai_chat_memory') or {'turns': [], 'records': []}

    @api.model
    def _describe_memory(self):
        """ The last turns of the conversation, as the agent tells Odoo's AI service. """
        memory = self._get_memory()
        lines = [f"{'User' if turn['role'] == 'user' else 'Assistant'}: {turn['text']}" for turn in memory['turns']]
        if memory['records']:
            lines.append("Records of the conversation: " + "; ".join(
                f"{record['name']} ({record.get('label') or record['model']})" for record in memory['records']))
        return "\n".join(lines)

    @api.model
    def _same_kind(self, kind, label):
        """ Whether a kind of record the agent read ("sales order") is the one a label
        names ("Sales Order"). """
        words = _keywords(kind)
        return bool(words) and any(_similar(word, other) for word in words for other in _keywords(label))

    @api.model
    def _find_remembered_record(self, name, family=()):
        """ The record of the conversation a name the agent read stands for: one it
        showed, mentioned or created, bearing that very name, of the kind of the name. """
        text = (name.get('text') or '').strip().lower()
        kind = name.get('label') or ''
        for record in self._get_memory()['records']:
            if record['model'] in family or text != str(record['name']).strip().lower():
                continue
            if not kind or self._same_kind(kind, record.get('label') or ''):
                return record
        return None
