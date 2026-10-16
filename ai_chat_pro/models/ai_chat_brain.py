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

from .ai_chat_assistant import _keywords, _normalize, _similar
from .ai_chat_creator import _loads_loosely

_logger = logging.getLogger(__name__)

# data questions a request answered step by step may take, at most
MAX_THINK_STEPS = 3
# what the brain reads of each answer of the data tool
MAX_OBSERVED_ROWS = 5
MAX_OBSERVED_CELL = 60
MAX_THOUGHT = 240
MAX_ANSWER = 1200


def _short(text, size):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    return text if len(text) <= size else text[:size - 1] + "…"


class AiChatAssistant(models.AbstractModel):
    """ The brain of the agent: it thinks with Odoo's AI service (or the OpenRouter
    model of the settings) only when a request needs it, so that simple questions stay
    one cheap step.

    - A request needing several steps ("the products of my biggest order": first the
      order, then its lines) is answered in a loop: each data question is answered by
      the data tool (the decision model plans its query), the brain reads what was
      found and decides the next question, with the names just found, or the answer.
    - An answer that found nothing (no data, a name no record bears, a record the data
      can not be filtered on, no record) is reflected on: the brain thinks why, and
      asks a better question once.

    Its thoughts are kept with the answer, to show the user how it was worked out.
    """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _is_thinking_enabled(self):
        return self.env['ir.config_parameter'].sudo().get_bool('ai_chat_pro.agent_thinking', True)

    @api.model
    def _run_data(self, question, previous_plan, usage, intent, deep=False):
        thinking = intent.get('routed') and self._is_thinking_enabled() \
            and not self.env.context.get('ai_chat_data_only')
        if thinking and intent.get('multi_step') and not deep:
            if (values := self._think_through(question, usage, intent)) is not None:
                return values
        values = super()._run_data(question, previous_plan, usage, intent, deep=deep)
        if thinking and values.get('source') != 'deep' and self._has_failed(values, usage):
            values = self._reflect(question, intent, values, usage)
        return values

    # ------------------------------------------------------------
    # Observing
    # ------------------------------------------------------------

    @api.model
    def _has_failed(self, values, usage):
        """ Whether the data tool found nothing answering the question. """
        if usage.get('no_data') or usage.get('name_missing'):
            return True
        result = values.get('result') or {}
        return result.get('type') == 'table' and not result.get('rows')

    @api.model
    def _observe(self, values):
        """ What an answer of the data tool found, shortly, as the brain reads it: the
        data it read, and its first rows. """
        result = values.get('result') or {}
        parts = [_short(values.get('content'), 200)]
        if result.get('type') in ('table', 'value') and result.get('rows'):
            columns = [column['label'] for column in result.get('columns') or []]
            if columns:
                parts.append("Columns: " + " | ".join(columns))
            parts += [
                " | ".join(_short(cell, MAX_OBSERVED_CELL) for cell in row.get('cells') or [])
                for row in result['rows'][:MAX_OBSERVED_ROWS]
            ]
        return "\n".join(part for part in parts if part)

    # ------------------------------------------------------------
    # Thinking step by step
    # ------------------------------------------------------------

    @api.model
    def _think_through(self, question, usage, intent):
        """ The answer to a request needing several data questions, one after the
        other; ``None`` when the brain finds no data question to ask. """
        request = intent.get('question') or question
        steps = intent.get('steps') or []
        step, is_last = (steps[0] if steps else None), False
        thoughts, observations, last, answer = [], [], None, ''
        for _index in range(MAX_THINK_STEPS):
            if step is None:
                decision = self._think(request, observations, usage)
                if decision.get('thought'):
                    thoughts.append(decision['thought'])
                if decision.get('action') == 'answer' or not decision.get('step'):
                    answer = decision.get('answer') or ''
                    break
                step, is_last = decision['step'], decision.get('last')
            values = self.with_context(ai_chat_intent=step, ai_chat_data_only=True)._answer_data(
                step['question'], None, usage)
            values.pop('escalate', None)
            observation = self._observe(values)
            observations.append((step['question'], observation))
            thoughts.append(self.env._("Asked: %(question)s → %(found)s", question=step['question'],
                                       found=_short(values.get('content'), 120)))
            last = values
            if is_last or self._has_failed(values, usage):
                break
            step = None
        if last is None:
            return None
        if self._has_failed(last, usage):
            return {**last, 'thoughts': thoughts}
        for flag in ('no_data', 'alternatives'):
            usage.pop(flag, None)
        return {
            **last,
            'content': answer or last.get('content'),
            'plan': {**(last.get('plan') or {}), 'question': request},
            'thoughts': thoughts,
        }

    @api.model
    def _think(self, request, observations, usage):
        """ The next action the brain decides from what was found so far:
        ``{'thought', 'action': 'ask'|'answer', 'step', 'last', 'answer'}``. """
        found = "\n".join(
            f"{index}. Asked: {asked}\nFound: {observation}"
            for index, (asked, observation) in enumerate(observations, start=1)
        ) or "Nothing yet."
        prompt = (
            "You are the reasoning of the AI assistant of Odoo, the business software. Its data tool answers one "
            "simple question on the data at a time: a list, a count, a total or a breakdown of one kind of records, "
            "filtered by names, periods or other records. Answer the user's request step by step.\n"
            + (f"Conversation so far:\n{memory}\n" if (memory := self._describe_memory()) else "")
            + f"Request: {request}\nDone so far:\n{found}\n"
            "Decide the next action. Reply with ONLY minified JSON, no text:\n"
            '{"thought":"<one short sentence>","action":"ask|answer",'
            '"step":{"q":"<the next simple data question, with the names found written out>","terms":["<words '
            'naming the data>"],"limit":<count asked or null>,"names":[{"label":"<kind of record>","text":"<name>"}]},'
            '"last":<true when the result of this step answers the request>,'
            '"answer":"<with answer: a short answer from the data found only, in the language of the request>"}'
        )
        # the names the brain may use: those of the request, of the conversation and of the data found
        written = f"{request}\n{memory}\n" + "\n".join(f"{asked}\n{observation}" for asked, observation in observations)
        decision = self._ask_brain(prompt, usage)
        step = self._clean_step(decision.get('step'), written.lower()) if decision.get('action') == 'ask' else None
        return {
            'thought': _short(decision.get('thought'), MAX_THOUGHT),
            'action': 'ask' if step else 'answer',
            'step': step,
            'last': decision.get('last') is True,
            'answer': _short(decision.get('answer'), MAX_ANSWER) if observations else '',
        }

    # ------------------------------------------------------------
    # Reflecting on a failed answer
    # ------------------------------------------------------------

    @api.model
    def _reflect(self, question, intent, values, usage):
        """ The answer, asked again once in a better way when the brain finds why the
        data tool found nothing; else the answer as it is, with the brain's thought. """
        tried = intent.get('question') or question
        plan = values.get('plan') or {}
        data = plan.get('source_label') or plan.get('menu_path') or (
            self.env[plan['model']]._description if plan.get('model') in self.env else "no data")
        observation = self._observe(values)
        prompt = (
            "You are the reasoning of the AI assistant of Odoo, the business software. Its data tool answers one "
            "simple question on the data at a time, and found nothing for the user's request.\n"
            + (f"Conversation so far:\n{memory}\n" if (memory := self._describe_memory()) else "")
            + f"Request: {question}\nAsked: {tried}\nData read: {data}\nFound: {observation}\n"
            "Think about why (another kind of records holds it, a name written otherwise, a filter or period too "
            "strict, a reference of another record...) and whether another simple data question answers the "
            "request. Never invent a name. Reply with ONLY minified JSON, no text:\n"
            '{"thought":"<one short sentence>","retry":{"q":"<the better data question>","terms":["<words naming '
            'the data>"],"limit":<count asked or null>,"names":[{"label":"<kind of record>","text":"<name>"}]} '
            'or null}'
        )
        decision = self._ask_brain(prompt, usage)
        thoughts = [thought] if (thought := _short(decision.get('thought'), MAX_THOUGHT)) else []
        retry = self._clean_step(decision.get('retry'), f"{question}\n{tried}\n{observation}\n{memory}".lower())
        if not retry or _normalize(retry['question']) == _normalize(tried) \
                or not self._is_fair_retry(retry, usage, f"{question} {tried}"):
            return {**values, 'thoughts': thoughts} if thoughts else values
        flags = {flag: usage.pop(flag) for flag in ('no_data', 'name_missing', 'alternatives') if flag in usage}
        try:
            with self.env.cr.savepoint():
                retried = self.with_context(ai_chat_intent=retry)._answer_data(retry['question'], None, usage)
        except Exception as error:  # noqa: BLE001 - the first answer is kept
            _logger.info("AI Chat Pro: the question %r asked again failed: %s", retry['question'], error)
            retried = None
        retried = retried and {key: value for key, value in retried.items() if key != 'escalate'}
        if retried and not self._has_failed(retried, usage):
            thoughts.append(self.env._("Asked instead: %(question)s → %(found)s", question=retry['question'],
                                       found=_short(retried.get('content'), 120)))
            return {**retried, 'thoughts': thoughts}
        for flag in ('no_data', 'name_missing', 'alternatives'):
            usage.pop(flag, None)
        usage.update(flags)
        return {**values, 'thoughts': thoughts} if thoughts else values

    @api.model
    def _is_fair_retry(self, retry, usage, request=''):
        """ Whether a question asked instead of a failed one still answers the request:
        it keeps the name no record bore (listing all the customers answers nothing
        about a customer that does not exist), and it names data of the user in full
        (not "companies" for "unicorn registrations"). """
        if missing := usage.get('name_missing'):
            if missing['text'].lower() not in retry['question'].lower():
                return False
        terms = retry.get('terms') or []
        if terms:
            candidates = self._find_candidates(_keywords(" ".join(terms)))
            if not candidates or candidates[0].get('unmatched'):
                return False
            # the data asked instead must be named by the request too ("companies" is no "unicorn registration")
            asked = _keywords(retry['question']) | _keywords(" ".join(terms))
            if not any(_similar(word, other) for word in asked for other in _keywords(request)):
                return False
        return True

    # ------------------------------------------------------------
    # AI
    # ------------------------------------------------------------

    @api.model
    def _ask_brain(self, prompt, usage):
        """ The decision of the brain for a prompt: ``{}`` when the AI can not answer. """
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage))
        except Exception as error:  # noqa: BLE001 - the agent answers without thinking
            _logger.info("AI Chat Pro: the brain could not think: %s", error)
            return {}
        return answer if isinstance(answer, dict) else {}
