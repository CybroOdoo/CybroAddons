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
#############################################################################
import json
import logging
import re

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain

from .dynamic_dashboard_block import (
    GROUPABLE_FIELD_TYPES,
    GROUPED_BLOCK_TYPES,
    MULTI_SERIES_BLOCK_TYPES,
    NUMERIC_FIELD_TYPES,
    STATIC_BLOCK_TYPES,
    SUB_GROUPED_BLOCK_TYPES,
    VALUE_BLOCK_TYPES,
)
from odoo.addons.iap.tools import iap_tools

_logger = logging.getLogger(__name__)

DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'
MAX_MODELS = 4
# number of blocks a user can ask the AI for
MAX_BLOCKS = 20
MAX_FIELDS = 40
# groups or records described to the AI when analyzing a block
MAX_ANALYZED_ROWS = 30
DOMAIN_OPERATORS = {'=', '!=', '>', '>=', '<', '<=', 'in', 'not in', 'ilike', 'not ilike'}
# technical models that never make a meaningful dashboard
EXCLUDED_MODEL_PREFIXES = (
    'ir.', 'base.', 'bus.', 'res.config', 'res.groups', 'res.lang', 'res.currency.rate', 'mail.', 'discuss.',
    'dynamic.dashboard', 'iap.', 'web_', 'web.', 'spreadsheet.', 'digest.', 'auth_', 'report.', 'resource.',
)
# kind of each block type, mirroring static/src/block_catalog/block_catalog.js
BLOCK_CATALOG = {
    'tile': "one key figure (count, total, average...) with an icon",
    'progress': "one figure compared to a target_value, as a progress bar",
    'gauge': "one figure compared to a target_value, as a gauge",
    'bar': "vertical bars comparing the values of group_by (optional sub_group_by for grouped bars)",
    'hbar': "horizontal bars, best for rankings with long labels (optional sub_group_by)",
    'stacked_bar': "bars of group_by stacked by sub_group_by (sub_group_by required)",
    'line': "trend over time: group_by a date field (optional sub_group_by for several lines)",
    'area': "volume over time: group_by a date field (optional sub_group_by)",
    'pie': "share of a total per value of group_by (few values)",
    'doughnut': "share of a total per value of group_by (few values)",
    'polar': "compare a few values of group_by",
    'radar': "compare profiles over the values of group_by (optional sub_group_by)",
    'table': "ranking table of the values of group_by",
    'pivot': "table crossing group_by (rows) and sub_group_by (columns), sub_group_by required",
    'record_list': "list of records with list_fields columns, sorted by order_by",
    'view': "embedded standard Odoo view of the model, view_mode list, kanban, graph or pivot",
    'text': "a section title (name) with an optional text_content, no model",
}
BLOCK_ICONS = [
    'tag', 'payments', 'attach_money', 'euro', 'shopping_cart', 'sell', 'receipt_long', 'group', 'person',
    'handshake', 'local_shipping', 'inventory_2', 'factory', 'storefront', 'description', 'mail',
    'calendar_today', 'schedule', 'task', 'check_circle', 'warning', 'star', 'trophy', 'rocket_launch',
]
BLOCK_COLORS = [
    '#714B67', '#017E84', '#2E7D32', '#E65100', '#C62828', '#1565C0', '#6A1B9A', '#F9A825', '#455A64', '#00838F',
]
DEFAULT_WIDTHS = {
    'tile': 3, 'progress': 4, 'gauge': 4, 'pie': 4, 'doughnut': 4, 'polar': 4, 'radar': 4, 'table': 4,
    'view': 12, 'text': 12,
}


class DynamicDashboardAiGenerator(models.AbstractModel):
    _name = 'dynamic.dashboard.ai.generator'
    _description = "Dynamic Dashboard AI Generator"

    # ------------------------------------------------------------
    # OLG
    # ------------------------------------------------------------

    @api.model
    def _olg_chat(self, prompt):
        """ Ask Odoo's text generation service (OLG), as the HTML editor does. """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        endpoint = IrConfigParameter.get_str('odoo_dynamic_dashboard.olg_api_endpoint') or DEFAULT_OLG_ENDPOINT
        try:
            response = iap_tools.iap_jsonrpc(endpoint + '/api/olg/1/chat', params={
                'prompt': prompt,
                'conversation_history': [],
                'database_id': IrConfigParameter.get_str('database.uuid'),
            }, timeout=60)
        except iap_tools.InsufficientCreditError:
            raise UserError(self.env._("You do not have enough credits to use the AI service."))
        except requests.RequestException:
            raise UserError(self.env._("Oops, it looks like our AI is unreachable! Please try again later."))
        status = response.get('status')
        if status == 'success':
            return response.get('content') or ''
        if status == 'error_prompt_too_long':
            raise UserError(self.env._("Sorry, your description is too long. Try to say it in fewer words."))
        if status == 'limit_call_reached':
            raise UserError(self.env._(
                "You have reached the maximum number of requests for this service. Try again later.",
            ))
        raise UserError(self.env._("Sorry, we could not generate a dashboard. Please try again later."))

    @api.model
    def _parse_json(self, content, expected_type):
        """ Extract the JSON value the AI answered with, ignoring any text around it. """
        pattern = r'\[[\s\S]*\]' if expected_type is list else r'\{[\s\S]*\}'
        if match := re.search(pattern, content or ''):
            try:
                value = json.loads(match.group())
            except json.JSONDecodeError:
                value = None
            if isinstance(value, expected_type):
                return value
        _logger.info("Dynamic dashboard: unexpected AI answer %r", (content or '')[:500])
        raise UserError(self.env._("The AI answer could not be understood. Please try again, or rephrase."))

    # ------------------------------------------------------------
    # Context given to the AI
    # ------------------------------------------------------------

    @api.model
    def _get_candidate_models(self):
        """ Business models the current user can read: those opened by a window action. """
        model_names = set(self.env['ir.actions.act_window'].sudo().search([]).mapped('res_model'))
        candidates = {}
        for model_name in sorted(model_names):
            if model_name not in self.env or model_name.startswith(EXCLUDED_MODEL_PREFIXES):
                continue
            Model = self.env[model_name]
            if Model._transient or Model._abstract or not Model._auto or not Model.has_access('read'):
                continue
            candidates[model_name] = Model._description or model_name
        return candidates

    @api.model
    def _get_model_fields(self, model_name):
        """ Fields the blocks of a model can use, by usage. """
        Model = self.env[model_name]
        measures, group_bys, dates, listables = {}, {}, {}, {}
        for name, field in Model._fields.items():
            if name == 'id' or not Model.has_field_access(field, 'read'):
                continue
            label = field._description_string(self.env)
            if field.store and field.type in NUMERIC_FIELD_TYPES and name not in ('sequence', 'color'):
                measures[name] = label
            if field.store and field.type in GROUPABLE_FIELD_TYPES and field._description_groupable(self.env):
                group_bys[name] = label
                if field.type in ('date', 'datetime'):
                    dates[name] = label
            if field.type not in ('one2many', 'many2many', 'binary', 'html', 'json', 'properties',
                                  'properties_definition'):
                listables[name] = label
        return {
            'measures': dict(list(measures.items())[:MAX_FIELDS]),
            'group_bys': dict(list(group_bys.items())[:MAX_FIELDS]),
            'dates': dates,
            'listables': listables,
        }

    @api.model
    def _prompt_pick_models(self, description, candidates):
        models_desc = "\n".join(f"- {name}: {label}" for name, label in candidates.items())
        return (
            "You are designing a business dashboard in Odoo.\n"
            f"The user wants: \"{description}\"\n\n"
            f"Available data models (technical name: label):\n{models_desc}\n\n"
            f"Pick the 1 to {MAX_MODELS} models whose data best answers this request. "
            "Return ONLY a JSON array of technical model names, most relevant first, "
            "e.g. [\"sale.order\", \"res.partner\"]. No explanation."
        )

    @api.model
    def _get_layout_instruction(self, block_count):
        """ How many blocks to design, and how many of them are key figures. """
        if not block_count:
            return "Design a dashboard of 6 to 12 blocks: start with 2 to 4 KPI tiles, then charts, then tables."
        if block_count <= 2:
            return (
                f"Design a dashboard of exactly {block_count} block(s): the most useful chart or key "
                "figure for the request, no text block."
            )
        kpi_count = max(1, min(4, round(block_count / 3)))
        return (
            f"Design a dashboard of exactly {block_count} blocks, no more, no less: start with about "
            f"{kpi_count} KPI tiles, then charts, then tables. Do not use text blocks unless there are "
            "more than 8 blocks."
        )

    @api.model
    def _prompt_design_dashboard(self, description, models_fields, block_count=None, existing_blocks=()):
        def fields_desc(fields_):
            return ", ".join(f"{name} ({label})" for name, label in fields_.items()) or "none"

        models_desc = "\n".join(
            f"Model {model_name} ({label}):\n"
            f"  numeric measures: {fields_desc(info['measures'])}\n"
            f"  group by fields: {fields_desc(info['group_bys'])}\n"
            f"  date fields: {fields_desc(info['dates'])}"
            for model_name, (label, info) in models_fields.items()
        )
        catalog_desc = "\n".join(f"- {block_type}: {desc}" for block_type, desc in BLOCK_CATALOG.items())
        return (
            "You are an expert designing Odoo dashboards out of building blocks.\n"
            f"The user wants: \"{description}\"\n\n"
            f"Data available:\n{models_desc}\n\n"
            f"Block types:\n{catalog_desc}\n\n"
            f"{self._get_layout_instruction(block_count)} Rules:\n"
            + (
                "- The dashboard already has these blocks, design different ones that complete them: "
                + "; ".join(f"{block['block_type']} \"{block['name']}\"" for block in existing_blocks) + "\n"
                if existing_blocks else ""
            ) +
            "- A tile, progress or gauge shows ONE number and has no group_by: name it after that "
            "number (\"Total Revenue\", \"Open Leads\"), and give it a domain to count a subset "
            "(e.g. [[\"is_company\", \"=\", true]]). Anything \"by\" or \"per\" something is a chart or a table.\n"
            "- Use line or area charts grouped by a date field for trends, pie or doughnut for shares "
            "of few values, hbar or table for rankings, record_list for latest or top records.\n"
            "- Only use the models and field names listed above. Measures are only used with sum, avg, "
            "min or max; count needs no measure.\n\n"
            "Return ONLY a JSON object, no explanation, with this shape:\n"
            "{\"name\": \"Dashboard name\", \"blocks\": [{\n"
            "  \"block_type\": \"one of the block types\",\n"
            "  \"name\": \"short block title\",\n"
            "  \"model\": \"technical model name\",\n"
            "  \"aggregate\": \"count|sum|avg|min|max\",\n"
            "  \"measure\": \"numeric field, when aggregate is not count\",\n"
            "  \"group_by\": \"group by field, for charts and tables\",\n"
            "  \"sub_group_by\": \"second group by field, optional\",\n"
            "  \"date_granularity\": \"day|week|month|quarter|year, when grouping by a date\",\n"
            "  \"group_limit\": 10,\n"
            "  \"target_value\": 100,\n"
            "  \"list_fields\": [\"fields shown by a record_list\"],\n"
            "  \"order_by\": \"field sorting a record_list\",\n"
            "  \"view_mode\": \"list|kanban|graph|pivot, for a view block\",\n"
            "  \"domain\": [[\"field\", \"operator\", \"value\"]],\n"
            "  \"icon\": \"one of: " + ", ".join(BLOCK_ICONS) + "\",\n"
            "  \"text_content\": \"for a text block\"\n"
            "}]}\n"
            "Omit the keys a block does not use. Keep domains simple, or omit them."
        )

    # ------------------------------------------------------------
    # Validation of the AI answer
    # ------------------------------------------------------------

    @api.model
    def _sanitize_domain(self, Model, raw_domain):
        """ Keep a simple AI-proposed domain only if it is valid on the model. """
        if not isinstance(raw_domain, list) or not raw_domain:
            return '[]'
        conditions = []
        for condition in raw_domain:
            if not (isinstance(condition, (list, tuple)) and len(condition) == 3):
                return '[]'
            field_name, operator, value = condition
            if field_name not in Model._fields or operator not in DOMAIN_OPERATORS:
                return '[]'
            if not isinstance(value, (str, int, float, bool, list)):
                return '[]'
            conditions.append((field_name, operator, value))
        try:
            Model.search_count(Domain.AND([Domain(*condition) for condition in conditions]), limit=1)
        except (ValueError, TypeError, AccessError, UserError):
            return '[]'
        return repr(conditions)

    @api.model
    def _sanitize_block(self, raw, models_fields, index):
        """ Turn a block proposed by the AI into a valid builder configuration, or None. """
        if not isinstance(raw, dict):
            return None
        block_type = raw.get('block_type')
        if block_type not in BLOCK_CATALOG:
            return None
        config = {
            'id': False,
            'block_type': block_type,
            'name': str(raw.get('name') or '').strip()[:80],
            'width': DEFAULT_WIDTHS.get(block_type, 6),
            'color': BLOCK_COLORS[index % len(BLOCK_COLORS)],
            'icon': raw.get('icon') if raw.get('icon') in BLOCK_ICONS else 'tag',
            'aggregate': 'count',
            'domain': '[]',
            'date_granularity': 'month',
            'group_limit': 10,
            'target_value': 0,
            'list_fields': [],
            'order_by': False,
            'order_desc': True,
            'view_mode': 'list',
            'text_content': '',
            'measure': False,
            'group_by': False,
            'sub_group_by': False,
            'model': False,
            'model_label': '',
        }
        if block_type in STATIC_BLOCK_TYPES:
            config['name'] = config['name'] or self.env._("Section")
            config['text_content'] = str(raw.get('text_content') or '')[:1000]
            return config

        model_name = raw.get('model')
        if model_name not in models_fields:
            return None
        model_label, info = models_fields[model_name]
        Model = self.env[model_name]
        config.update(model=model_name, model_label=model_label)
        config['domain'] = self._sanitize_domain(Model, raw.get('domain'))
        if isinstance(raw.get('group_limit'), int) and 0 < raw['group_limit'] <= 50:
            config['group_limit'] = raw['group_limit']

        if block_type == 'record_list':
            config['list_fields'] = [
                name for name in (raw.get('list_fields') or []) if name in info['listables']
            ][:6]
            if raw.get('order_by') in info['listables'] and Model._fields[raw['order_by']].store:
                config['order_by'] = raw['order_by']
            config['order_desc'] = raw.get('order_desc') is not False
            return config
        if block_type == 'view':
            if raw.get('view_mode') in ('list', 'kanban', 'graph', 'pivot'):
                config['view_mode'] = raw['view_mode']
            return config

        if raw.get('aggregate') in ('sum', 'avg', 'min', 'max') and raw.get('measure') in info['measures']:
            config.update(aggregate=raw['aggregate'], measure=raw['measure'])
        if block_type in VALUE_BLOCK_TYPES:
            if block_type in ('progress', 'gauge'):
                target = raw.get('target_value')
                if not isinstance(target, (int, float)) or target <= 0:
                    return None
                config['target_value'] = target
            return config

        if block_type in GROUPED_BLOCK_TYPES:
            if raw.get('group_by') not in info['group_bys']:
                return None
            config['group_by'] = raw['group_by']
            sub_group_by = raw.get('sub_group_by')
            if block_type in MULTI_SERIES_BLOCK_TYPES and sub_group_by in info['group_bys'] \
                    and sub_group_by != config['group_by']:
                config['sub_group_by'] = sub_group_by
            if block_type in SUB_GROUPED_BLOCK_TYPES and not config['sub_group_by']:
                return None
            if raw.get('date_granularity') in ('day', 'week', 'month', 'quarter', 'year'):
                config['date_granularity'] = raw['date_granularity']
        return config

    # ------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------

    @api.model
    def _add_designed_blocks(self, blocks, design, models_fields, wanted):
        """ Append the valid blocks of an AI design to ``blocks``, up to ``wanted`` blocks:
        the first valid ones, so that the blocks dropped as invalid do not lower the count. """
        raw_blocks = design.get('blocks') if isinstance(design.get('blocks'), list) else []
        blocks = list(blocks)
        for raw in raw_blocks[:2 * MAX_BLOCKS]:
            if len(blocks) >= wanted:
                break
            if config := self._sanitize_block(raw, models_fields, len(blocks)):
                blocks.append(config)
        return blocks

    @api.model
    def _generate_dashboard(self, description, block_count=None):
        """ Design a dashboard matching ``description`` with the AI.

        :param int block_count: number of blocks to design, decided by the AI when not given
        :return: ``{'name': str, 'blocks': [config]}``, the blocks being builder
            configurations (see ``dynamic.dashboard.block._get_block_config``), not saved
        """
        description = (description or '').strip()
        if not description:
            raise UserError(self.env._("Describe the dashboard you would like."))
        if block_count is not None and not (isinstance(block_count, int) and 1 <= block_count <= MAX_BLOCKS):
            raise UserError(self.env._("Choose between 1 and %s blocks.", MAX_BLOCKS))
        candidates = self._get_candidate_models()
        if not candidates:
            raise UserError(self.env._("You do not have access to any data to build a dashboard on."))

        answer = self._olg_chat(self._prompt_pick_models(description, candidates))
        model_names = [
            name for name in self._parse_json(answer, list) if isinstance(name, str) and name in candidates
        ][:MAX_MODELS]
        if not model_names:
            raise UserError(self.env._(
                "The AI did not find data matching your request. Try to mention what to analyze, "
                "e.g. sales orders, invoices, leads, products.",
            ))

        models_fields = {name: (candidates[name], self._get_model_fields(name)) for name in model_names}
        prompt = self._prompt_design_dashboard(description, models_fields, block_count=block_count)
        design = self._parse_json(self._olg_chat(prompt), dict)
        blocks = self._add_designed_blocks([], design, models_fields, block_count or MAX_BLOCKS)
        if block_count and blocks and len(blocks) < block_count:
            # the AI designed too few valid blocks: ask once for the missing ones
            prompt = self._prompt_design_dashboard(
                description, models_fields, block_count=block_count - len(blocks), existing_blocks=blocks,
            )
            try:
                extra_design = self._parse_json(self._olg_chat(prompt), dict)
            except UserError:
                extra_design = {}
            blocks = self._add_designed_blocks(blocks, extra_design, models_fields, block_count)
        if not any(block['model'] for block in blocks):
            raise UserError(self.env._("The AI could not design a dashboard for this request. Please rephrase it."))
        return {
            'name': str(design.get('name') or '').strip()[:80] or description[:80],
            'blocks': blocks,
        }

    # ------------------------------------------------------------
    # Analysis of a block
    # ------------------------------------------------------------

    @api.model
    def _format_number(self, value):
        if isinstance(value, float) and not value.is_integer():
            return f'{value:,.2f}'
        return f'{int(value or 0):,}'

    @api.model
    def _get_block_data_summary(self, block, data):
        """ Plain text description of the values a block displays, for the AI. """
        kind = block.block_type
        lines = []
        if kind in VALUE_BLOCK_TYPES:
            lines.append(f"Value: {self._format_number(data['value'])}")
            if block.target_value:
                progress = round(100 * (data['value'] or 0) / block.target_value)
                lines.append(f"Target: {self._format_number(block.target_value)} ({progress}% reached)")
        elif data.get('series'):
            labels, series = data['labels'], data['series']
            if not labels:
                return ''
            if len(series) == 1:
                lines += [
                    f"- {label}: {self._format_number(value)}"
                    for label, value in zip(labels[:MAX_ANALYZED_ROWS], series[0]['values'])
                ]
            else:
                lines.append("Rows are values of the grouping, columns are series: " + ", ".join(
                    serie['label'] for serie in series
                ))
                for index, label in enumerate(labels[:MAX_ANALYZED_ROWS]):
                    values = ", ".join(
                        f"{serie['label']}={self._format_number(serie['values'][index])}" for serie in series
                    )
                    lines.append(f"- {label}: {values}")
            if len(labels) > MAX_ANALYZED_ROWS:
                lines.append(f"(and {len(labels) - MAX_ANALYZED_ROWS} more groups)")
        elif 'rows' in data:
            if not data['rows']:
                return ''
            lines.append("Columns: " + " | ".join(column['label'] for column in data['columns']))
            lines += [" | ".join(row['values']) for row in data['rows'][:MAX_ANALYZED_ROWS]]
        elif kind == 'view':
            count = self.env[block.model_name].search_count(Domain(data.get('record_domain') or []))
            lines.append(f"Number of records: {count}")
        return "\n".join(lines)

    @api.model
    def _prompt_analyze_block(self, block, data, data_summary, filter_summary):
        Model = self.env[block.model_name]
        aggregate = dict(block._fields['aggregate']._description_selection(self.env))[block.aggregate]
        details = [
            f"Block title: {block.name}",
            f"Block type: {dict(block._fields['block_type']._description_selection(self.env))[block.block_type]}",
            f"Data: {Model._description} records",
            f"Measure: {aggregate} of {data['measure_label']}" if block.block_type not in ('record_list', 'view')
            else '',
            f"Grouped by: {block.group_by_field_id.field_description}" if block.group_by_field_id else '',
            f"Then split by: {block.sub_group_by_field_id.field_description}" if block.sub_group_by_field_id else '',
            f"Dates grouped by: {block.date_granularity}"
            if block.group_by_field_id.ttype in ('date', 'datetime') else '',
            f"Filters applied by the viewer: {filter_summary}" if filter_summary else '',
        ]
        language = self.env['res.lang']._get_data(code=self.env.lang).name or 'English'
        return (
            "You are a business analyst. Give a brief analysis of this dashboard block "
            "to the manager reading it.\n"
            f"Today is {fields.Date.context_today(self)}.\n"
            + "\n".join(detail for detail in details if detail)
            + f"\n\nValues displayed:\n{data_summary}\n\n"
            f"Answer in {language}. Write 3 to 5 short bullet points, each starting with \"- \": the key "
            "facts with their numbers, trends, outliers, concentrations or comparisons worth noticing. "
            "Then one last line starting with \"Recommendation:\" giving one concrete next step. "
            "Only rely on the values above, do not invent any. No introduction, no title, no other formatting."
        )

    @api.model
    def _analyze_block(self, block, filter_domain=None, filter_summary=''):
        """ Ask the AI for a brief analysis of what a block displays to the current user.

        :return: ``{'analysis': str}``
        """
        block.ensure_one()
        if block.block_type in STATIC_BLOCK_TYPES:
            raise UserError(self.env._("A text block has no data to analyze."))
        data = block._get_block_data(extra_domain=filter_domain)
        if data['error']:
            raise UserError(data['error'])
        data_summary = self._get_block_data_summary(block, data)
        if not data_summary:
            raise UserError(self.env._("This block has no data to analyze."))
        # field labels are read as superuser, like when the block is displayed
        prompt = self._prompt_analyze_block(block.sudo(), data, data_summary, filter_summary)
        analysis = self._olg_chat(prompt).strip()
        if not analysis:
            raise UserError(self.env._("Sorry, the AI did not answer. Please try again."))
        return {'analysis': analysis}
