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

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .ai_chat_assistant import _keywords

_logger = logging.getLogger(__name__)

MAX_MENTION_MODELS = 30
MENTION_PER_MODEL = 4
MENTION_SEARCHED = 10
MAX_MENTIONS = 12
MAX_QUESTION_MENTIONS = 10
# a record typed after "@" without being picked in the list: "@S00006", "@Azure Interior" (a few words at most)
TYPED_MENTION_RE = re.compile(r'(?:^|(?<=\s))@(\S+(?:[ \t]+[^\s@]+){0,5})')
# fields shown on the card of a record mentioned alone
MAX_CARD_FIELDS = 10


def _rank_mention(name, term):
    """ How well a name matches the text typed after "@": the name starting with it,
    then a word of it, then the text anywhere (a reference, a code). """
    name = (name or '').lower()
    if name.startswith(term) or re.sub(r'^\[[^\]]*\]\s*', '', name).startswith(term):
        return 0
    if re.search(rf'\b{re.escape(term)}', name):
        return 1
    return 2


class AiChatConversation(models.Model):
    _inherit = 'ai.chat.conversation'

    @api.model
    def search_mentions(self, term):
        """ The records the current user can read whose name holds a text: what "@" offers
        in the chat.

        :return: ``[{model, id, name, label}]``
        """
        self._check_chat_access()
        term = (term or '').strip()[:60]
        if not term:
            return []
        results = []
        lowered = term.lower()
        for priority, (model_name, label) in enumerate(self.env['ai.chat.assistant']._get_mention_models()):
            try:
                found = self.env[model_name].name_search(term, limit=MENTION_SEARCHED)
            except (AccessError, UserError, ValueError):
                continue
            ranked = sorted(
                ((_rank_mention(name, lowered), priority, len(name), record_id, name) for record_id, name in found),
            )[:MENTION_PER_MODEL]
            results += [(rank, priority, length, {'model': model_name, 'id': record_id, 'name': name, 'label': label})
                        for rank, priority, length, record_id, name in ranked]
        # the names starting with the text typed first, whatever their model
        results.sort(key=lambda item: item[:3])
        return [item[3] for item in results[:MAX_MENTIONS]]

    @api.model
    def _get_question_mentions(self, mentions, question=None):
        """ The records a question mentions, checked: they exist and the current user can
        read them. A record typed after "@" without being picked in the list ("@S00006")
        is mentioned too, when a record bears that very name. """
        checked = []
        for mention in (mentions or [])[:MAX_QUESTION_MENTIONS]:
            if not isinstance(mention, dict) or mention.get('model') not in self.env:
                continue
            if not self.env['ai.chat.assistant']._is_allowed_model(mention['model']):
                continue
            record = self.env[mention['model']].browse(int(mention.get('id') or 0)).exists()
            try:
                record.check_access('read')
            except AccessError:
                continue
            if record:
                checked.append({'model': record._name, 'id': record.id, 'name': record.display_name,
                                'label': record._description})
        return checked + self._find_typed_mentions(question, checked)

    @api.model
    def _find_typed_mentions(self, question, mentions=()):
        """ The records typed after "@" in a question without being picked in the list:
        the one bearing exactly the name typed (the longest one, "@Azure Interior" rather
        than "@Azure"), among those "@" offers. """
        known = {mention['name'].lower() for mention in mentions}
        found = []
        for match in TYPED_MENTION_RE.finditer(question or ''):
            words = match.group(1).split()
            if len(found) + len(mentions) >= MAX_QUESTION_MENTIONS:
                break
            texts = [' '.join(words[:count]).rstrip('?!.,;:)') for count in range(len(words), 0, -1)]
            if any(text.lower() in known for text in texts):
                continue
            offered = self.search_mentions(words[0].rstrip('?!.,;:)'))
            for text in texts:
                lowered = text.lower()
                exact = [mention for mention in offered
                         if lowered in (mention['name'].lower(), re.sub(r'^\[[^\]]*\]\s*', '', mention['name']).lower())]
                if exact:
                    found.append(exact[0])
                    known.add(exact[0]['name'].lower())
                    break
        return found


class AiChatMessage(models.Model):
    _inherit = 'ai.chat.message'

    mentions = fields.Json(help="The records the question mentions with @: their model, id and name.")

    def _get_chat_values(self):
        values = super()._get_chat_values()
        values['mentions'] = self.mentions or []
        return values


class AiChatAssistant(models.AbstractModel):
    """ Records mentioned with "@" in a question: exact references, used instead of
    names to match. "list sales orders of @Azure Interior" filters on that very
    customer, "create a sales order for @Azure Interior" links to it, and a record
    mentioned alone ("@S00100") is shown as a card. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _get_mention_models(self):
        """ The models searched for "@": the business models the user reaches by a menu
        of their apps, those reached by the most menus first (contacts: from sales,
        invoicing, purchases...). Not those stored with another one offered (the variants
        of products), nor the records of the settings. """
        catalog = {
            model_name: (label, len(menus)) for model_name, label, _words, menus in self._get_model_catalog()
            if any(not self._is_settings_candidate({'path': menu[0]}) for menu in menus)
        }
        models_ = []
        for name in sorted(catalog, key=lambda name: (-catalog[name][1], name)):
            Model = self.env[name]
            if not Model._auto or any(parent in catalog for parent in Model._inherits):
                continue
            rec_name = Model._fields.get(Model._rec_name or '')
            if not rec_name and 'display_name' not in Model._fields:
                continue
            models_.append((name, catalog[name][0]))
        return models_[:MAX_MENTION_MODELS]

    def _get_mentions(self):
        return self.env.context.get('ai_chat_mentions') or []

    @api.model
    def _strip_mentions(self, question):
        """ The words of a question besides the names of the records it mentions. """
        rest = question or ''
        for mention in self._get_mentions():
            rest = re.sub(re.escape('@' + mention['name']), ' ', rest, flags=re.IGNORECASE)
        return rest.strip()

    @api.model
    def _get_record_card(self, mention):
        """ The card of a record mentioned alone: its main fields, as its list shows them. """
        record = self.env[mention['model']].browse(mention['id']).exists()
        if not record:
            raise UserError(self.env._("The record %s no longer exists.", mention['name']))
        record.check_access('read')
        Model = self.env[record._name]
        names = [name for name in self._get_list_view_columns(Model) if name in Model._fields]
        names += [name for name in self._get_create_fields(Model) if name not in names]
        shown = []
        for name in names:
            field = Model._fields[name]
            if field.type in ('one2many', 'binary', 'html') or name == Model._rec_name or not record[name] \
                    or not self._is_usable_field(Model, field):
                continue
            value = self._format_field(record, field)
            if value not in (None, '', False):
                shown.append({'label': field._description_string(self.env), 'value': str(value)})
            if len(shown) >= MAX_CARD_FIELDS:
                break
        return {
            'content': self.env._("%(label)s %(name)s", label=Model._description, name=record.display_name),
            'result': {
                'type': 'record', 'model': record._name, 'id': record.id, 'title': record.display_name,
                'model_label': Model._description, 'fields': shown,
            },
        }

    @api.model
    def _resolve_named_record(self, Model, question, plan, options, candidate=None):
        """ A record mentioned with "@" restricts the answer by its id: a customer of the
        orders, a product of the lines, or the record itself. """
        mentions = self._get_mentions()
        for mention in mentions:
            if candidate and candidate.get('anchor_path') and mention['model'] == candidate.get('anchor_model'):
                # the lines of the documents of the record: filtered through the document
                plan = {key: value for key, value in plan.items() if key not in ('name_field', 'name_text', 'name_missing')}
                return {**plan, 'name_field': candidate['anchor_path'], 'name_id': mention['id'],
                        'name_text': mention['name']}
            if mention['model'] == Model._name:
                plan = {key: value for key, value in plan.items() if key not in ('name_field', 'name_text', 'name_missing')}
                return {**plan, 'name_field': 'id', 'name_id': mention['id'], 'name_text': mention['name']}
            # the field of the search view linking to it, else any field linking to it ("the lines of @S00006")
            field_name = next((
                field_name for field_name in options['names']
                if (field := Model._fields.get(field_name)) and field.type == 'many2one'
                and field.comodel_name == mention['model']
            ), None) or self._get_link_field(Model, mention['model'])
            if field_name:
                plan = {key: value for key, value in plan.items()
                        if key not in ('name_field', 'name_text', 'name_missing')}
                return {**plan, 'name_field': field_name, 'name_id': mention['id'], 'name_text': mention['name']}
        return super()._resolve_named_record(Model, question, plan, options, candidate)

    # ------------------------------------------------------------
    # Records of other data than the one asked
    # ------------------------------------------------------------

    @api.model
    def _get_link_field(self, Model, comodel_name):
        """ The field of a model linking to records of another model, if any. """
        return next((
            name for name, field in Model._fields.items()
            if field.type == 'many2one' and field.comodel_name == comodel_name and self._is_usable_field(Model, field)
        ), None)

    @api.model
    def _link_to_anchors(self, question, candidate, usage):
        """ A question about some data naming a record of other data ("products of
        @S00006", "products of sales order S00006"): when the data asked can not be
        filtered on that record, the records linking both are answered instead: the
        lines the record holds that link to the data asked (the lines of the order, one
        per product). The names the agent read of other kinds of records are looked for
        as the records "@" offers, and then filter like mentions. """
        Model = self.env[candidate['model']]
        family = self._get_model_family(Model._name)
        mentions = list(self._get_mentions())
        for name in self._get_intent().get('names') or []:
            # a record of other data, else one of the data asked that the conversation showed ("the second one")
            anchor = self._find_named_anchor(name, family) or self._find_remembered_record(name)
            if anchor and anchor not in mentions:
                mentions.append(anchor)
        Assistant = self.with_context(ai_chat_mentions=mentions) if len(mentions) > len(self._get_mentions()) else self
        for anchor in mentions:
            # the data asked itself, or data that can be filtered on the record directly
            if anchor['model'] in family or self._get_link_field(Model, anchor['model']):
                continue
            if bridge := Assistant._find_bridge(question, family, anchor, usage):
                return Assistant, bridge
        return Assistant, candidate

    @api.model
    def _names_other_records(self, candidate):
        """ Whether the question mentions, or names, a record of other data than the
        candidate, that the data asked would be read through. """
        family = self._get_model_family(candidate['model'])
        if any(mention['model'] not in family for mention in self._get_mentions()):
            return True
        return any(self._find_named_anchor(name, family) for name in self._get_intent().get('names') or [])

    @api.model
    def _get_unrelated_records(self, plan):
        """ The records mentioned (or named and found) of other data than the one a plan
        reads, when the plan filters on none of them: the answer would ignore them. """
        if plan.get('name_id') or plan.get('model') not in self.env:
            return []
        family = self._get_model_family(plan['model'])
        return [mention for mention in self._get_mentions() if mention['model'] not in family]

    @api.model
    def _find_named_anchor(self, name, family):
        """ The record a name the agent read stands for, as a mention, when it is of
        another kind of record than the data asked: the one of the conversation bearing
        that very name, else the one among the records "@" offers of the kind of the
        name. """
        if remembered := self._find_remembered_record(name, family):
            # a record the conversation showed, mentioned or created: that very one
            return remembered
        kind = name.get('label') or ''
        text = (name.get('text') or '').strip().lower()
        if not _keywords(kind) or not text:
            return None
        for mention in self.env['ai.chat.conversation'].search_mentions(text):
            if mention['model'] in family or not self._same_kind(kind, mention['label']):
                continue
            if text in (mention['name'].lower(), re.sub(r'^\[[^\]]*\]\s*', '', mention['name']).lower()):
                return mention
        return None

    @api.model
    def _find_bridge(self, question, family, anchor, usage):
        """ The records a record holds (the one2many fields of its model) that link to
        the data asked: the lines of an order link to products. The decision model
        chooses when there are several. """
        Anchor = self.env[anchor['model']]
        bridges, paths = {}, {}
        for field in Anchor._fields.values():
            if field.type != 'one2many' or not field.inverse_name or field.comodel_name in family \
                    or field.comodel_name in bridges or not self._is_allowed_model(field.comodel_name) \
                    or not Anchor._has_field_access(field, 'read'):
                continue
            Line = self.env[field.comodel_name]
            inverse = Line._fields.get(field.inverse_name)
            if inverse and self._is_usable_field(Line, inverse) \
                    and any(self._get_link_field(Line, name) for name in family):
                bridges[field.comodel_name] = field._description_string(self.env)
        if not bridges:
            # two links away: the lines of the documents of the record (the order lines of the orders of a
            # customer link to products), filtered through the document
            for field in Anchor._fields.values():
                if field.type != 'one2many' or not field.inverse_name or not self._is_allowed_model(field.comodel_name) \
                        or not Anchor._has_field_access(field, 'read'):
                    continue
                Document = self.env[field.comodel_name]
                for lines in Document._fields.values():
                    if lines.type != 'one2many' or not lines.inverse_name or lines.comodel_name in family \
                            or lines.comodel_name in bridges or not self._is_allowed_model(lines.comodel_name) \
                            or not Document._has_field_access(lines, 'read'):
                        continue
                    Line = self.env[lines.comodel_name]
                    inverse = Line._fields.get(lines.inverse_name)
                    if inverse and self._is_usable_field(Line, inverse) \
                            and any(self._get_link_field(Line, name) for name in family):
                        bridges[lines.comodel_name] = (f"{lines._description_string(self.env)} of the "
                                                       f"{field._description_string(self.env)}")
                        paths[lines.comodel_name] = f"{lines.inverse_name}.{field.inverse_name}"
        if not bridges:
            return None
        chosen = next(iter(bridges))
        if len(bridges) > 1:
            criteria = {
                model_name: f"{self.env[model_name]._description} [{model_name}]: the {label} of the "
                            f"{Anchor._description}"
                for model_name, label in bridges.items()
            }
            answers = self._decide(question, {'data': {
                'type': 'choice',
                'instructions': f"The question names {anchor['label']} {anchor['name']}: which of its records "
                                "answer it?",
                'criteria': criteria,
            }}, usage)
            chosen = self._get_choice(answers, 'data', criteria, chosen)
        return {
            'model': chosen, 'label': self.env[chosen]._description, 'score': 0, 'path': '', 'domain': '',
            'context': '', 'search_view_id': False, 'menu_names': [],
            # how the records link to the record named, when not by a field of their own
            'anchor_model': anchor['model'], 'anchor_path': paths.get(chosen),
        }

    @api.model
    def _find_record_for_create(self, field, text, warnings, warn_missing=True, exact_only=False, choices=None):
        """ A record mentioned with "@" is the one a value of a record to create names. """
        lowered = (text or '').strip().lstrip('@').lower()
        for mention in self._get_mentions():
            if mention['model'] == field.comodel_name and lowered and (
                    lowered in mention['name'].lower() or mention['name'].lower() in lowered):
                return self.env[mention['model']].browse(mention['id'])
        return super()._find_record_for_create(field, text, warnings, warn_missing=warn_missing, exact_only=exact_only,
                                               choices=choices)
