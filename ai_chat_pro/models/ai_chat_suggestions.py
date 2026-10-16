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

import logging
import re

from odoo import api, models

from .ai_chat_assistant import _stem

_logger = logging.getLogger(__name__)

MAX_SUGGESTIONS = 4
MAX_SUGGESTION_LENGTH = 120
MAX_APPS = 15


class AiChatAssistant(models.AbstractModel):
    """ Questions to click, offered with an answer the assistant is unsure of: when no
    data matched, when the AI hesitated between several data, when a draft got no value,
    or after an error. The user clicks one to ask it: a clearer question gets a better
    answer. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _get_suggestions(self, question, values, usage):
        if choices := usage.get('choices'):
            # the records the user is asked to choose among, as the request naming each one
            return list(dict.fromkeys(choices))
        result = values.get('result') or {}
        empty_draft = result.get('type') == 'draft' and result.get('state') == 'draft' and not result.get('values')
        if missing := usage.get('name_missing'):
            # a name no record bears: the same question, with the names that come close
            if missing['similar']:
                pattern = re.compile(re.escape(missing['text']), re.IGNORECASE)
                return _clean_suggestions([pattern.sub(name, question, count=1) for name in missing['similar']],
                                          question)
            usage = dict(usage, no_data=True)
        if not (values.get('is_error') or usage.get('no_data') or usage.get('alternatives') or empty_draft):
            return []
        suggestions = []
        try:
            suggestions = self._ask_suggestions(question, values, usage, empty_draft)
        except Exception as error:  # noqa: BLE001 - suggestions never fail an answer
            _logger.info("AI Chat Pro: no suggestion for %r: %s", question, error)
        return _clean_suggestions(suggestions, question)

    @api.model
    def _ask_suggestions(self, question, values, usage, empty_draft):
        """ Clearer questions the AI writing answers proposes, from what the assistant
        understood and could have understood. """
        context = []
        if usage.get('no_data'):
            menus = self._get_app_names()
            context.append("No data of Odoo matched the question." + (
                f" The apps the user can use: {', '.join(menus)}. Only suggest data of these apps." if menus else ""))
        if usage.get('alternatives'):
            context.append(f"It was read as: {usage.get('chosen')}. It may also be about: "
                           + "; ".join(usage['alternatives']) + ".")
        if empty_draft:
            Model = self.env[result_model] if (result_model := (values.get('result') or {}).get('model')) else None
            labels = [Model._fields[name]._description_string(self.env)
                      for name in list(self._get_create_fields(Model))[:8]] if Model is not None else []
            context.append(f"A new {(values.get('result') or {}).get('model_label')} was asked, but the request "
                           f"gives none of its values ({', '.join(labels)}).")
        if values.get('is_error'):
            context.append(f"The answer was an error: {str(values.get('content') or '')[:200]}")
        if (values.get('result') or {}).get('type') in ('draft', 'plan') and not empty_draft:
            # the record is being created already: creating it is no other reading
            context.append("The record asked is being created already: never suggest creating it.")
        answer = self._ask_json(
            "A user asks the AI assistant of Odoo, the business software, a question it is unsure of. Write up to "
            f"{MAX_SUGGESTIONS - 1} clearer requests the user may click instead, in the language of the question: "
            "each one short, complete and precise, starting with a verb (List, Show, Count, Total, Create...), "
            "naming the data as the apps and menus of the user do, "
            "keeping the names, numbers and periods the user wrote, never inventing a name. Cover the different "
            "readings of the question.\n"
            "Reply with ONLY minified JSON, no text: {\"suggestions\":[\"...\"]}\n"
            f"Question: {question}\n" + "\n".join(context), usage,
        )
        found = answer.get('suggestions')
        return [str(text) for text in found if isinstance(text, str)] if isinstance(found, list) else []

    @api.model
    def _get_example_data(self, count=3):
        """ The main data of the apps of the user, one per app, to write example
        questions with: the documents holding amounts first (orders, invoices), then the
        data reached by the most menus. ``[(app, menu name, model label)]`` """
        ranked = []
        for model_name, label, _words, menus in self._get_model_catalog():
            Model = self.env[model_name]
            paths = [menu[0] for menu in menus if '/' in menu[0] and not self._is_settings_candidate({'path': menu[0]})]
            if not paths or not Model._auto:
                continue
            has_amounts = any(field.type == 'monetary' and field.store for field in Model._fields.values())
            # the menu of the fewest words names the data best ("Orders", not "Orders to Invoice")
            leaf = min((path.rpartition('/')[2] for path in paths), key=lambda name: (len(name.split()), name))
            ranked.append((not has_amounts, -len(paths), model_name, paths[0].split('/')[0], leaf, label))
        # documents holding amounts, when there are some: the data users ask most about
        if any(not rank[0] for rank in ranked):
            ranked = [rank for rank in ranked if not rank[0]]
        examples, apps = [], set()
        for *_rank, _model_name, app, leaf, label in sorted(ranked):
            if app not in apps:
                apps.add(app)
                examples.append((app, leaf, label))
        return examples[:count]

    @api.model
    def _get_example_questions(self):
        """ Questions the user may ask, on the data of their own apps: shown on the
        landing page of the chat, and when no data matches a question. """
        data = self._get_example_data()
        if not data:
            return {}
        _app, leaf, _label = data[0]
        examples = {
            'insights': self.env._("%s per month this year", leaf),
            'export': self.env._("List the 10 latest %s", leaf.lower()),
            'others': [self.env._("List the 10 latest %s", other.lower()) for _app, other, _label in data],
        }
        if self._is_create_enabled():
            # named as its menu names it, in the singular ("Bills": a bill, not a journal entry)
            words = leaf.lower().split()
            examples['create'] = self.env._("Create a %s for ", " ".join([*words[:-1], _stem(words[-1])]))
        return examples

    @api.model
    def _get_app_names(self):
        """ The apps holding business data the user can ask about: those whose menus open
        the data the assistant reads (not the apps of tools: dashboards, discuss...). """
        apps = [path.split('/')[0] for _model, _label, _words, menus in self._get_model_catalog()
                for path, *_rest in menus if '/' in path and not self._is_settings_candidate({'path': path})]
        return list(dict.fromkeys(apps))[:MAX_APPS]


def _clean_suggestions(suggestions, question):
    """ Suggestions to show: short, different from the question and from each other. """
    seen = {(question or '').strip().lower().rstrip('?.!')}
    cleaned = []
    for text in suggestions:
        text = re.sub(r'\s+', ' ', str(text)).strip().strip('"“”')
        key = text.lower().rstrip('?.!')
        if not text or len(text) > MAX_SUGGESTION_LENGTH or key in seen:
            continue
        seen.add(key)
        cleaned.append(text[0].upper() + text[1:])
    return cleaned[:MAX_SUGGESTIONS]
