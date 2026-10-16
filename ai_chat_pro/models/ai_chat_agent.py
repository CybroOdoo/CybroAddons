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

import json
import logging
import re

from odoo import api, models

from .ai_chat_assistant import CHART_TYPES, MAX_LIMIT, _keywords, _normalize, _similar, _stem, _words
from .ai_chat_creator import _loads_loosely

_logger = logging.getLogger(__name__)

# what a message may ask, as the agent tells Odoo's AI service: each intent is answered by a tool
INTENTS = {
    'query': "see, list, count, total, compare, explain or analyze data of the company (the default)",
    'create': "create one or several new records",
    'duplicate': "copy an existing record, maybe with changes; also a new record like, same as or based on an "
                 "existing one",
    'explain': "explain or summarize one given record, with its history",
    'report': "print the PDF report of one given record",
    'card': "only show a record mentioned with @",
    'import': "create records from the attached file",
    'file': "a question about the attached file",
    'change': "change, update, delete, confirm, cancel or send an existing record, or add something to it (add 5 "
              "lamps to S00042, set the price of X to 200)",
    'chat': "a greeting, thanks, or a question about the assistant itself (what it can do, how to use it), never "
            "about business data",
}
# what the understanding of a message holds, at most
MAX_STEPS = 4
MAX_PARTS = 6
MAX_TERMS = 6
MAX_NAMES = 5
MAX_TEXT = 200
MAX_LABEL = 80
MAX_REPLY = 600
# kinds of records the message may create, told to the AI so that it names them as Odoo does
MAX_CREATE_KINDS = 8
# the share of a message the parts of a request creating several records cover, at least
MIN_PARTS_COVERAGE = 0.7
# confidence of the decision model above which a question is answered with a deep analysis
DEFAULT_DEEP_CONFIDENCE = 0.6


def _text(value, size=MAX_TEXT):
    """ A short text read from the answer of the AI, or ``''``. """
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()[:size]


def _texts(values, count, size=MAX_LABEL):
    texts = [_text(value, size) for value in values] if isinstance(values, list) else []
    return list(dict.fromkeys(text for text in texts if text))[:count]


def _limit(value):
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    return min(value, MAX_LIMIT) if isinstance(value, int) and not isinstance(value, bool) and value > 0 else False


class AiChatAssistant(models.AbstractModel):
    """ The agent of the assistant: rather than a fixed pipeline of patterns, each
    message is first understood by Odoo's AI service (OLG, or the OpenRouter model of
    the settings), in one small call: what it asks (to read data, create,
    duplicate, explain or print a record, import a file...), the request written as a
    whole (follow-ups completed from the previous question), the data and names it
    gives, the count and the chart it asks for, and, for a request for advice, the
    data questions an analysis would need.

    The agent then calls the tool answering that intent. Questions on the data go to
    the decision model (Jev), which plans the query and also decides, with its
    confidence, whether showing the data answers it, whether a short explanation is
    needed, or whether a deep analysis of several sets of data is worth its cost: the
    agent only switches to a deep analysis when Jev is confident enough, so that most
    questions stay cheap and fast.

    Commands typed after "/" and a record mentioned alone are explicit: they are
    answered without asking any AI. Without Odoo's AI service, a message is read as a
    question on the data.
    """
    _inherit = 'ai.chat.assistant'

    # ------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------

    @api.model
    def _answer_question(self, question, previous_plan, usage, deep=False, attachments=None, **kwargs):
        # explicit syntax first: no AI is needed to read it
        if not attachments:
            if (answer := self._answer_command(question, usage)) is not None:
                return answer
            mentions = self._get_mentions()
            if len(mentions) == 1 and not self._strip_mentions(question):
                return self._get_record_card(mentions[0])
        intent = self._understand(question, usage, previous_plan=previous_plan, attachments=attachments)
        values = self.with_context(ai_chat_intent=intent)._run_intent(
            question, previous_plan, usage, intent, deep=deep, attachments=attachments,
        )
        if usage.get('ai_unavailable') and not intent.get('routed') and values.get('content'):
            # read without the AI: said, as requests to create, copy or explain are then not understood
            values['content'] = (f"{values['content']}\n" + self.env._(
                "(The AI service could not read your message: %s. I answered it as a question on the data; "
                "requests to create or copy records will work again when it is available.)",
                usage['ai_unavailable']))
        if isinstance(values.get('plan'), dict):
            # how the agent answered, kept with the plan
            values['plan'] = {**values['plan'], 'agent': {
                **(values['plan'].get('agent') or {}),
                'intent': intent['intent'], 'routed': intent.get('routed', False),
                **({'depth': usage['agent_depth']} if usage.get('agent_depth') else {}),
            }}
        return values

    @api.model
    def _run_intent(self, question, previous_plan, usage, intent, deep=False, attachments=None):
        """ Call the tool answering what the message asks. """
        kind = intent['intent']
        if attachments:
            return self._answer_with_attachment(question, attachments, usage, creates=kind in ('import', 'create'))
        if kind == 'chat':
            return {'content': intent['reply']}
        if kind == 'query' and intent.get('routed') and not deep and not any(
                intent.get(key) for key in ('terms', 'names', 'advice', 'multi_step', 'figures', 'steps')) \
                and not self._get_mentions() and not self._find_candidates(_keywords(question)):
            # a message naming no data at all ("what can you do for me?"): what the assistant does, with
            # questions on the data of the user, rather than "no data found"
            return {'content': self._get_help()}
        if kind in ('explain', 'report', 'change'):
            names = [name['text'] for name in intent.get('names') or []]
            reference = intent.get('reference') or (names[0] if names else '') or self._strip_mentions(question)
            if kind == 'change':
                return self._answer_change(reference, usage)
            return getattr(self, f'_command_{kind}')(reference, usage)
        if kind == 'card' and (mentions := self._get_mentions()):
            return self._get_record_card(mentions[0])
        if kind in ('create', 'duplicate') and self._is_create_enabled():
            request = question
            if self._get_memory()['turns'] and _normalize(intent['question']) != _normalize(question):
                # a request referring to the conversation ("an invoice for him"): with the names it refers to
                request = f"{question}\n({intent['question']})"
            if (values := self._run_create(request, usage, intent)) is not None:
                return values
        # a deep analysis is only asked for questions on the data, never for a request to create
        return self._run_data(question, previous_plan, usage, intent, deep=deep and kind == 'query')

    @api.model
    def _run_create(self, question, usage, intent):
        """ The draft of the records a request asks to create or duplicate; ``None`` when
        it names nothing the user can create (it is then read as a question). """
        if intent['intent'] == 'duplicate':
            reference = intent.get('reference')
            found = self._get_known_record_to_duplicate(reference)
            # the record to copy: by its reference, else by a name the agent read ("copy the contact X")
            for text in ([reference] if reference else []) + [name['text'] for name in intent.get('names') or []]:
                if found:
                    break
                if found := self._find_record_to_duplicate(question, text):
                    reference = text
            if found:
                return self._draft_copy(question, found, reference or found['record'].display_name, usage)
            # a record that does not exist: said, rather than another record created that the user did not ask
            return {'content': self.env._(
                "I could not find the record \"%(reference)s\" to duplicate among the records you can access. "
                "Write its reference as Odoo shows it, or mention it with @.", reference=reference or question,
            ), 'is_error': True}
        parts = intent.get('parts') or []
        kinds = {}
        siblings = False

        def kind_of(text, target, whole=None, scope=None):
            # the kind of record a target names, chosen once per target: the kind the part names in full,
            # when the target names only a part of it ("contact" for "a contact tag Zeta Prime")
            if (target, whole) not in kinds:
                candidate = self._choose_create_model(text, target, usage, whole=whole) if target else None
                # widened by the part naming it, or by the whole request when it has no parts
                if candidate and (scope or not parts):
                    candidate = self._widen_kind(scope or question, target, candidate)
                kinds[target, whole] = candidate
            return kinds[target, whole]

        # a request naming an existing numbered record ("a quotation like S00003, with 1 extra lamp"): a copy of
        # it, of its own kind (not a quotation template), with the changes asked
        for token in [word.strip('.,;:!?()"\'') for word in question.split()]:
            if len(token) < 3 or not any(c.isdigit() for c in token) or not any(c.isalpha() for c in token):
                continue
            if (found := self._find_record_to_duplicate(question, token)) and self._is_numbered(found['record']):
                return self._with_choices(question, self._draft_copy(
                    question, found, found['record'].display_name, usage), usage)
        main_target = intent.get('target')
        main = kind_of(question, main_target) if main_target else None
        if not main_target and not parts:
            # the kind of record the decision model reads in the request, when the agent named none
            main = self._choose_kind_to_create(question, usage)
            main_target = main['label'] if main else ''
        if main_target and not main:
            # the record asked for can not be created: said, rather than creating only the records it needs
            usage['no_data'] = True
            return {'content': self.env._(
                "I can not create a %(kind)s: you can create no record of that kind here (its app may not be "
                "installed, or you may not be allowed to).", kind=main_target,
            ), 'is_error': True}
        # a request naming an existing numbered record of the kind it creates ("a sales order like S00042, with
        # 2 more chairs"): a copy of it with these changes, whatever its parts
        targets = [target for target in [main_target, *(part['target'] for part in parts)] if target]
        for target in targets or [question]:
            if (candidate := kind_of(question, target)) \
                    and (based_on := self._find_numbered_source(candidate['model'], intent, question)):
                return self._with_choices(question, self._draft_copy(
                    question, based_on, based_on['record'].display_name, usage), usage)
        if main and not parts:
            # several new records of the kind asked, named one by one ("3 tasks: Wireframes, Mockups and Review")
            named = [name for name in intent.get('names') or []
                     if name.get('new') and self._same_kind(name.get('label') or '', main['label'])]
            if len(named) > 1:
                parts = [{'text': name['text'], 'target': main_target, 'verbatim': False, 'refers_to': []}
                         for name in named]
                siblings = True
            else:
                # new records of other kinds named with it, that are records of their own ("a project Zeta
                # Site with a task Survey"): parts linking to the record asked
                others = []
                for name in intent.get('names') or []:
                    if not name.get('new') or self._same_kind(name.get('label') or '', main['label']):
                        continue
                    other = kind_of(question, name.get('label') or '')
                    if other and other['model'] != main['model'] \
                            and not self._are_pieces_of(main['model'], [other['model']]):
                        others.append({'text': f"{name['label']} {name['text']}", 'target': name['label'],
                                       'verbatim': False, 'refers_to': [0]})
                if others:
                    parts = [{'text': question, 'target': main_target, 'verbatim': True, 'refers_to': []}, *others]
                    apart = "; ".join(part['text'] for part in others)
                    texts = [f"{question}\n(Only the {main['label']} is to be created now; created apart, by the "
                             f"same request: {apart}.)"] + [
                        f"{question}\n(Part of the request to create now: {part['text']})" for part in others]
                    part_kinds = [main] + [kind_of(question, part['target']) for part in others]
                    return self._with_choices(question, self._draft_records(
                        [(text, kind, part['refers_to']) for text, kind, part in zip(texts, part_kinds, parts)
                         if kind], usage), usage)
        texts = [part['text'] if part.get('verbatim', True) else (
            # a part the message does not write as it is: its values are read in the whole message
            f"{question}\n(Part of the request to create now: {part['text']})") for part in parts]
        part_kinds = [kind_of(text, part['target'], whole=question, scope=part['text']) for text, part in zip(texts, parts)]
        if main and self._are_pieces_of(main['model'], [candidate['model'] for candidate in part_kinds if candidate]):
            # parts that are the record asked and records it links to (its customer, its products, its tags): one
            # record, the records it needs and that do not exist drafted first
            parts = []
        if len(parts) > 1:
            # several records, one per part of the request, in its order: a part creating nothing of its
            # own ("... and add him to the VIP tag") stays with the part before it
            requests, request_of_part = [], []
            for part, text, candidate in zip(parts, texts, part_kinds):
                refers = part.get('refers_to')
                if refers is not None:
                    refers = sorted({request_of_part[index] for index in refers
                                     if index < len(request_of_part) and request_of_part[index] is not None})
                if candidate:
                    request_of_part.append(len(requests))
                    requests.append((text, candidate, refers))
                elif requests:
                    # a part creating nothing of its own adds to the record of the part before it
                    request_of_part.append(len(requests) - 1)
                    previous = requests[-1]
                    requests[-1] = (f"{previous[0]} {part['text']}", previous[1], previous[2])
                else:
                    request_of_part.append(None)
            if len(requests) > 1:
                return self._with_choices(question, self._draft_records(requests, usage, siblings=siblings), usage)
        # the kind of record the request names, else the one of its first part
        part_target = parts[0]['target'] if parts else ''
        if candidate := main or (kind_of(question, part_target) if part_target else None):
            return self._with_choices(question, self._draft_record(question, candidate, usage), usage)
        return None

    @api.model
    def _links_to(self, model_name, family):
        """ Whether the records of a model link to records of a family of models, by a
        field of their own or of their lines. """
        Model = self.env[model_name]
        for field in Model._fields.values():
            if field.type in ('many2one', 'many2many') and field.comodel_name in family:
                return True
            if field.type == 'one2many' and field.comodel_name in self.env and self._is_usable_field(Model, field) \
                    and self._is_line_model(self.env[field.comodel_name]) and any(
                        line.type in ('many2one', 'many2many') and line.comodel_name in family
                        for line in self.env[field.comodel_name]._fields.values()):
                return True
        return False

    @api.model
    def _get_document_kinds(self, families):
        """ The kinds of records the user creates from a menu of their apps that link to
        every one of the families of records given (orders and invoices, for a customer
        and products). """
        configuration = self._get_configuration_paths()
        found = []
        for model_name, label, _model_words, menus in self._get_model_catalog():
            paths = [menu[0] for menu in menus if menu[0] not in configuration]
            if not paths or not self._can_create(model_name) or self._is_settings_candidate({'path': paths[0]}) \
                    or any(model_name in family for family in families):
                continue
            if all(self._links_to(model_name, family) for family in families):
                found.append({'model': model_name, 'label': label, 'score': 0, 'path': paths[0], 'domain': menus[0][1],
                              'context': menus[0][2], 'search_view_id': menus[0][3],
                              'menu_names': list(dict.fromkeys(path.rpartition('/')[2] for path in paths))[:5],
                              'menu_count': len(menus)})
        return found[:MAX_CREATE_KINDS]

    @api.model
    def _widen_kind(self, scope, target, candidate):
        """ The kind of record the words of a request name in full, as a phrase, when the
        kind read names only a part of it: "contact tag" names Contact Tags, not Contact;
        "a product in the category X" still names a product. """
        wanted = _keywords(target)
        stems = [_stem(word) for word in _words(scope)]
        wider = []
        for other in self._find_candidates(_keywords(scope)):
            if other['model'] == candidate['model'] or not other.get('menu_names') or not self._can_create(other['model']) \
                    or self._is_settings_candidate(other):
                continue
            for phrase in [other['label'], *other['menu_names']]:
                words = [_stem(word) for word in _words(phrase) if len(word) > 2]
                if not words or not all(any(_similar(w, word) for word in words) for w in wanted) \
                        or len(words) <= len(wanted):
                    continue
                # the phrase, written in the request
                if any(all(_similar(words[offset], stems[start + offset]) for offset in range(len(words)))
                       for start in range(len(stems) - len(words) + 1)):
                    wider.append(other)
                    break
        return wider[0] if len(wider) == 1 else candidate

    @api.model
    def _choose_kind_to_create(self, question, usage):
        """ The kind of record a request asks to create, when the agent did not say:
        chosen by the decision model among the kinds the user can create from a menu that
        the words of the request match (a sales order, not the customer it names). """
        options = [c for c in self._find_candidates(_keywords(question))
                   if c.get('menu_names') and not self._is_settings_candidate(c) and self._can_create(c['model'])]
        # the records named with it (a customer, products) say what it is: a document linking to them (an order,
        # an invoice), whatever the language of the request
        linked = []
        for name in self._get_intent().get('names') or []:
            if name.get('new') or not name.get('label'):
                continue
            kinds = [c for c in self._find_candidates(_keywords(name['label'])) if c.get('menu_names')]
            if kinds:
                linked.append(self._get_model_family(kinds[0]['model']))
        if linked:
            documents = [c for c in self._get_document_kinds(linked) if c['model'] not in {o['model'] for o in options}]
            options = [c for c in options if all(self._links_to(c['model'], family) for family in linked)] + documents
        if len(options) < 2:
            return options[0] if options else None
        criteria = {
            f"option_{index}": f"{c['label']} [{c['model']}]" + (f" (menu {c['path']})" if c.get('path') else '')
            for index, c in enumerate(options)
        }
        answers = self._decide(question, {'record': {
            'type': 'choice',
            'instructions': "Which kind of record does the request ask to create? Not the records it only refers to "
                            "(the customer or the products of an order to create).",
            'criteria': criteria,
        }}, usage)
        return options[int(self._get_choice(answers, 'record', criteria, 'option_0').removeprefix('option_'))]

    @api.model
    def _are_pieces_of(self, model_name, part_models):
        """ Whether the kinds of records of the parts of a request are the record of a
        model and the records it links to, by its fields or the fields of its lines (a
        contact and its tags, a sales order and its customer and products), rather than
        records of their own (a project and its tasks, two contacts). """
        if sum(1 for name in part_models if name == model_name) > 1:
            return False
        if any(name != model_name and self._is_configuration_model(name) for name in part_models):
            # a tag, a category asked for by the request: created as asked, not as a value of the record
            return False
        Model = self.env[model_name]
        linked = set()
        for field in Model._fields.values():
            if field.type in ('many2one', 'many2many'):
                linked.add(field.comodel_name)
            elif field.type == 'one2many' and field.comodel_name in self.env and self._is_usable_field(Model, field) \
                    and self._is_line_model(self.env[field.comodel_name]):
                # the records the lines of the record link to (the products of the lines of an order): not the
                # lines themselves, nor the records of other documents (the tasks of a project, the invoices of
                # the orders of a customer are records of their own)
                linked.update(line.comodel_name for line in self.env[field.comodel_name]._fields.values()
                              if line.type in ('many2one', 'many2many')
                              and line.comodel_name not in (model_name, field.comodel_name))
        families = set().union(*(self._get_model_family(name) for name in linked)) if linked else set()
        return all(name == model_name or name in families for name in part_models)

    @api.model
    def _with_choices(self, question, values, usage):
        """ The draft of a request, unless several existing records match a name it
        gives: the user is then asked which one, each one offered as the request naming
        it exactly, to click. """
        result = values.get('result') or {}
        choices = [choice for draft in (result.get('steps') or [result]) for choice in draft.get('choices') or []]
        if not choices:
            return values
        choice = choices[0]
        pattern = re.compile(re.escape(choice['text']), re.IGNORECASE)
        usage['choices'] = [
            pattern.sub(lambda _match, option=option: option, question, count=1) if pattern.search(question)
            else f"{question} ({choice['field']}: {option})"
            for option in choice['options']
        ]
        return {'content': self.env._(
            "Several %(field)s match \"%(name)s\": which one do you mean? Choose it below, or write its name "
            "exactly.", field=choice['field'], name=choice['text'],
        ), 'plan': {'agent': {
            # the request understood, to answer the choice clicked without reading it again
            'understood': self._get_intent(),
            'choice': {**choice, 'questions': usage['choices']},
        }}}

    @api.model
    def _find_numbered_source(self, model_name, intent, question=''):
        """ The existing record of a model Odoo numbers itself that a request to create
        one names (by its number, or as a record of the conversation): the record it is
        to be based on. """
        Model = self.env[model_name]
        if not self._is_numbered(Model):
            return None
        mentioned = [mention for mention in self._get_mentions() if mention['model'] == model_name]
        if mentioned:
            record = Model.browse(mentioned[0]['id']).exists()
            return {'record': record, 'label': Model._description} if record else None
        texts = [name['text'] for name in intent.get('names') or []]
        texts += [intent['reference']] if intent.get('reference') else []
        # the references the request writes with figures ("S00042"), as Odoo numbers them
        texts += [word.strip('.,;:!?()"\'') for word in question.split() if any(char.isdigit() for char in word)]
        for text in texts:
            if found := self._search_reference(model_name, [text], exact_only=True):
                return found
        return None

    @api.model
    def _answer_change(self, reference, usage):
        """ A request to change, delete, confirm or send records: not done from the chat,
        said plainly, with the record named shown to open it. """
        content = self.env._("I do not change, delete, confirm or send records from the chat: I only read data, "
                             "and draft new records for you to confirm. Open the record to change it.")
        record = self._get_command_record(reference) if reference else None
        if record:
            card = self._get_record_card({'model': record._name, 'id': record.id, 'name': record.display_name})
            return {**card, 'content': f"{content}\n{card['content']}"}
        return {'content': content}

    @api.model
    def _get_known_record_to_duplicate(self, reference):
        """ The record to copy the message points to exactly: the one mentioned with "@",
        else the one of the conversation bearing the reference, or named in the request
        as the agent wrote it whole ("the second one": "duplicate S00004"). """
        records = [mention for mention in self._get_mentions() if self._can_create(mention['model'])]
        if not records:
            intent = self._get_intent()
            texts = [reference] if reference else []
            texts += [name['text'] for name in intent.get('names') or []]
            for text in texts:
                if (remembered := self._find_remembered_record({'label': '', 'text': text})) \
                        and self._can_create(remembered['model']):
                    records = [remembered]
                    break
            else:
                request = (intent.get('question') or '').lower()
                records = [record for record in self._get_memory()['records']
                           if self._can_create(record['model']) and str(record['name']).lower() in request][:1]
        if not records:
            return None
        record = self.env[records[0]['model']].browse(records[0]['id']).exists()
        return {'record': record, 'label': record._description} if record else None

    @api.model
    def _run_data(self, question, previous_plan, usage, intent, deep=False):
        """ The answer to a question on the data: by the data tool, switching to a deep
        analysis when the user asks for one, when the decision model is confident the
        question needs one, or when it asks for advice the data tool can not answer
        from a single set of data. """
        deep_enabled = self._is_deep_analysis_enabled()
        if deep and deep_enabled:
            usage['agent_depth'] = 'deep'
            return self._answer_deep(intent.get('question') or question, usage, steps=intent.get('steps'))
        values = self._answer_data(question, previous_plan, usage)
        escalate = values.pop('escalate', False)
        if deep_enabled and not escalate and intent.get('advice') and (
                usage.get('alternatives') or (usage.get('no_data') and intent.get('steps'))):
            # advice on data the decision model is unsure of, or that no single data answers: an analysis
            # of the data the agent planned
            escalate, values = True, {**values, 'result': None}
        if not escalate:
            return values
        usage['agent_depth'] = 'deep'
        usage.pop('no_data', None)
        usage.pop('alternatives', None)
        return self._answer_deep(
            intent.get('question') or question, usage, steps=intent.get('steps'), first=values.get('result') or {},
        )

    @api.model
    def _choose_depth(self, plan, usage):
        """ The depth the decision model chose, kept only when the agent may take it: a
        deep analysis needs to be enabled, and the decision model confident enough; it
        is an explanation of the data otherwise. The data of an analysis is only read. """
        depth = super()._choose_depth(plan, usage)
        if self.env.context.get('ai_chat_data_only'):
            return 'data'
        if depth != 'deep':
            return depth
        confidence = plan.get('depth_confidence')
        if self._is_deep_analysis_enabled() and (confidence is None or confidence >= self._get_deep_confidence()):
            return 'deep'
        return 'explain'

    @api.model
    def _get_deep_confidence(self):
        value = self.env['ir.config_parameter'].sudo().get_float('ai_chat_pro.deep_confidence', None)
        return min(max(value, 0.0), 1.0) if value else DEFAULT_DEEP_CONFIDENCE

    # ------------------------------------------------------------
    # Understanding, by Odoo's AI service
    # ------------------------------------------------------------

    @api.model
    def _understand(self, question, usage, previous_plan=None, attachments=None):
        """ What a message asks, read by Odoo's AI service.

        :return: ``{'intent', 'routed', 'question', 'follow_up', 'terms', 'names', 'limit',
            'chart', 'ranks_by_total', 'advice', 'steps', 'target', 'parts', 'reference',
            'reply'}``; only ``intent`` and ``routed`` when the AI could not answer
        """
        if chosen := self._understand_choice(question, previous_plan):
            return chosen
        previous = self._describe_previous(previous_plan)
        memory = self._describe_memory()
        mentions = [f"@{mention['name']}" + (f" ({mention['label']})" if mention.get('label') else '')
                    for mention in self._get_mentions()]
        files = [attachment.name for attachment in attachments] if attachments else []
        context = []
        if memory:
            # the conversation so far: the message may refer to anything it said ("him", "the second one")
            context.append(f"Conversation so far:\n{memory}")
        if previous:
            context.append(f"Previous question: {previous}")
        if mentions:
            context.append(f"Records mentioned with @: {', '.join(mentions)}")
        if files:
            context.append(f"Attached file: {', '.join(files)}")
        if kinds := self._get_create_kinds(question):
            context.append(f"Kinds of records the user can create that the message may name: {', '.join(kinds)}")
        prompt = (
            "You are the planner of the AI assistant of Odoo, the business software. Understand the user's "
            "message. Reply with ONLY minified JSON, no text, leaving out the keys that do not apply:\n"
            '{"intent":"<an intent below>",'
            '"question":"<the message as one complete request standing alone, in the language of the message: '
            'completed from the conversation when it continues it or refers to what it said (him, that order, '
            'the second one...), with the names it refers to written out>",'
            '"follow_up":<true when it keeps the records of the previous question, only filtering, sorting, '
            'grouping or charting them otherwise>,'
            '"terms":["<words naming the kind of records or figures asked, as Odoo menus name them, e.g. sales '
            'orders, vendor bills, products, salespersons, profit>"],'
            '"names":[{"label":"<the kind of record the name is of: customer, product, sales order, invoice...; '
            'a reference like S00006 is of a sales order, not of the products asked>","text":"<a name or '
            'reference of a record exactly as written, not one mentioned with @>","new":<true only when the message '
            'says this very record does not exist yet, e.g. the new customer X>}: every record named, each of '
            'several records to create too (two products Zeta A and Zeta B: two names, new)],'
            '"limit":<the number of records asked, e.g. 10 for top 10>,'
            '"chart":"<bar|line|pie|doughnut, or any for a chart of no given type>",'
            '"ranks_by_total":<true when records are ranked by what other records total: sold, bought, spent, '
            'invoiced the most>,'
            '"advice":<true when it asks for a decision, advice, causes or a forecast>,'
            '"figures":<true when it asks for accounting figures computed from the books: profit, loss, turnover, '
            'income, expenses, balance, cash...>,'
            '"multi_step":<true when a first answer is needed to ask the data asked, e.g. the products of my '
            'biggest order, the customers of the salesperson who sold the most>,'
            '"steps":[<with advice: up to 4 simple data questions the analysis needs; with multi_step: the first '
            'data question only; each {"q":"<question>","terms":[...],"limit":<n>,"names":[...]}>],'
            '"spoken":["<create: each number, date or time the message writes in words, copied exactly, e.g. two, '
            'tomorrow, next monday>"],'
            '"target":"<required with create or import: the kind of record to create, one of the kinds below when '
            'one fits; a '
            'customer, vendor, person or company the business deals with is a contact>",'
            '"parts":[<only when two records or more are created, never for the lines of one record ("with 2 '
            'chairs" is a line): one '
            '{"text":"<its part of the message, copied word '
            'for word>","target":"<its kind of record, named as for target>","refers_to":[<numbers, from 1, of '
            'the earlier parts whose record it links to, by name or by a pronoun (in it, that project, there, '
            'them, the same company); [] for none>]} per record>],'
            '"reference":"<duplicate, explain, report or change: only the reference or name of the record, e.g. S00042 '
            'or Azure Interior, without the words naming its kind; the one of the conversation when the message '
            'refers to it (the second one)>",'
            '"reply":"<chat: a short answer>"}\n'
            "Intents: " + "; ".join(f"{name}: {description}" for name, description in INTENTS.items()) + "\n"
            + "".join(f"{line}\n" for line in context)
            + f"Message: {question}"
        )
        try:
            content = self._text_chat(prompt, usage)
            answer = _loads_loosely(content)
            if not isinstance(answer, dict):
                _logger.info("AI Chat Pro: the message %r was not understood, the AI answered: %s", question,
                             (content or '')[:300])
        except Exception as error:  # noqa: BLE001 - the message is still answered, as a question on the data
            _logger.info("AI Chat Pro: the message %r was not understood: %s", question, error)
            usage['ai_unavailable'] = str(error.args[0] if getattr(error, 'args', None) else error)[:200]
            answer = None
        return self._clean_intent(answer, question, f"{previous}\n{memory}".strip(), attachments)

    @api.model
    def _get_help(self):
        """ What the assistant does, told with questions on the apps of the user. """
        examples = self._get_example_questions()
        lines = [self.env._("I answer questions on your Odoo data, in plain words, and show the records found: "
                            "lists, counts, totals, breakdowns and charts, that you can download as PDF or Excel.")]
        if examples.get('others'):
            lines.append(self.env._("For example: %s.", ", ".join(f"\"{text}\"" for text in examples['others'])))
        if self._is_create_enabled():
            lines.append(self.env._("I can also draft records for you to confirm (\"%s...\"), copy existing ones "
                                    "(\"duplicate S00042 for another customer\"), and import a spreadsheet.",
                                    examples.get('create') or self.env._("create a ")))
        lines.append(self.env._("Mention a record with @ to point to it exactly, /explain it or /report it."))
        if self._is_deep_analysis_enabled():
            lines.append(self.env._("Ask for advice (\"how can I increase my sales?\") to get a deep analysis with "
                                    "findings and next steps."))
        return "\n".join(lines)

    @api.model
    def _get_create_kinds(self, question):
        """ The kinds of records the user can create that the words of a message match,
        as their menus name them: found locally, without AI. """
        if not self._is_create_enabled():
            return []
        kinds = []
        configuration = self._get_configuration_paths()
        for candidate in self._find_candidates(_keywords(question)):
            # those users create from a menu of their apps, named as the menus name them ("Bills" of the
            # vendors, not "Journal Entry"): not the settings, nor the configuration, nor technical records
            if candidate.get('menu_names') and not self._is_settings_candidate(candidate) \
                    and self._can_create(candidate['model']):
                path = candidate.get('path') or ''
                if path and (path not in configuration or not candidate.get('unmatched')):
                    kinds.append(f"{path.rpartition('/')[2]} ({path})")
        return list(dict.fromkeys(kinds))[:MAX_CREATE_KINDS]

    @api.model
    def _understand_choice(self, question, previous_plan):
        """ The understanding of a request asked again with one of the records the user
        was asked to choose among: the one of the request, with that record named. """
        agent = (previous_plan or {}).get('agent') or {}
        choice = agent.get('choice')
        understood = agent.get('understood')
        if not choice or not understood or question not in (choice.get('questions') or []):
            return None
        option = choice['options'][choice['questions'].index(question)]
        intent = json.loads(json.dumps(understood))
        intent['question'] = question
        intent['names'] = [
            {**name, 'text': option} if name['text'].lower() == choice['text'].lower() else name
            for name in intent.get('names') or []
        ]
        if not any(name['text'] == option for name in intent['names']):
            intent['names'].append({'label': choice['field'], 'text': option})
        for part in intent.get('parts') or []:
            part['text'] = re.sub(re.escape(choice['text']), option, part['text'], flags=re.IGNORECASE)
        return intent

    @api.model
    def _describe_previous(self, previous_plan):
        """ The previous question of the conversation, with the data it was answered from. """
        plan = previous_plan or {}
        text = (plan.get('questions') or [''])[0] if plan.get('kind') == 'deep' else plan.get('question')
        text = _text(text)
        if not text:
            return ''
        source = plan.get('source_label') or plan.get('menu_path') or (
            self.env[plan['model']]._description if plan.get('model') in self.env else '')
        return f"{text} (data: {source})" if source else text

    @api.model
    def _clean_intent(self, answer, question, previous='', attachments=None):
        """ The understanding of a message, checked: only the expected keys, of the
        expected types, and the names of records the message (or the question it
        continues) does write. """
        if isinstance(answer, dict) and answer.get('intent') in ('multi_step', 'advice', 'figures', 'deep', 'analysis'):
            # the AI answered a flag as the intent: a question on the data, with that flag
            answer = {**answer, 'intent': 'query', **({answer['intent']: True} if answer['intent'] in (
                'multi_step', 'advice', 'figures') else {'advice': True})}
        if not isinstance(answer, dict) or answer.get('intent') not in INTENTS:
            return {'intent': 'file' if attachments else 'query', 'routed': False}
        kind = answer['intent']
        if attachments:
            kind = kind if kind in ('import', 'create', 'file') else 'file'
        elif kind in ('import', 'file'):
            kind = 'create' if kind == 'import' else 'query'
        if kind == 'card' and not self._get_mentions():
            kind = 'query'
        reply = _text(answer.get('reply'), MAX_REPLY)
        if kind == 'chat' and not reply:
            kind = 'query'
        written = f"{question} {previous}".lower()
        intent = {
            'intent': kind,
            'routed': True,
            'question': _text(answer.get('question')) or question,
            'follow_up': answer.get('follow_up') is True and bool(previous),
            'terms': _texts(answer.get('terms'), MAX_TERMS),
            'names': self._clean_names(answer.get('names'), written),
            'limit': _limit(answer.get('limit')),
            'chart': answer.get('chart') if answer.get('chart') in (*CHART_TYPES, 'any') else False,
            'ranks_by_total': answer.get('ranks_by_total') is True,
            'advice': answer.get('advice') is True,
            'figures': answer.get('figures') is True and kind == 'query',
            'multi_step': answer.get('multi_step') is True and kind == 'query',
            'steps': [],
            'target': _text(answer.get('target'), MAX_LABEL),
            # numbers and dates written in words, that the values read for a record may come from
            'spoken': [text for text in _texts(answer.get('spoken'), MAX_TERMS) if text.lower() in question.lower()],
            'parts': [],
            'reference': _text(answer.get('reference'), MAX_LABEL),
            'reply': reply if kind == 'chat' else '',
        }
        if (intent['advice'] or intent['multi_step']) and isinstance(answer.get('steps'), list):
            steps = [self._clean_step(step, written) for step in answer['steps']]
            intent['steps'] = [step for step in steps if step][:MAX_STEPS]
        # parts are records: a single one is the record of the whole message, never a line of it, and parts
        # covering only a little of the message are pieces of one record (its customer, its lines)
        parts = answer.get('parts') if isinstance(answer.get('parts'), list) else []
        covered = sum(len(_text(part.get('text'), 1000)) for part in parts if isinstance(part, dict))
        if kind == 'create' and len(parts) > 1 and covered >= MIN_PARTS_COVERAGE * len(question):
            for index, part in enumerate(answer['parts'][:MAX_PARTS]):
                if isinstance(part, dict) and (text := _text(part.get('text'), 1000)):
                    refers = part.get('refers_to')
                    numbers = [number for number in refers if isinstance(number, int) and not isinstance(number, bool)] \
                        if isinstance(refers, list) else []
                    # numbered from 1 as asked, or from 0 as the AI may
                    start = 0 if 0 in numbers else 1
                    intent['parts'].append({
                        'text': text,
                        'target': _text(part.get('target'), MAX_LABEL),
                        # whether the message writes the part as it is: else it is read in the whole message
                        'verbatim': _normalize(text) in _normalize(question),
                        'refers_to': sorted({number - start for number in numbers if 0 <= number - start < index})
                        if isinstance(refers, list) else None,
                    })
        return intent

    @api.model
    def _clean_names(self, names, written):
        """ The names of records the AI read, that the text does write: not those of the
        records mentioned with "@", which are exact references already. """
        mentioned = [mention['name'].lower() for mention in self._get_mentions()]
        found = []
        for name in names if isinstance(names, list) else []:
            if isinstance(name, dict) and (text := _text(name.get('text'), 60).lstrip('@')) \
                    and text.lower() in written and not any(
                        text.lower() in mention or mention in text.lower() for mention in mentioned):
                found.append({'label': _text(name.get('label'), MAX_LABEL), 'text': text,
                              **({'new': True} if name.get('new') is True else {})})
        return found[:MAX_NAMES]

    @api.model
    def _clean_step(self, step, written=None):
        """ A data question of an analysis, understood as any question; ``None`` when it
        has no text. Its names are only kept when the question asked writes them. """
        if isinstance(step, str):
            step = {'q': step}
        if not isinstance(step, dict) or not (text := _text(step.get('q') or step.get('question'))):
            return None
        return {
            'intent': 'query',
            'routed': True,
            'question': text,
            'terms': _texts(step.get('terms'), MAX_TERMS),
            'names': self._clean_names(step.get('names'), written if written is not None else text.lower()),
            'limit': _limit(step.get('limit')),
        }
