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
from odoo.exceptions import AccessError, UserError
from odoo.tools import str2bool

from .ai_chat_creator import _loads_loosely

_logger = logging.getLogger(__name__)

# the data questions an analysis is answered from, and how much of each the AI reads
MAX_DEEP_QUESTIONS = 4
MAX_DEEP_ROWS = 15
MAX_DEEP_CELL = 60
# what the decision answer holds, at most
MAX_DEEP_ITEMS = {'findings': 5, 'recommendations': 5, 'risks': 4, 'next_steps': 4}
MAX_DEEP_TEXT = 500
# the rows of each dataset shown with the answer
MAX_SHOWN_ROWS = 10
CONFIDENCES = ('high', 'medium', 'low')


class AiChatAssistant(models.AbstractModel):
    """ Deep analysis: a question asking for a decision ("how can I increase the sales
    of this product", "which products should I forecast for next month") is answered
    from several sets of data, read as the user asking, and the AI writes a decision:
    a verdict, findings, recommendations, risks and next steps. The agent switches to
    it when the decision model is confident the question needs it, or when the user
    asks for it. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _is_deep_analysis_enabled(self):
        return str2bool(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.deep_analysis') or 'False', False)

    @api.model
    def _answer_deep(self, question, usage, steps=None, first=None):
        """ The deep analysis tool of the agent: the question is answered from several
        sets of data, each one read by the data tool as the user asking, then the AI
        writes a decision from them.

        :param list steps: the data questions the analysis needs, as the agent
            understood them (see ``_clean_step``); planned by the AI when not given
        :param dict first: the result the data tool already found for the question
            itself, when the agent switched to a deep analysis after it
        """
        steps = steps or self._plan_deep_analysis(question, usage)
        intent = self._get_intent()
        todo = [] if first is not None else [{**intent, 'question': intent.get('question') or question}]
        seen = {question.strip().lower()}
        for step in steps:
            if step['question'].strip().lower() not in seen:
                seen.add(step['question'].strip().lower())
                todo.append(step)
        todo = todo[:MAX_DEEP_QUESTIONS + (1 if first is None else 0)]
        questions = ([] if first is None else [question]) + [step['question'] for step in todo]
        datasets, errors = [], []
        if first is not None and (dataset := self._get_deep_dataset(question, first)):
            datasets.append(dataset)
        for step in todo:
            try:
                with self.env.cr.savepoint():
                    # each set of data is only read: no analysis of its own, no other analysis
                    result = self.with_context(ai_chat_intent=step, ai_chat_data_only=True)._answer_data(
                        step['question'], None, usage).get('result') or {}
            except (UserError, AccessError) as error:
                _logger.info("AI Chat Pro: no data for the analysis question %r: %s", step['question'], error)
                errors.append(error)
                continue
            if dataset := self._get_deep_dataset(step['question'], result):
                datasets.append(dataset)
        if not datasets and errors and len(errors) == len(todo):
            # nothing could be asked at all (no API key, no credit...): the reason, not "no data"
            raise errors[0]
        if not datasets:
            return {'content': self.env._(
                "I could not find data you can access to analyze this question. Try naming what it is about: "
                "the records, the people or the period to weigh."
            ), 'plan': {'kind': 'deep', 'questions': questions}}
        analysis = self._write_deep_analysis(question, datasets, usage)
        content = "\n\n".join(part for part in (analysis['verdict'], analysis['summary']) if part)
        return {
            'content': content or self.env._("The analysis is ready."),
            'result': {
                'type': 'analysis',
                **analysis,
                'datasets': [
                    {**dataset, 'rows': dataset['rows'][:MAX_SHOWN_ROWS]} for dataset in datasets
                ],
            },
            'plan': {'kind': 'deep', 'questions': questions},
            'source': 'deep',
        }

    @api.model
    def _plan_deep_analysis(self, question, usage):
        """ The questions on the data of the user that the analysis needs, written by the
        AI as a user would ask them, when the agent did not plan them already. """
        prompt = (
            "You prepare the analysis of a business question asked in Odoo, the business software. List the "
            f"questions on the data of the company that the analysis needs, at most {MAX_DEEP_QUESTIONS}, each "
            "one simple and answerable from Odoo records as a list, a total or a breakdown, written like a user "
            "would type them, e.g. \"sales amount per month of Office Chair this year\", \"top 10 customers of "
            "Office Chair\", \"quantity of Office Chair on hand\". Use the names the question uses. Never ask to "
            "create, change or delete anything.\n"
            "Reply with ONLY minified JSON, no text: "
            + '{"steps":[{"q":"<question>","terms":["<words naming the data>"],"limit":<count asked or null>,'
            '"names":[{"label":"<kind of record>","text":"<name>"}]}]}\n'
            f"Question: {question}"
        )
        try:
            answer = _loads_loosely(self._text_chat(prompt, usage)) or {}
        except UserError as error:
            _logger.info("AI Chat Pro: the analysis could not be planned: %s", error)
            answer = {}
        planned = answer.get('steps') if isinstance(answer, dict) else None
        steps = [self._clean_step(item) for item in planned if isinstance(item, (dict, str))] \
            if isinstance(planned, list) else []
        return [step for step in steps if step][:MAX_DEEP_QUESTIONS]

    @api.model
    def _get_deep_dataset(self, question, result):
        """ The data an answer found, as the AI reads it and the user sees it; ``None``
        when it found nothing. """
        if result.get('type') not in ('table', 'value') or not result.get('rows'):
            return None
        columns = [column['label'] for column in result.get('columns') or []]
        rows = [[str(cell)[:MAX_DEEP_CELL] for cell in row['cells']] for row in result['rows'][:MAX_DEEP_ROWS]]
        return {
            'question': question,
            'heading': result.get('heading') or result.get('title') or question,
            'tags': result.get('tags') or [],
            'columns': columns,
            'rows': rows,
            'total': result.get('total') or len(result['rows']),
        }

    @api.model
    def _write_deep_analysis(self, question, datasets, usage):
        """ The decision the AI writes from the data: ``{verdict, confidence, summary,
        findings, recommendations, risks, next_steps}``. """
        data = []
        for index, dataset in enumerate(datasets, start=1):
            title = " · ".join([dataset['heading'], *dataset['tags']])
            shown = len(dataset['rows'])
            more = f" (first {shown} of {dataset['total']})" if dataset['total'] > shown else ""
            data.append(f"Data {index}: {title}{more}\n" + " | ".join(dataset['columns']) + "\n"
                        + "\n".join(" | ".join(row) for row in dataset['rows']))
        prompt = (
            "You are a senior business analyst advising the manager of a company, from the data of their Odoo "
            "database below. Answer their question with a decision they can act on. Use only this data: never "
            "invent a figure, name or trend that it does not show, and say what is missing to decide better. "
            "When the question is about people (to dismiss, promote or rate an employee), only weigh measurable "
            "work results, never personal traits (gender, age, family, health, origin, religion), say that the data "
            "is not a complete picture of anyone's work, and advise a fair review with HR before any decision.\n"
            "Reply in the language of the question, with ONLY minified JSON, no text and no code block:\n"
            '{"verdict":"<the decision, one sentence>","confidence":"high|medium|low",'
            '"summary":"<2 to 3 sentences explaining the decision from the data>",'
            '"findings":["<a fact of the data that matters, with its figures>"],'
            '"recommendations":[{"action":"<what to do>","reason":"<why, from the data>",'
            '"impact":"<what to expect>"}],"risks":["<what could go wrong, or what the data cannot tell>"],'
            '"next_steps":["<a concrete step, with who or when if known>"]}\n'
            f"At most {MAX_DEEP_ITEMS['findings']} findings, {MAX_DEEP_ITEMS['recommendations']} recommendations, "
            f"{MAX_DEEP_ITEMS['risks']} risks and {MAX_DEEP_ITEMS['next_steps']} next steps.\n"
            f"Question: {question}\n\n" + "\n\n".join(data)
        )
        text = self._text_chat(prompt, usage)
        return _clean_analysis(_loads_loosely(text), text)


def _clean_text(value):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    return text[:MAX_DEEP_TEXT]


def _clean_analysis(answer, text):
    """ The decision written by the AI, with the expected parts only: a text that is no
    JSON becomes its summary. """
    if not isinstance(answer, dict):
        return {'verdict': '', 'confidence': 'low', 'summary': _clean_text(text), 'findings': [],
                'recommendations': [], 'risks': [], 'next_steps': []}

    def texts(name):
        items = answer.get(name)
        return [text for text in map(_clean_text, items if isinstance(items, list) else []) if text][:MAX_DEEP_ITEMS[name]]

    recommendations = []
    for item in answer.get('recommendations') if isinstance(answer.get('recommendations'), list) else []:
        if isinstance(item, dict) and (action := _clean_text(item.get('action'))):
            recommendations.append({
                'action': action, 'reason': _clean_text(item.get('reason')), 'impact': _clean_text(item.get('impact')),
            })
        elif isinstance(item, str) and (action := _clean_text(item)):
            recommendations.append({'action': action, 'reason': '', 'impact': ''})
    confidence = str(answer.get('confidence') or '').strip().lower()
    return {
        'verdict': _clean_text(answer.get('verdict')),
        'confidence': confidence if confidence in CONFIDENCES else 'medium',
        'summary': _clean_text(answer.get('summary')),
        'findings': texts('findings'),
        'recommendations': recommendations[:MAX_DEEP_ITEMS['recommendations']],
        'risks': texts('risks'),
        'next_steps': texts('next_steps'),
    }
