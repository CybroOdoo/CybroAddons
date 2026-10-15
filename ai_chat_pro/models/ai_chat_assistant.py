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

import difflib
import hashlib
import json
import logging
import math
import os
import re
import time as time_module
from collections import Counter
from datetime import date, datetime, time, timedelta

import pytz
import requests
from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain
from odoo.tools import ormcache, safe_eval as safe_eval_module, str2bool
from odoo.tools.misc import format_amount, format_date, format_datetime, formatLang
from odoo.tools.safe_eval import safe_eval

from odoo.addons.iap.tools import iap_tools

_logger = logging.getLogger(__name__)

DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'
DECISIONS_ENDPOINT = 'https://openrouter.ai/api/alpha/decisions'
OPENROUTER_CREDITS_ENDPOINT = 'https://openrouter.ai/api/v1/credits'
OPENROUTER_KEY_ENDPOINT = 'https://openrouter.ai/api/v1/key'
BALANCE_CACHE_SECONDS = 60
# balance read from OpenRouter, by database and key: (time read, balance)
_BALANCE_CACHE = {}
DEFAULT_AI_MODEL = '~typesafe/jev-latest'
DEFAULT_MAX_ROWS = 50

# models proposed to the AI when the question does not point clearly to one
MAX_CANDIDATES = 6
# a candidate scoring this many times more than the next one is picked without the AI
CLEAR_WINNER_RATIO = 1.5
# models a question may be about whose totals from linking data are proposed, and how many each
MAX_TOTAL_SUBJECTS = 3
MAX_TOTALS_PER_SUBJECT = 4
MAX_TOTAL_OPTIONS = 5
# data proposed to the AI when choosing what answers a question
MAX_DATA_OPTIONS = 9
# options proposed to the AI for each decision
MAX_SORT_OPTIONS = 12
MAX_MEASURE_OPTIONS = 10
MAX_GROUP_OPTIONS = 12
MAX_DATE_OPTIONS = 8
MAX_FILTER_QUESTIONS = 15
MAX_NAME_FIELDS = 8
# probability above which a yes/no decision is taken as yes
NOUL_THRESHOLD = 0.5
MAX_COLUMNS = 7
MAX_LIMIT = 500
# charts: types the web client draws, and the tables worth drawing
CHART_TYPES = ('bar', 'line', 'pie', 'doughnut')
MAX_CHART_ROWS = 50
MAX_CHART_SERIES = 3
# rows of data given to Odoo's AI service to analyze
MAX_REASONING_ROWS = 20
MAX_CELL_LENGTH = 120

# technical models, or models that are no business data
EXCLUDED_MODEL_PREFIXES = (
    'ir.', 'base.', 'base_', 'bus.', 'res.config', 'res.groups', 'res.users.', 'res.device', 'mail.', 'discuss.',
    'iap.', 'web_', 'web.', 'auth_', 'report.', 'digest.', 'ai.chat.', 'spreadsheet.', 'html_editor.', 'sms.',
)
SKIPPED_FIELD_TYPES = {
    'binary', 'image', 'html', 'json', 'properties', 'properties_definition', 'reference', 'many2one_reference',
}
SKIPPED_FIELD_PREFIXES = ('message_', 'activity_', 'website_message', 'access_', 'rating_', 'my_activity', 'has_message')
SKIPPED_FIELD_NAMES = {'id', 'create_uid', 'write_uid', 'write_date', 'display_name', '__last_update'}
NUMERIC_FIELD_TYPES = {'integer', 'float', 'monetary'}
GROUPABLE_FIELD_TYPES = {'many2one', 'selection', 'boolean', 'char', 'date', 'datetime', 'many2many'}
AGGREGATORS = {'sum', 'avg', 'min', 'max'}
GRANULARITIES = {'day', 'week', 'month', 'quarter', 'year'}

MODE_CRITERIA = {
    'list': "List or show matching records, e.g. 'list', 'show', 'which', 'top 10', 'latest'",
    'count': "Count how many records match, e.g. 'how many', 'number of'",
    'total': "One total, average, minimum or maximum of a value over all matching records, e.g. 'total amount', "
             "'how much', 'average'",
    'group': "Values broken down per category or per period, e.g. 'per customer', 'by month', 'for each', "
             "'breakdown', 'monthly'",
}
DIRECTION_CRITERIA = {
    'desc': "Highest, largest, most, latest or newest first (top, best, biggest, recent)",
    'asc': "Lowest, smallest, least, oldest or earliest first (bottom, worst, cheapest, first)",
}
AGGREGATOR_CRITERIA = {
    'sum': "Total, sum, how much",
    'avg': "Average, mean",
    'min': "Minimum, lowest, smallest",
    'max': "Maximum, highest, largest",
}
GRANULARITY_CRITERIA = {
    'day': "Per day, daily",
    'week': "Per week, weekly",
    'month': "Per month, monthly (default for periods)",
    'quarter': "Per quarter, quarterly",
    'year': "Per year, yearly",
}
# how much work an answer takes, decided by the decision model with the rest of the plan: the agent
# switches to a deep analysis only when it is confident enough (see ai_chat_agent)
DEPTH_CRITERIA = {
    'data': "Showing the data answers it: a list, a count, a total or a breakdown",
    'explain': "A short explanation, comparison or comment of this one set of data",
    'deep': "A decision, advice, a plan or a forecast that needs several sets of data (e.g. sales, stock and "
            "customers) to be weighed together",
}
DEPTH_QUESTION = {
    'type': 'choice',
    'instructions': "What does answering the question take, beyond reading this data?",
    'criteria': DEPTH_CRITERIA,
}
# date periods: (description, first day, last day), as placeholders resolved on each run
PERIODS = {
    'none': ("No date condition", None, None),
    'today': ("Today", '$today', '$today'),
    'yesterday': ("Yesterday", '$yesterday', '$yesterday'),
    'tomorrow': ("Tomorrow", '$tomorrow', '$tomorrow'),
    'this_week': ("This week", '$week_start', '$week_end'),
    'last_week': ("Last week, previous week", '$week_start-1w', '$week_end-1w'),
    'next_week': ("Next week", '$week_start+1w', '$week_end+1w'),
    'this_month': ("This month, current month", '$month_start', '$month_end'),
    'last_month': ("Last month, previous month", '$last_month_start', '$last_month_end'),
    'next_month': ("Next month", '$month_start+1m', '$month_end+1m'),
    'this_quarter': ("This quarter", '$quarter_start', '$quarter_end'),
    'last_quarter': ("Last quarter, previous quarter", '$quarter_start-3m', '$quarter_start-1d'),
    'this_year': ("This year, current year, year to date", '$year_start', '$year_end'),
    'last_year': ("Last year, previous year", '$last_year_start', '$last_year_end'),
    'last_7_days': ("Last 7 days, past week", '$today-6d', '$today'),
    'last_30_days': ("Last 30 days, past month", '$today-29d', '$today'),
    'next_7_days': ("Next 7 days, coming week", '$today', '$today+7d'),
    'next_30_days': ("Next 30 days, coming month", '$today', '$today+30d'),
    'past': ("Before today: overdue, late, expired, already past (not 'oldest' or 'first', which only sort)", None,
             '$yesterday'),
    'future': ("After today: upcoming, in the future (not 'newest' or 'latest', which only sort)", '$tomorrow', None),
}

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
PLACEHOLDER_RE = re.compile(
    r'^\$(today|yesterday|tomorrow|now|week_start|week_end|month_start|month_end|last_month_start|'
    r'last_month_end|quarter_start|quarter_end|year_start|year_end|last_year_start|last_year_end)'
    r'(?:([+-])(\d{1,4})([dwmy]))?$'
)
QUOTED_RE = re.compile(r'["“”«»]([^"“”«»]{2,60})["“”«»]')
STOPWORDS = frozenset("""
    a about above after all also am an and any are as at be been before below between both but by can could did
    do does doing done each few for from get give had has have having he her here hers him his how i if in into
    is it its just let list lists me more most my need no not now of off on only or other our ours out over own
    please same she should show so some such than that the their theirs them then there these they this those
    through to too top under until up very was we were what when where which while who whom whose why will with
    would you your yours find display tell want see know
""".split())


def _normalize(text):
    return ' '.join(re.findall(r'[^\W_]+|[<>=!]+|\d+', (text or '').lower()))


def _words(text):
    return re.findall(r'[^\W_]+', (text or '').lower())


def _stem(word):
    if len(word) > 4 and word.endswith('ies'):
        return word[:-3] + 'y'
    if len(word) > 3 and word.endswith('s') and not word.endswith('ss'):
        return word[:-1]
    return word


# names offered when a question names a record that does not exist
SIMILAR_NAMES = 3
# below this confidence of the AI choosing the data of a question, other readings are suggested
UNCERTAIN_CONFIDENCE = 0.75


def _keywords(text):
    """ Meaningful words of a text, roughly singularized. """
    return {
        _stem(word) for word in _words(text)
        if len(word) > 2 and word not in STOPWORDS and not word.isdigit()
    }


def _similar(keyword, word):
    """ Whether two keywords are the same word, also across forms (invoice, invoicing). """
    if keyword == word:
        return True
    length = min(len(keyword), len(word))
    if length < 4:
        return False
    common = len(os.path.commonprefix([keyword, word]))
    return common >= 4 and common >= length - 1


def _score(keywords, weighted_words):
    """ Sum, for each keyword, of the best weight of the words it matches. """
    return sum(
        max((weight for word, weight in weighted_words if _similar(keyword, word)), default=0)
        for keyword in keywords
    )


def _mentions(question_words, text):
    """ Whether a question uses one of the words of a text (also short ones, like "my"). """
    return any(
        _similar(_stem(q), _stem(w)) if len(w) > 3 else q == w
        for w in _words(text) for q in question_words
    )


class AiChatAssistant(models.AbstractModel):
    """ The engine of the AI assistant: the data tool of the agent (see ai_chat_agent,
    that understands each question with Odoo's AI service and chooses the tool).

    The AI model (TypeSafe Jev, through OpenRouter's Decisions API) is a decision
    model: it never writes queries nor sees any record, it only makes choices among
    options built here from what Odoo itself defines for the data:

    - the model a question is about, detected locally from the menus and models the
      user can access, and only asked to the AI when several match as well;
    - for that model, in a single request: what to show (a list, a count, a total or
      groups), the filters of its search view and of its menu that apply, the date
      field and period, the field to sort by, the value to total and how to group.

    The decisions are taken anew for each question, then turned into a query run by
    the ORM as the current user, so access rights, record
    rules and field groups always apply. Only questions that need an analysis send
    the (already accessible) result to Odoo's AI service (OLG), to write the answer.

    All the methods are private: the engine is only reachable through
    ``ai.chat.conversation.ask_question``.
    """
    _name = 'ai.chat.assistant'
    _description = "AI Chat Assistant"

    # ------------------------------------------------------------
    # Answer
    # ------------------------------------------------------------

    @api.model
    def _answer(self, question, previous_plan=None, deep=False, attachments=None):
        """ Values of the assistant message answering ``question``.

        :param bool deep: whether to answer with a deep analysis, a decision written from
            several sets of data
        """
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        try:
            # roll back any failed query, to still be able to save the answer
            with self.env.cr.savepoint():
                options = {'deep': True} if deep else {}
                if attachments:
                    # files sent with the question: read rather than analyzed
                    options = {'attachments': attachments}
                values = self._answer_question(question, previous_plan, usage, **options)
        except (UserError, AccessError) as error:
            values = {'content': str(error.args[0] if error.args else error), 'is_error': True}
        except Exception:
            _logger.exception("AI Chat Pro: could not answer %r", question)
            values = {
                'content': self.env._("Sorry, something went wrong while answering. Please rephrase your question."),
                'is_error': True,
            }
        return {
            **values,
            'source': values.get('source') or ('openrouter' if usage['ai_called'] else 'local'),
            'prompt_tokens': usage['prompt_tokens'],
            'completion_tokens': usage['completion_tokens'],
            'cost': usage['cost'],
            'suggestions': self._get_suggestions(question, values, usage) or False,
            'text_model': usage.get('text_model') or False,
            'used_olg': bool(usage.get('used_olg')),
            # the decision model is the only one called through the question's usage (writing
            # models count apart): shown with the answer when it was called
            'decision_model': (
                self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.model') or DEFAULT_AI_MODEL
            ) if usage['ai_called'] else False,
        }

    @api.model
    def _get_suggestions(self, question, values, usage):
        """ Questions the user may click instead of an answer the assistant is unsure of
        (see ai_chat_suggestions). """
        return []

    @api.model
    def _answer_question(self, question, previous_plan, usage, **kwargs):
        """ The answer to a question: the agent (see ai_chat_agent) chooses the tool
        answering it; without it, the question is read as a question on the data. """
        return self._answer_data(question, previous_plan, usage)

    @api.model
    def _get_intent(self):
        """ What the agent understood of the question being answered (see
        ai_chat_agent): ``{}`` when it was not understood by the AI. """
        return self.env.context.get('ai_chat_intent') or {}

    @api.model
    def _get_question_keywords(self, question, use_terms=True):
        """ The words a question names its data with: the terms the agent read in it,
        else the words of the question without the names of records it gives. """
        intent = self._get_intent()
        if use_terms and (terms := intent.get('terms')):
            return _keywords(" ".join(terms))
        for name in intent.get('names') or []:
            question = re.sub(re.escape(name['text']), ' ', question, flags=re.IGNORECASE)
        return _keywords(question)

    @api.model
    def _answer_data(self, question, previous_plan, usage):
        """ The data tool: the answer to a question on the data of the user, read as the
        user by a query the decision model plans. """
        intent = self._get_intent()
        question = intent.get('question') or question
        keywords = self._get_question_keywords(question)
        candidates = self._find_candidates(keywords)
        # accounting figures (profit, income, cash...) are computed, not records to list
        figure_candidate = self._get_figure_candidate(keywords)
        if not candidates and not figure_candidate and intent.get('terms'):
            # the terms the agent read match no data: the words of the question itself
            keywords = self._get_question_keywords(question, use_terms=False)
            candidates = self._find_candidates(keywords)
            figure_candidate = self._get_figure_candidate(keywords)
        previous_model = (previous_plan or {}).get('model')
        if previous_model and not self._is_allowed_model(previous_model):
            previous_model = None
        # a follow-up keeps the data of the previous question, unless the question names other data ("the
        # products of the second one", after sales orders)
        is_follow_up = bool(previous_model) and (
            (bool(intent.get('follow_up'))
             and (not candidates or previous_model in {candidate['model'] for candidate in candidates[:3]}))
            or (not candidates and not figure_candidate))
        if is_follow_up and not intent.get('question'):
            # the question was not written as a whole by the agent: it completes the previous one
            question = f"{previous_plan.get('question') or ''}, then: {question}"
        if is_follow_up and previous_plan.get('kind') == 'figure':
            candidate = {'figures': True}
        elif is_follow_up:
            candidate = {
                'model': previous_model,
                'label': previous_plan.get('source_label') or self.env[previous_model]._description,
                'path': previous_plan.get('menu_path') or '', 'domain': previous_plan.get('menu_domain') or '',
                'context': previous_plan.get('menu_context') or '',
                'search_view_id': previous_plan.get('search_view_id') or False,
                'link_field': previous_plan.get('link_field') or False,
                'subject_label': previous_plan.get('subject_label') or False,
            }
        elif candidates and not figure_candidate and self._names_other_records(candidates[0]):
            # the question names a record of other data ("the products of S00004"): the data asked, read
            # through the records linking both (see _link_to_anchors)
            candidate = candidates[0]
        elif candidates or figure_candidate:
            extra = [figure_candidate] if figure_candidate else []
            candidate = self._choose_candidate(question, candidates, usage, keywords, extra=extra)
        else:
            candidate = None
        if not candidate:
            # the user is offered questions to click instead (see _get_suggestions)
            usage['no_data'] = True
            examples = self._get_example_questions().get('others') or []
            content = self.env._("I could not find any data you can access that matches this question.")
            if examples:
                content += " " + self.env._("Try naming what you are looking for, e.g. %s.", ", ".join(
                    f"\"{example}\"" for example in examples))
            return {'content': content}

        if not candidate.get('figures') and not candidate.get('link_field'):
            # the records the question names of other data than the one asked ("products of S00006"): the
            # data linking them is answered instead (the lines of that order), in a follow-up too
            self, candidate = self._link_to_anchors(question, candidate, usage)  # noqa: PLW0642
        if candidate.get('figures'):
            plan = self._get_figure_plan(question, usage)
            result, content = self._run_figure(plan)
        else:
            plan = self._get_plan(question, candidate, usage)
            if missing := plan.get('name_missing'):
                # a record the question names that does not exist: said, rather than answered without it
                usage['name_missing'] = missing
                similar = missing['similar']
                return {'content': self.env._(
                    "I found no %(label)s named \"%(name)s\" in the records you can access.%(similar)s",
                    label=missing['label'], name=missing['text'],
                    similar=(" " + self.env._("Did you mean %s?", ", ".join(similar))) if similar else "",
                ), 'plan': plan}
            if unrelated := self._get_unrelated_records(plan):
                # a record the question names that the data can not be filtered on: said, rather than
                # answered with all the records
                usage['no_data'] = True
                return {'content': self.env._(
                    "I could not find how %(data)s relate to %(records)s, so I did not list them all. Try asking "
                    "about the records of %(records)s directly, e.g. its lines.",
                    data=candidate.get('label') or self.env[plan['model']]._description,
                    records=", ".join(f"{record['label']} {record['name']}" for record in unrelated),
                ), 'plan': plan}
            query = self._prepare_query(plan)
            result, content = self._run_query(query)
        if result.get('type') == 'table':
            result['chart'] = self._get_chart(question, result, usage)
        values = {'content': content, 'result': result, 'plan': plan}
        depth = self._choose_depth(plan, usage)
        if depth == 'deep':
            # the agent answers with a deep analysis, this data being its first set
            values['escalate'] = True
        elif depth == 'explain' and result.get('rows'):
            values.update(self._reason(question, result, content, usage))
        return values

    @api.model
    def _choose_depth(self, plan, usage):
        """ How much work the answer of a plan takes: ``'data'``, ``'explain'`` or
        ``'deep'`` (the agent decides, see ai_chat_agent). """
        return plan.get('depth') or ('explain' if plan.get('reasoning') else 'data')

    @api.model
    def _read_depth(self, answers):
        """ The depth the decision model chose for a question, and its confidence. """
        depth = self._get_choice(answers, 'depth', DEPTH_CRITERIA, 'data')
        confidence = (answers.get('depth') or {}).get('confidence')
        return depth, confidence if isinstance(confidence, (int, float)) else None

    # ------------------------------------------------------------
    # Model detection
    # ------------------------------------------------------------

    @api.model
    def _is_allowed_model(self, model_name):
        if not model_name or model_name not in self.env or model_name.startswith(EXCLUDED_MODEL_PREFIXES):
            return False
        Model = self.env[model_name]
        return not (Model._transient or Model._abstract) and Model.has_access('read')

    @api.model
    @ormcache('frozenset(self.env.user._get_group_ids())', 'self.env.lang')
    def _get_model_catalog(self):
        """ Business models the current user can read, with the words describing them:
        their name, and the menus opening them (that the user can see), with the default
        filter of these menus. Computed once per set of groups and language.

        Words are weighted by where they appear (the name of a menu weighs more than its
        parents), and by how rare they are: a word naming few models ("delivery") says
        more about the data asked for than a word naming many ("order").

        :return: tuple of ``(model, label, weighted words, menus)``, menus being tuples
            ``(menu path, action domain, action context, search view id, weighted words)``
        """
        Menu = self.env['ir.ui.menu']
        menus_by_model = {}
        for menu in Menu.sudo().browse(Menu._visible_menu_ids(debug=False)):
            if not (target := self._get_menu_window_action(menu)):
                continue
            model_name, action_name, domain, context, search_view_id = target
            path = menu.complete_name or menu.name
            parts = path.split('/')
            words = {}
            self._add_words(words, ' '.join(parts[:-1]), 1)
            self._add_words(words, action_name, 2)
            self._add_words(words, parts[-1], 3)
            menus_by_model.setdefault(model_name, []).append((path, domain, context, search_view_id, words))
        entries = []
        for model_name in self.env.registry:
            if not self._is_allowed_model(model_name):
                continue
            Model = self.env[model_name]
            words = {}
            self._add_words(words, model_name.replace('.', ' '), 1)
            self._add_words(words, Model._description, 2)
            # the kinds of records a model holds, named by its "type" fields: leads and opportunities,
            # customer invoices and vendor bills
            for field in Model._fields.values():
                if field.type == 'selection' and field.name.endswith('type') and not field.related:
                    try:
                        for _key, label in field._description_selection(self.env):
                            self._add_words(words, label, 1)
                    except Exception:  # noqa: BLE001 - a selection computed from a context
                        continue
            entries.append((model_name, Model._description or model_name, words, menus_by_model.get(model_name, [])))

        # how many models each word describes
        frequency = Counter()
        for _model_name, _label, words, menus in entries:
            frequency.update(set(words).union(*(menu[4] for menu in menus)))
        count = max(len(entries), 2)

        def weigh(words):
            # from 2 for a word naming a single model, to 1 for a word naming them all
            return tuple(
                (word, weight * (1 + math.log(count / frequency[word]) / math.log(count)))
                for word, weight in words.items()
            )

        return tuple(
            (model_name, label, weigh(words), tuple(menu[:4] + (weigh(menu[4]),) for menu in menus))
            for model_name, label, words, menus in entries
        )

    @api.model
    @ormcache('frozenset(self.env.user._get_group_ids())', 'self.env.lang')
    def _get_configuration_paths(self):
        """ The menus the user sees under a menu of configuration or settings of an app
        (those Odoo declares so), by their path. """
        data = self.env['ir.model.data'].sudo().search([
            ('model', '=', 'ir.ui.menu'), '|', ('name', 'ilike', 'config'), ('name', 'ilike', 'setting'),
        ])
        configuration = set(data.mapped('res_id'))
        Menu = self.env['ir.ui.menu']
        paths = set()
        for menu in Menu.sudo().browse(Menu._visible_menu_ids(debug=False)):
            ancestors = {int(part) for part in (menu.parent_path or '').split('/') if part}
            if ancestors & configuration:
                paths.add(menu.complete_name or menu.name)
        return frozenset(paths)

    @api.model
    def _is_configuration_model(self, model_name):
        """ Whether the records of a model are set up in the configuration of an app
        (taxes, units of measure, stages...): the user reaches them by no other menu. """
        paths = [menu[0] for entry in self._get_model_catalog() if entry[0] == model_name for menu in entry[3]]
        configuration = self._get_configuration_paths()
        return bool(paths) and all(path in configuration for path in paths)

    @api.model
    def _get_menu_window_action(self, menu):
        """ The model, name, domain, context and search view a menu opens, if any.

        Menus may open a server action returning a window action at run time (the
        deliveries of the inventory app): its code is never run, its model is the one
        the server action declares, and its filters those of the window action of that
        model bearing the name of the menu, when there is one.
        """
        action = menu.action
        if not action:
            return None
        if action._name == 'ir.actions.act_window':
            if not self._is_allowed_model(action.res_model):
                return None
            return (action.res_model, action.name, (action.domain or '').strip(), (action.context or '').strip(),
                    action.search_view_id.id)
        if action._name == 'ir.actions.server' and self._is_allowed_model(action.model_name):
            window = self.env['ir.actions.act_window'].sudo().search(
                [('res_model', '=', action.model_name), ('name', '=', menu.name)], limit=1,
            )
            if window:
                return (action.model_name, window.name, (window.domain or '').strip(),
                        (window.context or '').strip(), window.search_view_id.id)
            return action.model_name, menu.name, '', '', False
        return None

    @api.model
    def _add_words(self, words, text, weight):
        for word in _keywords(text):
            words[word] = max(words.get(word, 0), weight)

    @api.model
    def _find_candidates(self, keywords):
        """ Models matching the keywords of a question, best first. """
        if not keywords:
            return []
        candidates = []
        for model_name, label, model_words, menus in self._get_model_catalog():
            score = _score(keywords, model_words)
            best_menu, best_words = ('', '', '', False), model_words
            for path, domain, context, search_view_id, menu_words in menus:
                menu_score = _score(keywords, model_words + menu_words)
                if menu_score > score:
                    score, best_menu, best_words = menu_score, (path, domain, context, search_view_id), \
                        model_words + menu_words
            if not score:
                continue
            # favor models with menus, whose name matches exactly (Sales Order before Sales Order Line),
            # and documents before reports (SQL views)
            label_keywords = _keywords(label)
            precision = (
                len([w for w in label_keywords if any(_similar(k, w) for k in keywords)]) / len(label_keywords)
                if label_keywords else 0
            )
            score += 0.5 * precision + (0.5 if menus else 0) + (0.25 if self.env[model_name]._auto else 0)
            candidates.append({
                'model': model_name, 'label': label, 'score': score,
                'path': best_menu[0], 'domain': best_menu[1], 'context': best_menu[2],
                'search_view_id': best_menu[3],
                # what users call these records, to tell the AI what they are
                'menu_names': list(dict.fromkeys(menu[0].rpartition('/')[2] for menu in menus))[:5],
                'menu_count': len(menus),
                # the words of the question these records do not match ("manufacturing" of "manufacturing
                # orders", for sales orders)
                'unmatched': [keyword for keyword in keywords
                              if not any(_similar(keyword, word) for word, _weight in best_words)],
            })
        candidates.sort(key=lambda c: -c['score'])
        return candidates[:MAX_CANDIDATES]

    @api.model
    def _choose_candidate(self, question, candidates, usage, keywords=None, extra=()):
        """ The data the question is about: the clear winner, else the one the AI picks
        among the records themselves, the totals of records linking to them, and the
        ``extra`` answers (computed accounting figures). """
        if not candidates:
            if len(extra) == 1:
                return extra[0]
            options = list(extra)
        else:
            keywords = keywords or self._get_question_keywords(question)
            totals = self._get_total_candidates(candidates, keywords)
            # data matching only a part of the words the agent read for it ("manufacturing orders": sales orders)
            # may be other data, not installed: the decision model decides, "none" being one of its options
            partial = bool(self._get_intent().get('terms')) and bool(candidates[0].get('unmatched'))
            # the records the question names in full ("sale orders": Sales Order), when they are the only
            # ones and nothing is ranked by totals: they are listed, not a report or another model sharing
            # some of their words
            named = [
                c for c in candidates
                if c.get('path') and self.env[c['model']]._auto and (label_words := _keywords(c['label']))
                and all(any(_similar(keyword, word) for keyword in keywords) for word in label_words)
            ]
            # the most precise name wins: "contact tags" names Contact Tag, not Contact
            if named:
                longest = max(len(_keywords(c['label'])) for c in named)
                named = [c for c in named if len(_keywords(c['label'])) == longest]
            # ...unless they may be ranked by totals of data the question is also about ("which sales team
            # sold the most": teams ranked by their sales)
            close_models = {c['model'] for c in candidates if c['score'] * CLEAR_WINNER_RATIO > candidates[0]['score']}
            ranked = named and any(
                total.get('subject_model') == named[0]['model'] and total['model'] in close_models for total in totals)
            if len(named) == 1 and not ranked and not partial and (
                    not any(total.get('signal') for total in totals)
                    # "orders for customer X": the other words name a record to filter on, not data to rank
                    or self._get_explicit_names(question, self._get_model_options(
                        self.env[named[0]['model']], named[0].get('search_view_id'))['names'], named[0]['label'])):
                return named[0]
            best, second = candidates[0], candidates[1] if len(candidates) > 1 else None
            if (
                not second or best['score'] >= CLEAR_WINNER_RATIO * second['score']
                # a model the user reaches by a matching menu, before a model without menu
                or (best['path'] and not second['path'] and best['score'] >= second['score'] + 1)
            ) and not any(total.get('signal') for total in totals) and not extra and not partial:
                return best
            # only the candidates that are close to the best one are worth the tokens
            close = [c for c in candidates if c['score'] * CLEAR_WINNER_RATIO > best['score']]
            # the extra answers are kept within the options limit
            options = close[:MAX_DATA_OPTIONS - len(extra)] + list(extra)
            options += totals[:MAX_DATA_OPTIONS - len(options)]
        criteria = {f"option_{index}": self._describe_candidate(c) for index, c in enumerate(options)}
        # the data a question is about may not be in this database (an app not installed)
        criteria['none'] = "None of these: the question is about other data than all the options above"
        answers = self._decide(question, {
            'data': {
                'type': 'choice',
                'instructions': "Which data of the Odoo business software answers this question? Match what the "
                                "question names with the menus of each option. When the question ranks or "
                                "totals records by a value they do not hold themselves (quantities sold, amounts "
                                "invoiced, number of orders...), pick the option that totals them from the records "
                                "linking to them.",
                'criteria': criteria,
            },
        }, usage)
        index = self._get_choice(answers, 'data', criteria, 'option_0')
        if index == 'none':
            return None
        chosen = options[int(index.removeprefix('option_'))]
        confidence = (answers.get('data') or {}).get('confidence')
        if isinstance(confidence, (int, float)) and confidence < UNCERTAIN_CONFIDENCE:
            # an uncertain choice: the other readings are offered to the user as questions to click
            usage['chosen'] = self._describe_candidate(chosen)
            usage['alternatives'] = [self._describe_candidate(c) for c in options if c is not chosen][:3]
        return chosen

    @api.model
    def _names_other_records(self, candidate):
        """ Whether the question names records of other data than ``candidate`` (see
        ai_chat_mentions). """
        return False

    @api.model
    def _get_unrelated_records(self, plan):
        """ The records the question names that the plan does not filter on (see
        ai_chat_mentions). """
        return []

    @api.model
    def _link_to_anchors(self, question, candidate, usage):
        """ The assistant and the data answering a question about ``candidate`` that
        names records of other data (see ai_chat_mentions). """
        return self, candidate

    @api.model
    def _describe_candidate(self, candidate):
        if candidate.get('figures'):
            return (
                "Accounting figures computed from the posted journal items for a period, as in financial "
                "reports (profit and loss, balance sheet): " + ", ".join(candidate['examples'])
            )
        menu = f" (menu {candidate['path']})" if candidate.get('path') else ''
        if not candidate.get('link_field'):
            menus = candidate.get('menu_names') or []
            known_as = f", known as: {', '.join(menus)}" if menus else ''
            return (f"{candidate['label']} [{candidate['model']}] records themselves{menu}{known_as}: "
                    "list, count or sort them by their own fields")
        return (
            f"{candidate['subject_label']} ranked or totaled from {candidate['label']}{menu}, "
            f"one line per {candidate['link_label']}: {', '.join(candidate['measures'])}"
        )

    @api.model
    @ormcache('frozenset(self.env.user._get_group_ids())')
    def _get_inbound_links(self):
        """ The stored many2one fields linking business models to each model, as the
        current user can read them: ``{model: ((linking model, field), ...)}``. """
        links = {}
        for model_name in self.env.registry:
            if not self._is_allowed_model(model_name):
                continue
            Model = self.env[model_name]
            for field in Model._fields.values():
                if field.type == 'many2one' and field.comodel_name != model_name \
                        and self._is_usable_field(Model, field):
                    links.setdefault(field.comodel_name, []).append((model_name, field.name))
        return {model_name: tuple(model_links) for model_name, model_links in links.items()}

    @api.model
    def _get_model_family(self, model_name):
        """ A model with the models it is stored with (``_inherits``): a product
        template and its variants are linked to as the same thing. """
        family = {model_name, *self.env[model_name]._inherits}
        family.update(name for name in self.env.registry if model_name in self.env[name]._inherits)
        return family

    @api.model
    def _get_total_candidates(self, candidates, keywords):
        """ For the models a question may be about, the data that can total them: the
        business models linking to them by a many2one, that users reach by a menu and
        that hold values to total. E.g. products are totaled from sales, invoices or
        purchases lines, customers from invoices, salespeople from orders. """
        catalog = {entry[0]: entry for entry in self._get_model_catalog()}
        links = self._get_inbound_links()
        totals = []
        # only the models close to the best match: the others would only add noise
        subjects = [c for c in candidates if c['score'] * CLEAR_WINNER_RATIO > candidates[0]['score']]
        for subject in subjects[:MAX_TOTAL_SUBJECTS]:
            family = self._get_model_family(subject['model'])
            # the words naming the subject itself ("contacts", "partner") do not ask for a total
            subject_words = catalog.get(subject['model'], (None, None, (), ()))[2] + tuple(
                (word, 1) for word in _keywords(subject['label'])
            )
            other_keywords = {
                keyword for keyword in keywords if not any(_similar(keyword, word) for word, _w in subject_words)
            }
            if subject['model'] != candidates[0]['model']:
                # another subject than the records the question is about is only ranked when the question
                # names it by its own words: "top sale orders by revenue" lists sales orders, it does not
                # rank the sales teams, whose menus also say "sales"
                best_words = catalog.get(candidates[0]['model'], (None, None, (), ()))[2] + tuple(
                    (word, 1) for word in _keywords(candidates[0]['label']))
                own_words = [word for word, _weight in subject_words
                             if not any(_similar(word, best) for best, _w in best_words)]
                if not any(_similar(keyword, word) for keyword in keywords for word in own_words):
                    continue
            fact_links = {}
            for target in sorted(family, key=lambda name: name != subject['model']):
                for fact_name, field_name in links.get(target, ()):
                    if fact_name in family or fact_name not in catalog:
                        continue
                    # the link the question names (customer, salesperson...), else the first
                    # link to the model itself, else to its family
                    link_label = self.env[fact_name]._fields[field_name]._description_string(self.env)
                    link_score = _score(keywords, [(word, 1) for word in _keywords(link_label)])
                    if fact_name not in fact_links or link_score > fact_links[fact_name][1]:
                        fact_links[fact_name] = (field_name, link_score)
            subject_totals = []
            for fact_name, (field_name, link_score) in fact_links.items():
                _name, label, model_words, menus = catalog[fact_name]
                Fact = self.env[fact_name]
                if not menus:
                    continue

                measures = self._get_total_measures(Fact)
                if not measures:
                    continue
                measure_words = tuple((word, 2) for measure in measures.values() for word in _keywords(measure))
                path, domain, _context, search_view_id, menu_words = max(
                    menus, key=lambda menu: _score(keywords, model_words + menu[4]),
                )
                # the link counts too: purchases total vendors through their "Vendor" field
                score = _score(keywords, model_words + menu_words + measure_words) + 2 * link_score
                # reports are made to total data
                rank = score + (0.5 if not Fact._auto else 0)
                subject_totals.append((rank, {
                    'model': fact_name,
                    'label': label,
                    'score': score,
                    # whether the question names something of this data besides the subject:
                    # a value, the data itself... only then the AI is asked to choose
                    'signal': _score(other_keywords, model_words + menu_words + measure_words)
                    # "sold the most", "bought", "spent": a ranking by what other records total, as the
                    # agent read it
                    + (1 if self._get_intent().get('ranks_by_total') else 0),
                    'path': path,
                    'domain': domain,
                    # the default filters of the menu are asked, not applied: a total over all time
                    # must not be limited to the last year that a report menu shows by default
                    'context': '',
                    'search_view_id': search_view_id,
                    'link_field': field_name,
                    'link_label': Fact._fields[field_name]._description_string(self.env),
                    'subject_label': subject['label'],
                    'subject_model': subject['model'],
                    'measures': list(measures.values())[:4],
                }))
            subject_totals.sort(key=lambda item: -item[0])
            totals += subject_totals[:MAX_TOTALS_PER_SUBJECT]
        # the best totals over all the models, as the options are limited
        totals.sort(key=lambda item: -item[0])
        return [total for _rank, total in totals[:MAX_TOTAL_OPTIONS]]

    # ------------------------------------------------------------
    # Options: what Odoo defines for a model, as the user sees it
    # ------------------------------------------------------------

    @api.model
    def _get_model_options(self, Model, search_view_id=False):
        """ The options the decisions about a model are taken among: the filters, date
        fields, group bys and searchable fields of its search view (the one of the menu
        the question matched), and its fields to sort by and to total. Labels are the
        ones users see. """
        views = Model.get_views([(False, 'list'), (search_view_id or False, 'search')])['views']
        list_arch = etree.fromstring(views['list']['arch'])
        search_arch = etree.fromstring(views['search']['arch'])
        list_fields = [node.get('name') for node in list_arch.iter('field')]
        options = {'filters': {}, 'dates': {}, 'group_bys': {}, 'names': {}, 'sorts': {}, 'measures': {}}
        options['filters'] = {
            name: search_filter['label']
            for name, search_filter in self._get_search_filters(Model, search_view_id).items()
            if not search_filter['hidden']
        }

        def usable(name):
            field = Model._fields.get(name)
            return field if field and self._is_usable_field(Model, field) else None

        def label(field, node=None):
            return (node is not None and (node.get('string') or node.get('help'))) or \
                field._description_string(self.env)

        for node in search_arch.iter('filter'):
            if node.get('date'):
                if field := usable(node.get('date')):
                    options['dates'][field.name] = label(field, node)
            elif (context := node.get('context')) and 'group_by' in context:
                match = re.search(r"""['"]group_by['"]\s*:\s*['"]([\w.:]+)['"]""", context)
                field = match and usable(match.group(1).partition(':')[0])
                if field and field.type not in ('date', 'datetime'):
                    options['group_bys'][field.name] = label(field, node)
        for node in search_arch.iter('field'):
            field = usable(node.get('name'))
            if field and field.type in ('many2one', 'char') and len(options['names']) < MAX_NAME_FIELDS:
                options['names'][field.name] = label(field, node)

        # fields of the list view first: they are the ones that matter to users
        names = list(dict.fromkeys(list_fields + list(Model._fields)))
        for name in names:
            field = usable(name)
            if not field:
                continue
            in_views = name in list_fields or name in options['names'] or name in options['dates']
            if field.type in ('date', 'datetime') and len(options['dates']) < MAX_DATE_OPTIONS:
                options['dates'].setdefault(name, label(field))
            # amounts, and the values users see in the views, are the ones worth totaling and sorting by
            if not (in_views or field.type == 'monetary'):
                continue
            if field.type in NUMERIC_FIELD_TYPES and len(options['measures']) < MAX_MEASURE_OPTIONS:
                options['measures'][name] = label(field)
            if (field.type in NUMERIC_FIELD_TYPES | {'date', 'datetime'} or name == Model._rec_name) \
                    and len(options['sorts']) < MAX_SORT_OPTIONS:
                options['sorts'][name] = label(field)
            if field.type in GROUPABLE_FIELD_TYPES - {'char', 'date', 'datetime'} and in_views \
                    and field._description_groupable(self.env) and len(options['group_bys']) < MAX_GROUP_OPTIONS:
                options['group_bys'].setdefault(name, label(field))
        # dates are grouped per period
        options['group_bys'].update({
            f"{name}:date": self.env._("%s (per period)", date_label) for name, date_label in options['dates'].items()
        })
        return options

    @api.model
    def _is_usable_field(self, Model, field):
        """ Whether a field can be used in a query, by the current user. """
        if (
            field.name in SKIPPED_FIELD_NAMES or field.name.startswith(SKIPPED_FIELD_PREFIXES)
            or field.type in SKIPPED_FIELD_TYPES or not field.store
            or not Model._has_field_access(field, 'read')
        ):
            return False
        return not field.relational or self.env[field.comodel_name].has_access('read')

    @api.model
    def _get_search_filters(self, Model, search_view_id=False):
        """ The filters with a domain of a search view, by name, with their label and
        group: like in the web client, the filters of a group (between separators) are
        combined with OR, and the groups with AND. """
        arch = etree.fromstring(Model.get_views([(search_view_id or False, 'search')])['views']['search']['arch'])
        filters, group = {}, 0
        for node in arch.iter():
            if node.tag == 'filter' and node.get('name') and node.get('domain') and not node.get('date'):
                filters[node.get('name')] = {
                    'domain': node.get('domain'),
                    'label': node.get('string') or node.get('help') or node.get('name'),
                    'group': group,
                    'hidden': node.get('invisible') in ('1', 'True'),
                }
            else:
                group += 1
        return filters

    @api.model
    def _get_default_filters(self, Model, context, search_filters):
        """ The filters a menu applies by default (``search_default_*`` of its action),
        like the web client does. Filters on the current user ("My Orders") are only a
        convenience of the menu: they are applied when the question asks for them. """
        if not context:
            return []
        try:
            values = safe_eval(context, self._get_eval_context())
        except Exception as error:  # noqa: BLE001 a context depending on the web client
            _logger.info("AI Chat Pro: menu context of %s ignored: %s", Model._name, error)
            return []
        return [
            name.removeprefix('search_default_') for name, value in (values or {}).items()
            if name.startswith('search_default_') and value
            and (search_filter := search_filters.get(name.removeprefix('search_default_')))
            and not re.search(r'\b(uid|user)\b', search_filter['domain'])
        ]

    @api.model
    def _get_eval_context(self):
        """ Values available to the domains and contexts written in views and actions. """
        today = fields.Date.context_today(self)
        return {
            'uid': self.env.uid,
            'user': self.env.user,
            'context': dict(self.env.context),
            'allowed_company_ids': self.env.companies.ids,
            'company_id': self.env.company.id,
            'company_ids': self.env.companies.ids,
            'context_today': lambda: today,
            'current_date': fields.Date.to_string(today),
            'today': fields.Date.to_string(today),
            'datetime': safe_eval_module.datetime,
            'time': safe_eval_module.time,
            'relativedelta': safe_eval_module.dateutil.relativedelta.relativedelta,
            'True': True, 'False': False, 'None': None,
        }

    @api.model
    def _eval_domain(self, Model, domain):
        """ Evaluate a domain written in a view or an action, like the web client does. """
        if not domain:
            return Domain.TRUE
        if isinstance(domain, str):
            domain = safe_eval(domain, self._get_eval_context())
        domain = Domain(domain)
        domain.validate(Model)
        return domain

    # ------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------

    @api.model
    def _get_plan(self, question, candidate, usage):
        """ The decisions of the AI about a question on a model. """
        model_name = candidate['model']
        Model = self.env[model_name]
        search_view_id = candidate.get('search_view_id') or False
        options = self._get_model_options(Model, search_view_id)
        question_words = set(_words(question))
        # the filters of the search view, except those the menu applies anyway; those the
        # question mentions first, as a model may have dozens of them
        default_filters = self._get_default_filters(
            Model, candidate.get('context'), self._get_search_filters(Model, search_view_id),
        )
        filters = {name: label for name, label in options['filters'].items() if name not in default_filters}
        filters = dict(sorted(filters.items(), key=lambda item: not _mentions(question_words, item[1])))
        filters = dict(list(filters.items())[:MAX_FILTER_QUESTIONS])
        link_field = candidate.get('link_field') or False
        if link_field:
            # one line per linked record: only the value to total remains to decide
            options.update(measures=self._get_total_measures(Model, question_words), group_bys={}, sorts={})
        questions = self._build_questions(options, filters, ranked=bool(link_field))
        if link_field:
            questions.pop('mode', None)

        if link_field:
            link_label = Model._fields[link_field]._description_string(self.env)
            state = (f"Question about {candidate['subject_label']}, totaled from {candidate['label']} records, "
                     f"one line per {link_label}")
        else:
            state = f"Question about {candidate['label']} records"
        if candidate.get('path'):
            state += f" (menu {candidate['path']})"
        answers = self._decide(f"{state}: {question}", questions, usage)

        mode = 'group' if link_field else self._get_choice(answers, 'mode', MODE_CRITERIA, 'list')
        depth, depth_confidence = self._read_depth(answers)
        plan = {
            'question': question,
            'model': model_name,
            'menu_path': candidate.get('path') or '',
            'menu_domain': candidate.get('domain') or '',
            'menu_context': candidate.get('context') or '',
            'search_view_id': search_view_id,
            'mode': mode,
            'filters': [name for name in filters if self._get_noul(answers, f"filter_{name}")],
            'date_field': self._get_choice(answers, 'date_field', options['dates'], 'none'),
            'period': self._get_choice(answers, 'period', PERIODS, 'none'),
            'sort': self._get_choice(answers, 'sort', options['sorts'], 'none'),
            'direction': self._get_choice(answers, 'direction', DIRECTION_CRITERIA, 'desc'),
            'measure': self._get_choice(answers, 'measure', options['measures'], 'none'),
            'aggregator': self._get_choice(answers, 'aggregator', AGGREGATOR_CRITERIA, 'sum'),
            'group_by': self._get_choice(answers, 'group_by', options['group_bys'], 'none'),
            'granularity': self._get_choice(answers, 'granularity', GRANULARITY_CRITERIA, 'month'),
            'limit': self._extract_limit(question),
            'depth': depth,
            'depth_confidence': depth_confidence,
            'name_field': False,
            'name_text': False,
            'link_field': link_field,
            'subject_label': link_field and candidate.get('subject_label'),
            'source_label': link_field and candidate.get('label'),
        }
        if link_field:
            plan['group_by'] = link_field
        if plan['mode'] == 'group' and plan['group_by'] == 'none':
            # a breakdown without a grouping: per period of the date, else one total
            if plan['date_field'] != 'none':
                plan['group_by'] = f"{plan['date_field']}:date"
            else:
                plan['mode'] = 'total'
        # whether the question names a record, and in which field: the name itself is looked for in the data
        plan['names_record'] = self._get_noul(answers, 'names_record')
        plan['name_choice'] = self._get_choice(answers, 'name_field', options['names'], False)
        # check the plan, as the user asking
        self._prepare_query(plan)
        return self._resolve_named_record(Model, question, plan, options, candidate)

    @api.model
    def _get_total_measures(self, Model, question_words=()):
        """ The values of a model worth totaling: those Odoo shows as measures in its
        pivot, graph and list views, then its amounts; those the question names first. """
        views = Model.get_views([(False, 'pivot'), (False, 'graph'), (False, 'list')])['views']
        in_views = []
        for view_type in ('pivot', 'graph', 'list'):
            in_views += [node.get('name') for node in etree.fromstring(views[view_type]['arch']).iter('field')]
        measures = {}
        for name in dict.fromkeys(in_views + list(Model._fields)):
            field = Model._fields.get(name)
            if (
                field and field.type in NUMERIC_FIELD_TYPES and field.aggregator in AGGREGATORS
                and (name in in_views or field.type == 'monetary') and self._is_usable_field(Model, field)
            ):
                measures[name] = field._description_string(self.env)
        ordered = sorted(measures.items(), key=lambda item: not _mentions(question_words, f"{item[0]} {item[1]}"))
        return dict(ordered[:MAX_MEASURE_OPTIONS])

    @api.model
    def _build_questions(self, options, filters, ranked=False):
        """ The decisions asked to the AI, in a single request.

        :param bool ranked: whether the answer ranks records by a total or a count of the
            records linking to them ("least selling products")
        """
        def with_none(choices, none_label):
            return {'none': none_label, **choices}

        questions = {
            'mode': {
                'type': 'choice',
                'instructions': "What kind of answer does the question ask for?",
                'criteria': MODE_CRITERIA,
            },
            'depth': DEPTH_QUESTION,
        }
        if options['dates']:
            questions['date_field'] = {
                'type': 'choice',
                'instructions': "Which date must the records be filtered on? 'none' if no period is mentioned.",
                'criteria': with_none(options['dates'], "No date condition in the question"),
            }
            questions['period'] = {
                'type': 'choice',
                'instructions': "Which period must that date be in?",
                'criteria': {key: description for key, (description, _start, _end) in PERIODS.items()},
            }
        if options['sorts']:
            questions['sort'] = {
                'type': 'choice',
                'instructions': "Which value must the records be sorted by? 'none' if no ranking is asked.",
                'criteria': with_none(options['sorts'], "No particular order"),
            }
        if options['sorts'] or ranked:
            # totals are ranked too: "least selling products" are the lowest totals first
            questions['direction'] = {
                'type': 'choice',
                'instructions': "In which order?",
                'criteria': DIRECTION_CRITERIA,
            }
        if options['measures']:
            questions['measure'] = {
                'type': 'choice',
                'instructions': "Which value must be totaled or compared? 'none' to count records.",
                'criteria': with_none(options['measures'], "Number of records"),
            }
            questions['aggregator'] = {
                'type': 'choice',
                'instructions': "How must that value be aggregated?",
                'criteria': AGGREGATOR_CRITERIA,
            }
        if options['group_bys']:
            questions['group_by'] = {
                'type': 'choice',
                'instructions': "Per what must the results be broken down? 'none' if not asked.",
                'criteria': with_none(options['group_bys'], "No breakdown"),
            }
            questions['granularity'] = {
                'type': 'choice',
                'instructions': "If broken down per period, which period?",
                'criteria': GRANULARITY_CRITERIA,
            }
        if options['names']:
            questions['names_record'] = {
                'type': 'noul',
                'instructions': "Does the question restrict the results to one named " +
                                ", ".join(options['names'].values()) + "?",
                'criteria': {
                    'true': "Names a specific one, e.g. a given customer, vendor, product or person",
                    'false': "Names none, or only uses generic words",
                },
            }
            questions['name_field'] = {
                'type': 'choice',
                'instructions': "If so, what is named?",
                'criteria': options['names'],
            }
        for name, label in filters.items():
            questions[f"filter_{name}"] = {
                'type': 'noul',
                'instructions': f"Does the question ask only for records that are '{label}'?",
                'criteria': {'true': f"Asks for '{label}' records", 'false': f"Does not restrict to '{label}'"},
            }
        return questions

    @api.model
    def _get_choice(self, answers, name, options, default):
        choice = (answers.get(name) or {}).get('choice')
        return choice if choice in options else default

    @api.model
    def _get_noul(self, answers, name):
        return ((answers.get(name) or {}).get('noul') or 0.0) > NOUL_THRESHOLD

    @api.model
    def _extract_limit(self, question):
        """ The number of records a question ranks ("top 10", "5 biggest", "top selling
        five"), as the agent read it. """
        limit = self._get_intent().get('limit')
        return min(limit, MAX_LIMIT) if isinstance(limit, int) and limit > 0 else False

    @api.model
    def _resolve_named_record(self, Model, question, plan, options, candidate=None):
        """ The plan, restricted to the record the question names ("orders of customer
        Azure Interior"): the names are the ones the agent read in the question (or
        quoted), looked for in the field they name. A name no record bears is said, with
        the names that come close, rather than ignored. """
        plan = {key: value for key, value in plan.items() if key not in ('name_field', 'name_text', 'name_missing')}
        names = options['names']
        field_name = plan.get('name_choice') if plan.get('names_record') and plan.get('name_choice') in names else False
        explicit = self._get_explicit_names(
            question, names, " ".join([(candidate or {}).get('label') or '', Model._description]))
        if not field_name and explicit:
            # the AI did not say, or the plan is older: the field the name was given for
            field_name = explicit[0][0] or next(iter(names))
        if not field_name:
            return plan
        field = Model._fields[field_name]
        texts = [(name or field_name, text) for name, text in explicit]
        if not texts and plan.get('names_record') and self._get_intent().get('routed'):
            # the decision model says the question names a record, the agent read no name: the words of the
            # question that name no data ("Gemini Furniture" in "the sales orders of Gemini Furniture")
            texts = [(field_name, text) for text in self._get_residual_texts(question)]
        missing = None
        # the most precise name first: in a follow-up, "Zeta Partner A" rather than "Zeta Partner". The name is
        # looked for in the field it was read for, then in the other fields naming records: the AI may have
        # taken a customer for an order ("orders of Azure Interior")
        for own_field, text in sorted(texts, key=lambda item: -len(item[1])):
            text = text.strip()[:60]
            if len(text) < 2:
                continue
            for name_field in dict.fromkeys([own_field, field_name, *names]):
                if self._name_exists(Model, name_field, text):
                    return {**plan, 'name_field': name_field, 'name_text': text}
            missing = missing or text
        if missing:
            plan['name_missing'] = {
                'text': missing, 'field': field_name, 'label': names[field_name],
                'similar': self._get_similar_names(Model, field, missing),
            }
        return plan

    @api.model
    def _get_residual_texts(self, question):
        """ The runs of words of a question that name no data (not the terms the agent
        read, nor common words): what may name a record. """
        intent = self._get_intent()
        known = set()
        for term in intent.get('terms') or []:
            known |= {_stem(word) for word in _words(term)}
        runs, run = [], []
        for word in question.split():
            clean = word.strip('?!.,;:()[]"\'')
            stem = _stem(clean.lower())
            if clean and stem not in known and clean.lower() not in STOPWORDS and not clean.isdigit():
                run.append(clean)
            else:
                if run:
                    runs.append(' '.join(run))
                run = []
        if run:
            runs.append(' '.join(run))
        # a run, then its last words ("named Azure": "Azure"), the longest texts first
        texts = [' '.join(words[start:]) for run in runs for words in [run.split()] for start in range(len(words))]
        return sorted(dict.fromkeys(texts), key=len, reverse=True)

    @api.model
    def _name_exists(self, Model, field_name, text):
        """ Whether a record the user can read bears a name, in a field naming records. """
        field = Model._fields.get(field_name)
        if not field or not self._is_usable_field(Model, field):
            return False
        try:
            if field.type == 'many2one':
                return bool(self.env[field.comodel_name].name_search(text, limit=1))
            return bool(Model.search_count([(field_name, 'ilike', text)], limit=1))
        except (AccessError, UserError, ValueError):
            return False

    @api.model
    def _get_explicit_names(self, question, names, label=''):
        """ The names of records a question gives, as the agent read them ("Azure
        Interior" for "customer"), or quoted: ``[(field name or None, text)]``, the field
        being the one of ``names`` whose label is the kind the agent gave. A name of
        another kind of record than the data asked (``label``) and than its fields
        ("S00006" of a sales order, when products are asked) is left out: it names
        records linked to the data, not the data itself (see ai_chat_mentions). """
        found = []
        own_kind = _keywords(label)
        for name in self._get_intent().get('names') or []:
            kind = _keywords(name.get('label') or '')
            field_name = next((
                field_name for field_name, field_label in names.items()
                if kind and any(_similar(word, other) for word in kind for other in _keywords(field_label))
            ), None)
            if field_name is None and kind and own_kind and not any(
                    _similar(word, other) for word in kind for other in own_kind):
                continue
            found.append((field_name, name['text']))
        found += [(None, text) for text in QUOTED_RE.findall(question or '')
                  if text not in [known for _field, known in found]]
        if not names:
            return []
        return [(field_name, str(text).strip()[:60]) for field_name, text in found if str(text).strip()]

    @api.model
    def _get_similar_names(self, Model, field, text):
        """ The names of the records close to a name no record bears: "Sayuj" for
        "sayooj". """
        Comodel = self.env[field.comodel_name] if field.type == 'many2one' else Model
        try:
            if field.type == 'many2one':
                names = [name for _id, name in Comodel.name_search(text[:3], limit=60)]
            else:
                names = Model.search([(field.name, 'ilike', text[:3])], limit=60).mapped(field.name)
        except (AccessError, UserError, ValueError):
            return []
        lowered = {str(name).lower(): str(name) for name in names if name}
        close = difflib.get_close_matches(text.lower(), list(lowered), n=SIMILAR_NAMES, cutoff=0.6)
        return [lowered[name] for name in close]

    # ------------------------------------------------------------
    # Query
    # ------------------------------------------------------------

    def _invalid(self, reason):
        _logger.info("AI Chat Pro: invalid query plan: %s", reason)
        return UserError(self.env._(
            "The assistant could not build a valid query for this question (%(reason)s). Please rephrase it.",
            reason=reason,
        ))

    @api.model
    def _prepare_query(self, plan):
        """ Turn decisions into a query, checked against the access of the current user:
        anything the user may not read is rejected. """
        model_name = plan.get('model')
        if not self._is_allowed_model(model_name):
            raise self._invalid(self.env._("unknown data %s", model_name))
        Model = self.env[model_name]
        Model.check_access('read')
        max_rows = int(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.max_rows') or 0) or DEFAULT_MAX_ROWS

        def usable(name, types=None):
            field = Model._fields.get(name) if name and name != 'none' else None
            ok = field and self._is_usable_field(Model, field) and (not types or field.type in types)
            return field if ok else None

        domains = []
        title_parts = [plan.get('menu_path', '').rpartition('/')[2] or Model._description]
        try:
            domains.append(self._eval_domain(Model, plan.get('menu_domain')))
        except Exception as error:  # noqa: BLE001 a menu domain depending on a context
            _logger.info("AI Chat Pro: menu domain of %s ignored: %s", model_name, error)
        search_filters = self._get_search_filters(Model, plan.get('search_view_id'))
        default_filters = self._get_default_filters(Model, plan.get('menu_context'), search_filters)
        filter_groups = {}
        for name in dict.fromkeys([*default_filters, *(plan.get('filters') or [])]):
            if not (search_filter := search_filters.get(name)):
                continue
            try:
                filter_domain = self._eval_domain(Model, search_filter['domain'])
            except Exception as error:  # noqa: BLE001 a filter depending on a context
                _logger.info("AI Chat Pro: filter %s of %s ignored: %s", name, model_name, error)
                continue
            filter_groups.setdefault(search_filter['group'], []).append(filter_domain)
            title_parts.append(search_filter['label'])
        domains += [Domain.OR(group_domains) for group_domains in filter_groups.values()]

        period = PERIODS.get(plan.get('period'))
        date_field = usable(plan.get('date_field'), ('date', 'datetime'))
        if date_field and period and plan['period'] != 'none':
            _description, start, end = period
            if start:
                domains.append(Domain(self._make_leaf(date_field.name, '>=', self._resolve_value(start), date_field)))
            if end:
                domains.append(Domain(self._make_leaf(date_field.name, '<=', self._resolve_value(end), date_field)))
            title_parts.append(f"{date_field._description_string(self.env)}: {period[0].split(',')[0]}")
        if plan.get('name_id') and (plan.get('name_field') == 'id' or usable(plan.get('name_field'), ('many2one',))
                                    or self._usable_path(Model, plan.get('name_field'))):
            # a record mentioned with "@": by its id, not by its name
            domains.append(Domain(plan['name_field'], '=', int(plan['name_id'])))
            title_parts.append(str(plan.get('name_text') or '')[:60])
        elif (name_field := usable(plan.get('name_field'), ('many2one', 'char'))) and plan.get('name_text'):
            domains.append(Domain(name_field.name, 'ilike', str(plan['name_text'])[:60]))
            title_parts.append(str(plan['name_text'])[:60])
        domain = Domain.AND(domains)

        limit = plan.get('limit') or max_rows
        query = {
            'model': model_name,
            'mode': plan.get('mode') or 'list',
            'title': " · ".join(dict.fromkeys(title_parts)),
            'domain': domain,
            'limit': max(1, min(int(limit), max_rows)),
            'order': None,
        }
        measure = usable(plan.get('measure'), NUMERIC_FIELD_TYPES)
        aggregator = plan.get('aggregator') if plan.get('aggregator') in AGGREGATORS else 'sum'
        measures = [f"{measure.name}:{aggregator}"] if measure else []
        direction = 'asc' if plan.get('direction') == 'asc' else 'desc'
        sort = usable(plan.get('sort'))
        if query['mode'] == 'list':
            # the name of the records first, then the values asked for, then the columns of the list view
            first = Model._rec_name if usable(Model._rec_name) else 'display_name'
            columns = [first] + [extra.name for extra in (sort, measure) if extra and extra.name != first]
            columns += [name for name in self._get_list_view_columns(Model) if name not in columns]
            # a list view may hold alternative fields with the same label: show one
            labels = set()
            query['fields'] = [
                name for name in columns
                if not ((label := Model._fields[name]._description_string(self.env)) in labels or labels.add(label))
            ][:MAX_COLUMNS]
            if sort:
                query['order'] = f"{sort.name} {direction}"
        elif query['mode'] == 'total':
            query['mode'] = 'aggregate' if measures else 'count'
            query['group_by'], query['measures'] = [], measures
        elif query['mode'] == 'group':
            group_spec = plan.get('group_by') or 'none'
            name, _sep, is_date = group_spec.partition(':')
            group_field = usable(name)
            if not group_field or not group_field._description_groupable(self.env):
                raise self._invalid(self.env._("nothing to group by"))
            if group_field.type in ('date', 'datetime') or is_date:
                granularity = plan.get('granularity') if plan.get('granularity') in GRANULARITIES else 'month'
                group_by = f"{name}:{granularity}"
                query['order'] = f"{group_by} asc"
            else:
                group_by = name
                query['order'] = f"{measures[0] if measures else '__count'} {direction}"
            query['group_by'], query['measures'] = [group_by], measures
            if plan.get('link_field') and plan.get('subject_label'):
                # records totaled from the data linking to them: titled by what is ranked
                title_parts[0] = plan['subject_label']
                title_parts.insert(1, self.env._("from %s", plan.get('source_label') or Model._description))
            else:
                title_parts.append(self.env._("per %s", group_field._description_string(self.env)))
            query['title'] = " · ".join(dict.fromkeys(title_parts))
        elif query['mode'] != 'count':
            raise self._invalid(self.env._("unknown kind of answer"))
        # the data shown, then the conditions applied to it, for the web client to display apart
        parts = list(dict.fromkeys(title_parts))
        query['heading'], query['tags'] = parts[0], parts[1:]
        return query

    @api.model
    def _usable_path(self, Model, path):
        """ Whether a dotted path of many2one fields ("order_id.partner_id") can be used
        in a domain by the current user: each field usable, the last one a many2one. """
        if not path or '.' not in str(path):
            return False
        for name in str(path).split('.'):
            field = Model._fields.get(name)
            if not field or field.type != 'many2one' or not self._is_usable_field(Model, field):
                return False
            Model = self.env[field.comodel_name]
        return True

    @api.model
    def _resolve_value(self, value):
        """ Replace a date placeholder by its value. """
        if isinstance(value, str) and (match := PLACEHOLDER_RE.match(value.strip())):
            return self._resolve_placeholder(*match.groups())
        if isinstance(value, str) and DATE_RE.match(value):
            return date.fromisoformat(value)
        return value

    @api.model
    def _resolve_placeholder(self, name, sign=None, amount=None, unit=None):
        today = fields.Date.context_today(self)
        if name == 'now':
            moment = fields.Datetime.now()
        else:
            quarter_start = today.replace(month=3 * ((today.month - 1) // 3) + 1, day=1)
            moment = {
                'today': today,
                'yesterday': today - timedelta(days=1),
                'tomorrow': today + timedelta(days=1),
                'week_start': today - timedelta(days=today.weekday()),
                'week_end': today + timedelta(days=6 - today.weekday()),
                'month_start': today.replace(day=1),
                'month_end': today + relativedelta(day=31),
                'last_month_start': today.replace(day=1) - relativedelta(months=1),
                'last_month_end': today.replace(day=1) - timedelta(days=1),
                'quarter_start': quarter_start,
                'quarter_end': quarter_start + relativedelta(months=3, days=-1),
                'year_start': today.replace(month=1, day=1),
                'year_end': today.replace(month=12, day=31),
                'last_year_start': today.replace(year=today.year - 1, month=1, day=1),
                'last_year_end': today.replace(year=today.year - 1, month=12, day=31),
            }[name]
        if sign:
            delta = int(amount) * (1 if sign == '+' else -1)
            moment += {
                'd': relativedelta(days=delta), 'w': relativedelta(weeks=delta),
                'm': relativedelta(months=delta), 'y': relativedelta(years=delta),
            }[unit]
        return moment

    @api.model
    def _make_leaf(self, path, operator, value, field):
        """ Domain items of a condition: days are converted to the right moments for
        datetime fields, in the timezone of the user. """
        if field.type == 'datetime' and isinstance(value, date) and not isinstance(value, datetime):
            start = self._day_start_utc(value)
            next_start = self._day_start_utc(value + timedelta(days=1))
            if operator == '=':
                return ['&', (path, '>=', start), (path, '<', next_start)]
            if operator == '!=':
                return ['|', (path, '<', start), (path, '>=', next_start)]
            if operator in ('>=', '<'):
                return [(path, operator, start)]
            if operator == '>':
                return [(path, '>=', next_start)]
            if operator == '<=':
                return [(path, '<', next_start)]
        return [(path, operator, self._serialize(value))]

    @api.model
    def _day_start_utc(self, day):
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        moment = tz.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        return fields.Datetime.to_string(moment)

    @api.model
    def _serialize(self, value):
        if isinstance(value, (list, tuple)):
            return [self._serialize(v) for v in value]
        if isinstance(value, datetime):
            return fields.Datetime.to_string(value)
        if isinstance(value, date):
            return fields.Date.to_string(value)
        if isinstance(value, Domain):
            return self._serialize_domain(value)
        if isinstance(value, models.BaseModel):
            return value.ids
        return value

    @api.model
    def _get_list_view_columns(self, Model):
        arch = Model.get_views([(False, 'list')])['views']['list']['arch']
        columns = []
        for node in etree.fromstring(arch).xpath('/list/field'):
            name = node.get('name')
            hidden = node.get('column_invisible') in ('1', 'True') or node.get('invisible') in ('1', 'True')
            field = Model._fields.get(name)
            if field and not hidden and node.get('optional') != 'hide' and self._is_usable_field(Model, field) \
                    and field.type not in ('one2many', 'many2many'):
                columns.append(name)
        return columns

    # ------------------------------------------------------------
    # Execution, as the current user
    # ------------------------------------------------------------

    @api.model
    def _run_query(self, query):
        """ Run a checked query with the access of the current user.

        :return: the result to display, and a one line summary of it
        """
        Model = self.env[query['model']]
        domain = query['domain']
        base = {
            'title': query['title'],
            'heading': query.get('heading') or query['title'],
            'tags': query.get('tags') or [],
            'model': query['model'],
            'domain': self._serialize_domain(domain),
        }
        if query['mode'] == 'count':
            count = Model.search_count(domain)
            value = formatLang(self.env, count, digits=0)
            return (
                {**base, 'type': 'value', 'label': self.env._("Records"), 'value': value},
                f"{query['title']}: {value}",
            )
        if query['mode'] in ('aggregate', 'group'):
            return self._run_group_query(Model, query, base)

        records = Model.search(domain, order=query['order'], limit=query['limit'])
        total = Model.search_count(domain) if len(records) == query['limit'] else len(records)
        fields_ = [Model._fields[name] for name in query['fields']]
        result = {
            **base,
            'type': 'table',
            'openable': True,
            'total': total,
            'columns': [
                {
                    'label': field._description_string(self.env),
                    'numeric': field.type in NUMERIC_FIELD_TYPES,
                    'kind': 'date' if field.type in ('date', 'datetime') else False,
                }
                for field in fields_
            ],
            'rows': [
                {
                    'id': record.id,
                    'cells': [self._format_field(record, field) for field in fields_],
                    # the values themselves, to draw charts
                    'raw': [record[field.name] if field.type in NUMERIC_FIELD_TYPES else None for field in fields_],
                }
                for record in records
            ],
        }
        if not records:
            content = self.env._("No matching record found.")
        elif total > len(records):
            content = self.env._(
                "%(title)s: %(total)s records found, showing the first %(count)s.",
                title=query['title'], total=total, count=len(records),
            )
        else:
            content = self.env._("%(title)s: %(total)s record(s) found.", title=query['title'], total=total)
        return result, content

    @api.model
    def _run_group_query(self, Model, query, base):
        group_by, measures = query['group_by'], query['measures']
        aggregates = [*measures, '__count']
        rows = Model._read_group(
            query['domain'], group_by, aggregates, order=query['order'] if group_by else None,
            limit=query['limit'] if group_by else None,
        )
        measure_fields = [Model._fields[spec.partition(':')[0]] for spec in measures]
        columns = [
            {
                'label': Model._fields[spec.partition(':')[0]]._description_string(self.env),
                'numeric': False,
                # groups per period are drawn as a line
                'kind': 'date' if ':' in spec else False,
            }
            for spec in group_by
        ] + [
            {
                'label': f"{field._description_string(self.env)} ({spec.partition(':')[2]})",
                'numeric': True,
                'kind': False,
            }
            for spec, field in zip(measures, measure_fields)
        ] + [{'label': self.env._("Count"), 'numeric': True, 'kind': 'count'}]
        # groups of a many2one are records: each row opens its record (a product, a customer...)
        row_field = Model._fields[group_by[0]] if len(group_by) == 1 and ':' not in group_by[0] else None
        row_model = row_field.comodel_name if row_field and row_field.type == 'many2one' else False
        if row_model and not self.env[row_model].has_access('read'):
            row_model = False
        table_rows = []
        for row in rows:
            cells = [
                self._format_group_value(Model, spec, value) for spec, value in zip(group_by, row[:len(group_by)])
            ]
            cells += [self._format_number(field, value) for field, value in zip(measure_fields, row[len(group_by):])]
            cells.append(formatLang(self.env, row[-1] or 0, digits=0))
            raw = [None] * len(group_by) + [value or 0 for value in row[len(group_by):]]
            table_rows.append({'id': row[0].id if row_model and row[0] else False, 'cells': cells, 'raw': raw})

        if not group_by:
            # aggregate: key figures over all the matching records
            values = ", ".join(f"{column['label']}: {cell}" for column, cell in zip(columns, table_rows[0]['cells']))
            return (
                {
                    **base, 'type': 'value', 'label': columns[0]['label'], 'value': table_rows[0]['cells'][0],
                    'columns': columns, 'rows': table_rows,
                },
                f"{query['title']}: {values}",
            )
        result = {**base, 'type': 'table', 'openable': bool(row_model), 'row_model': row_model,
                  'total': len(rows), 'columns': columns, 'rows': table_rows}
        if not rows:
            return result, self.env._("No matching record found.")
        return result, self.env._("%(title)s: %(count)s group(s).", title=query['title'], count=len(rows))

    @api.model
    def _serialize_domain(self, domain):
        """ The domain, as JSON for the web client (to open the records in a list view). """
        return [
            item if isinstance(item, str) else [item[0], item[1], self._serialize(item[2])]
            for item in list(Domain(domain))
        ]

    # ------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------

    @api.model
    def _format_field(self, record, field):
        if field.name == 'display_name':
            return record.display_name or ''
        value = record[field.name]
        if field.type == 'monetary':
            currency_field = field.get_currency_field(record)
            currency = (
                record[currency_field]
                if currency_field and record._has_field_access(record._fields[currency_field], 'read') else None
            )
            return format_amount(self.env, value or 0.0, currency) if currency else formatLang(self.env, value or 0.0)
        return self._format_value(field, value)

    @api.model
    def _format_value(self, field, value):
        if field.type in ('integer', 'float', 'monetary'):
            return self._format_number(field, value)
        if value is False or value is None:
            return ''
        if field.type == 'many2one':
            return value.display_name or ''
        if field.type in ('one2many', 'many2many'):
            names = value[:3].mapped('display_name')
            return ", ".join(names) + (", …" if len(value) > 3 else '')
        if field.type == 'selection':
            return dict(field._description_selection(self.env)).get(value, str(value))
        if field.type == 'boolean':
            return self.env._("Yes") if value else self.env._("No")
        if field.type == 'date':
            return format_date(self.env, value)
        if field.type == 'datetime':
            return format_datetime(self.env, value, tz=self.env.user.tz or False)
        value = str(value)
        return value if len(value) <= MAX_CELL_LENGTH else value[:MAX_CELL_LENGTH - 1] + "…"

    @api.model
    def _format_number(self, field, value):
        if field.type == 'integer':
            return formatLang(self.env, value or 0, digits=0)
        return formatLang(self.env, value or 0.0)

    @api.model
    def _format_group_value(self, Model, spec, value):
        name, _sep, granularity = spec.partition(':')
        field = Model._fields[name]
        if value is False or value is None:
            return self.env._("None")
        if granularity and isinstance(value, date):
            return {
                'day': lambda d: format_date(self.env, d),
                'week': lambda d: self.env._("W%(week)s %(year)s", week=d.isocalendar()[1], year=d.isocalendar()[0]),
                'month': lambda d: format_date(self.env, d, date_format='MMMM yyyy'),
                'quarter': lambda d: f"Q{(d.month - 1) // 3 + 1} {d.year}",
                'year': lambda d: str(d.year),
            }[granularity](value)
        return self._format_value(field, value)

    # ------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------

    @api.model
    def _get_chart(self, question, result, usage=None):
        """ How to draw a table as a Chart.js chart, or False when it cannot be drawn.

        The usual cases are decided here, without any AI: values per category are
        drawn as bars, values per period as a line, and the type of chart the agent
        read in the question is drawn. Only when the question asks for a chart
        without saying which, or when several values could be drawn, Odoo's AI service
        (OLG) chooses, from the question and the names of the columns: it never sees
        the data. OpenRouter is never used for charts.

        :return: ``{'type', 'label', 'values', 'horizontal', 'preferred', 'source'}``,
            ``label`` and ``values`` being indexes of columns
        """
        columns, rows = result['columns'], result['rows']
        if len(rows) < 2 or len(rows) > MAX_CHART_ROWS:
            return False
        label = next((index for index, column in enumerate(columns) if not column['numeric']), None)
        values = [index for index, column in enumerate(columns) if column['numeric'] and column.get('kind') != 'count']
        values = values or [index for index, column in enumerate(columns) if column.get('kind') == 'count']
        if label is None or not values:
            return False
        is_period = columns[label].get('kind') == 'date'
        chart = {
            'type': 'line' if is_period else 'bar',
            'label': label,
            'values': values[:1],
            'source': 'local',
        }
        # the chart the question asks for, as the agent read it: a given type is drawn without asking more
        asked = self._get_intent().get('chart') or False
        wants_chart = bool(asked)
        if asked in CHART_TYPES:
            chart.update(type=asked, source='agent')
        elif (wants_chart or len(values) > 1) \
                and str2bool(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.chart_olg') or 'False', False):
            chart = self._get_olg_chart(question, columns, len(rows), usage) or chart
        chart['horizontal'] = chart['type'] == 'bar' and not is_period and len(rows) > 6
        # groups and asked charts are shown as a chart first, lists of records as a table
        chart['preferred'] = wants_chart or any(column.get('kind') == 'count' for column in columns)
        return chart

    @api.model
    def _get_olg_chart(self, question, columns, row_count, usage=None):
        """ The chart Odoo's AI service designs for a table, from its columns only. """
        description = "\n".join(
            f"{index}. {column['label']} ({'number' if column['numeric'] else 'text'})"
            for index, column in enumerate(columns)
        )
        prompt = (
            "You choose how to chart the answer to a business question. Reply with ONLY minified JSON, no text: "
            '{"type":"bar|line|pie|doughnut","label":<number of the column naming each item>,'
            '"values":[<numbers of the columns to draw>]}. A line suits periods, pie and doughnut suit the share '
            "of one value among few items, bars suit comparisons. Follow the chart the question asks for.\n"
            f"Question: {question}\nColumns:\n{description}\nRows: {row_count}"
        )
        try:
            content = self._text_chat(prompt, usage)
        except UserError as error:
            _logger.info("AI Chat Pro: no chart from Odoo's AI service: %s", error)
            return False
        chart = False
        if match := re.search(r'\{[\s\S]*\}', content or ''):
            try:
                answer = json.loads(match.group())
            except json.JSONDecodeError:
                answer = {}
            chart = self._check_chart(answer, columns)
        return chart

    @api.model
    def _check_chart(self, answer, columns):
        """ A valid chart from the answer of the AI, or False. """
        if not isinstance(answer, dict) or answer.get('type') not in CHART_TYPES:
            return False
        label, values = answer.get('label'), answer.get('values')
        if not isinstance(label, int) or not 0 <= label < len(columns) or not isinstance(values, list):
            return False
        values = [
            index for index in values
            if isinstance(index, int) and 0 <= index < len(columns) and columns[index]['numeric'] and index != label
        ]
        if not values:
            return False
        if answer['type'] in ('pie', 'doughnut'):
            values = values[:1]
        return {'type': answer['type'], 'label': label, 'values': values[:MAX_CHART_SERIES], 'source': 'odoo_ai'}

    # ------------------------------------------------------------
    # Reasoning, by Odoo's AI service
    # ------------------------------------------------------------

    @api.model
    def _reason(self, question, result, summary, usage):
        """ Answer a question that needs an analysis, from the data it is about. """
        if not str2bool(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.use_olg') or 'False', False):
            return {}
        header = " | ".join(column['label'] for column in result['columns'])
        lines = [" | ".join(str(cell)[:60] for cell in row['cells']) for row in result['rows'][:MAX_REASONING_ROWS]]
        prompt = (
            "You are a business analyst. Answer the question using only the data below, from the user's Odoo "
            "database. Be concise: at most 120 words, plain text, no table.\n"
            f"Question: {question}\nData ({summary}):\n{header}\n" + "\n".join(lines)
        )
        try:
            answer = self._text_chat(prompt, usage)
        except UserError as error:
            return {'content': self.env._(
                "%(summary)s\n(The analysis is not available: %(error)s)", summary=summary, error=error.args[0],
            )}
        return {
            'content': answer.strip() or summary,
            'source': 'openrouter_olg' if usage['ai_called'] else 'olg',
        }

    # ------------------------------------------------------------
    # AI services
    # ------------------------------------------------------------

    @api.model
    def _decide(self, state, questions, usage, api_key=None, ai_model=None):
        """ Ask the decision model (Jev, through OpenRouter's Decisions API) to answer
        typed questions about a state, and count the tokens it used.

        :return: the answers, by question name
        """
        ai_model = ai_model or self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.model') or DEFAULT_AI_MODEL
        data = self._openrouter_post(DECISIONS_ENDPOINT, {
            'model': ai_model,
            'state': state,
            'questions': questions,
            'user': str(self.env.uid),
        }, usage, api_key=api_key)
        tokens = data.get('usage') or {}
        usage['prompt_tokens'] += int(tokens.get('input_tokens') or 0)
        usage['completion_tokens'] += int(tokens.get('output_tokens') or 0)
        usage['cost'] += float(tokens.get('cost') or 0.0)
        answers = data.get('answers')
        return answers if isinstance(answers, dict) else {}

    @api.model
    def _openrouter_post(self, endpoint, payload, usage, api_key=None):
        """ Call an API of OpenRouter with the key of the settings.

        :return: the JSON answer
        """
        api_key = api_key or self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.openrouter_api_key')
        if not api_key:
            raise UserError(self.env._(
                "The AI assistant is not configured yet: an administrator must set the OpenRouter API key in "
                "Settings > AI Chat Pro.",
            ))
        try:
            response = requests.post(endpoint, timeout=60, headers={
                'Authorization': f"Bearer {api_key}",
                'HTTP-Referer': self.get_base_url(),
                'X-Title': "Odoo AI Chat Pro",
            }, json=payload)
        except requests.RequestException:
            raise UserError(self.env._("Oops, the AI service (OpenRouter) is unreachable! Please try again later."))
        usage['ai_called'] = True
        if response.status_code == 401:
            raise UserError(self.env._("The OpenRouter API key is invalid. Please check it in the settings."))
        if response.status_code == 402:
            raise UserError(self.env._("Your OpenRouter account has no credit left."))
        if response.status_code == 429:
            raise UserError(self.env._("Too many requests to the AI service. Please try again in a moment."))
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok or data.get('error'):
            _logger.warning("AI Chat Pro: OpenRouter error %s: %s", response.status_code, response.text[:500])
            error = data.get('error')
            message = error.get('message') if isinstance(error, dict) else None
            raise UserError(self.env._(
                "The AI service returned an error: %(error)s", error=message or response.status_code,
            ))
        return data

    @api.model
    def _get_openrouter_balance(self, refresh=False):
        """ The credits left on OpenRouter: what remains of the spending limit of the
        key, else, for a key without limit (that may spend all of it), the balance of
        the account. Kept for a minute, not to call OpenRouter on each question.

        :return: ``{'amount': float or None, 'kind': 'account'|'key'|False, 'error': str or False}``
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.openrouter_api_key')
        if not api_key:
            return {'amount': None, 'kind': False, 'error': self.env._("No API key set")}
        cache_key = (self.env.cr.dbname, hashlib.sha256(api_key.encode()).hexdigest())
        cached = _BALANCE_CACHE.get(cache_key)
        if cached and not refresh and time_module.monotonic() - cached[0] < BALANCE_CACHE_SECONDS:
            return cached[1]
        headers = {'Authorization': f"Bearer {api_key}"}
        balance = {'amount': None, 'kind': False, 'error': False}
        try:
            response = requests.get(OPENROUTER_KEY_ENDPOINT, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json().get('data') or {}
            if data.get('limit_remaining') is not None:
                balance.update(amount=data['limit_remaining'], kind='key')
            else:
                response = requests.get(OPENROUTER_CREDITS_ENDPOINT, headers=headers, timeout=10)
                if response.ok:
                    data = response.json().get('data') or {}
                    balance.update(amount=(data.get('total_credits') or 0.0) - (data.get('total_usage') or 0.0),
                                   kind='account')
                else:
                    balance['error'] = self.env._("No spending limit on this key")
        except (requests.RequestException, ValueError) as error:
            _logger.info("AI Chat Pro: could not read the OpenRouter balance: %s", error)
            balance['error'] = self.env._("Unavailable")
        _BALANCE_CACHE[cache_key] = (time_module.monotonic(), balance)
        return balance

    @api.model
    def _olg_chat(self, prompt):
        """ Ask Odoo's text generation service (OLG), as the HTML editor does. """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        endpoint = IrConfigParameter.get_param('ai_chat_pro.olg_api_endpoint') or DEFAULT_OLG_ENDPOINT
        try:
            response = iap_tools.iap_jsonrpc(endpoint + '/api/olg/1/chat', params={
                'prompt': prompt,
                'conversation_history': [],
                'database_id': IrConfigParameter.get_param('database.uuid'),
            }, timeout=60)
        except iap_tools.InsufficientCreditError:
            raise UserError(self.env._("You do not have enough credits to use Odoo's AI service."))
        except requests.RequestException:
            raise UserError(self.env._("Odoo's AI service is unreachable."))
        status = response.get('status')
        if status == 'success':
            return response.get('content') or ''
        if status == 'error_prompt_too_long':
            raise UserError(self.env._("the data is too long to be analyzed"))
        if status == 'limit_call_reached':
            raise UserError(self.env._("the maximum number of requests is reached, try again later"))
        raise UserError(self.env._("Odoo's AI service could not answer"))
