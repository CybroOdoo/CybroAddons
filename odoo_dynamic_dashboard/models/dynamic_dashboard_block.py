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
import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import format_date, format_datetime, formatLang, safe_eval

_logger = logging.getLogger(__name__)

NUMERIC_FIELD_TYPES = ['integer', 'float', 'monetary']
GROUPABLE_FIELD_TYPES = ['many2one', 'selection', 'char', 'boolean', 'date', 'datetime', 'integer']

# blocks showing one aggregated figure
VALUE_BLOCK_TYPES = ['tile', 'progress', 'gauge']
# blocks needing a group by
GROUPED_BLOCK_TYPES = [
    'bar', 'hbar', 'stacked_bar', 'line', 'area', 'pie', 'doughnut', 'polar', 'radar', 'table', 'pivot',
]
# grouped blocks that also need a second group by
SUB_GROUPED_BLOCK_TYPES = ['stacked_bar', 'pivot']
# grouped blocks that can show one series per value of a second group by
MULTI_SERIES_BLOCK_TYPES = ['bar', 'hbar', 'stacked_bar', 'line', 'area', 'radar', 'pivot']
# blocks without any model
STATIC_BLOCK_TYPES = ['text']
MAX_SERIES = 12

# fields exchanged as is with the dashboard builder, see _get_block_config
CONFIG_FIELDS = [
    'name', 'block_type', 'domain', 'aggregate', 'date_granularity', 'group_limit', 'width', 'color',
    'icon', 'target_value', 'order_desc', 'view_mode', 'text_content',
]
# fields exchanged by field name with the dashboard builder
CONFIG_FIELD_REFS = {
    'measure': 'measure_field_id',
    'group_by': 'group_by_field_id',
    'sub_group_by': 'sub_group_by_field_id',
    'order_by': 'order_field_id',
}


class DynamicDashboardBlock(models.Model):
    _name = 'dynamic.dashboard.block'
    _description = "Dynamic Dashboard Block"
    _order = 'sequence, id'

    name = fields.Char(
        compute='_compute_name', store=True, readonly=False, precompute=True, required=True,
        help="Suggested from the model and fields, it can be changed freely.",
    )
    sequence = fields.Integer(default=10)
    dashboard_id = fields.Many2one(
        'dynamic.dashboard', string="Dashboard", required=True, index=True, ondelete='cascade',
    )
    block_type = fields.Selection(
        [
            ('tile', "KPI Tile"),
            ('progress', "Progress Bar"),
            ('gauge', "Gauge"),
            ('bar', "Bar Chart"),
            ('hbar', "Horizontal Bar Chart"),
            ('stacked_bar', "Stacked Bar Chart"),
            ('line', "Line Chart"),
            ('area', "Area Chart"),
            ('pie', "Pie Chart"),
            ('doughnut', "Doughnut Chart"),
            ('polar', "Polar Area Chart"),
            ('radar', "Radar Chart"),
            ('table', "Ranking Table"),
            ('pivot', "Pivot Table"),
            ('record_list', "Record List"),
            ('view', "Odoo View"),
            ('text', "Text"),
        ],
        string="Type", required=True, default='tile',
    )
    model_id = fields.Many2one(
        'ir.model', string="Model", ondelete='cascade',
        domain=[('transient', '=', False), ('abstract', '=', False)],
    )
    model_name = fields.Char(related='model_id.model', store=True, string="Model Name")
    domain = fields.Char(default='[]', help="Only the records matching this domain are used.")
    aggregate = fields.Selection(
        [
            ('count', "Count"),
            ('sum', "Sum"),
            ('avg', "Average"),
            ('min', "Minimum"),
            ('max', "Maximum"),
        ],
        required=True, default='count',
    )
    measure_field_id = fields.Many2one(
        'ir.model.fields', string="Measure", ondelete='cascade',
        domain="[('model_id', '=', model_id), ('store', '=', True), ('ttype', 'in', %s)]" % NUMERIC_FIELD_TYPES,
    )
    group_by_field_id = fields.Many2one(
        'ir.model.fields', string="Group By", ondelete='cascade',
        domain="[('model_id', '=', model_id), ('store', '=', True), ('ttype', 'in', %s)]" % GROUPABLE_FIELD_TYPES,
    )
    sub_group_by_field_id = fields.Many2one(
        'ir.model.fields', string="Then Group By", ondelete='cascade',
        domain="[('model_id', '=', model_id), ('store', '=', True), ('ttype', 'in', %s)]" % GROUPABLE_FIELD_TYPES,
        help="Splits each group into one series per value (stacked bars, pivot columns, multiple lines...).",
    )
    group_by_field_type = fields.Selection(related='group_by_field_id.ttype', string="Group By Type")
    date_granularity = fields.Selection(
        [
            ('day', "Day"),
            ('week', "Week"),
            ('month', "Month"),
            ('quarter', "Quarter"),
            ('year', "Year"),
        ],
        default='month',
    )
    group_limit = fields.Integer(
        string="Limit", default=10, help="Maximum number of groups or records displayed. 0 means no limit.",
    )
    target_value = fields.Float(string="Target", help="Goal reached at 100% by progress bars and gauges.")
    list_field_ids = fields.Many2many(
        'ir.model.fields', string="Columns",
        domain="[('model_id', '=', model_id), ('ttype', 'not in', "
               "['one2many', 'many2many', 'binary', 'html', 'json', 'properties', 'properties_definition'])]",
    )
    order_field_id = fields.Many2one(
        'ir.model.fields', string="Order By", ondelete='set null',
        domain="[('model_id', '=', model_id), ('store', '=', True)]",
    )
    order_desc = fields.Boolean(string="Descending", default=True)
    view_mode = fields.Selection(
        [
            ('list', "List"),
            ('kanban', "Kanban"),
            ('graph', "Graph"),
            ('pivot', "Pivot"),
            ('calendar', "Calendar"),
        ],
        default='list',
    )
    text_content = fields.Text(string="Text")
    width = fields.Selection(
        [
            ('3', "Quarter"),
            ('4', "Third"),
            ('6', "Half"),
            ('8', "Two Thirds"),
            ('12', "Full Width"),
        ],
        required=True, default='4',
    )
    color = fields.Char(default='#714B67', help="Main color of the block (hexadecimal).")
    icon = fields.Char(default='tag', help="Material Symbols icon shown on KPI tiles, e.g. payments.")

    _group_limit_positive = models.Constraint('CHECK (group_limit >= 0)', "The limit cannot be negative.")

    @api.depends('model_id', 'block_type', 'aggregate', 'measure_field_id', 'group_by_field_id')
    def _compute_name(self):
        for block in self:
            if block.block_type in STATIC_BLOCK_TYPES:
                block.name = block.name or self.env._("Text")
                continue
            if not block.model_id:
                block.name = block.name or self.env._("New Block")
                continue
            if block.block_type in ('record_list', 'view'):
                block.name = block.model_id.name
                continue
            field = block.measure_field_id.field_description
            if block.aggregate == 'count' or not field:
                name = self.env._("%s Count", block.model_id.name)
            elif block.aggregate == 'sum':
                name = self.env._("Total %s", field)
            elif block.aggregate == 'avg':
                name = self.env._("Average %s", field)
            elif block.aggregate == 'min':
                name = self.env._("Minimum %s", field)
            else:
                name = self.env._("Maximum %s", field)
            if block.block_type in GROUPED_BLOCK_TYPES and block.group_by_field_id:
                name = self.env._(
                    "%(measure)s by %(group)s", measure=name, group=block.group_by_field_id.field_description,
                )
            block.name = name

    @api.constrains('model_id', 'measure_field_id', 'group_by_field_id', 'sub_group_by_field_id', 'order_field_id')
    def _check_fields_model(self):
        for block in self:
            fields_ = block.measure_field_id | block.group_by_field_id | block.sub_group_by_field_id
            for field in fields_ | block.order_field_id:
                if field.model_id != block.model_id:
                    raise ValidationError(self.env._(
                        "Field %(field)s does not belong to model %(model)s.",
                        field=field.field_description, model=block.model_id.name,
                    ))

    @api.constrains('block_type', 'model_id', 'aggregate', 'measure_field_id', 'group_by_field_id',
                    'sub_group_by_field_id')
    def _check_configuration(self):
        for block in self:
            if error := block._get_configuration_error():
                raise ValidationError(error)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.measure_field_id = False
        self.group_by_field_id = False
        self.sub_group_by_field_id = False
        self.order_field_id = False
        self.list_field_ids = False
        self.domain = '[]'

    def _get_configuration_error(self):
        """ Return why the block cannot be computed, or False. """
        self.ensure_one()
        if self.block_type in STATIC_BLOCK_TYPES:
            return False
        if not self.model_id:
            return self.env._("Block %s needs a model.", self.name)
        if self.block_type in ('record_list', 'view'):
            return False
        if self.aggregate != 'count' and not self.measure_field_id:
            return self.env._("Block %s needs a measure for this aggregate.", self.name)
        if self.block_type in GROUPED_BLOCK_TYPES and not self.group_by_field_id:
            return self.env._("Block %s needs a field to group by.", self.name)
        if self.block_type in SUB_GROUPED_BLOCK_TYPES and not self.sub_group_by_field_id:
            return self.env._("Block %s needs a second field to group by.", self.name)
        return False

    # ------------------------------------------------------------
    # Builder configuration
    # ------------------------------------------------------------

    def _get_block_config(self):
        """ Return the block as edited by the dashboard builder, fields given by name. """
        self.ensure_one()
        block = self.sudo()
        config = {fname: block[fname] for fname in CONFIG_FIELDS}
        config.update({
            'id': self._origin.id or False,
            'model': block.model_name or False,
            'model_label': block.model_id.name or '',
            'width': int(block.width),
            'domain': block.domain or '[]',
            'text_content': block.text_content or '',
            'list_fields': block.list_field_ids.mapped('name'),
            **{key: block[fname].name or False for key, fname in CONFIG_FIELD_REFS.items()},
        })
        return config

    @api.model
    def _config_to_vals(self, config):
        """ Convert a builder configuration (see _get_block_config) to field values. """
        IrModelFields = self.env['ir.model.fields'].sudo()
        model_name = config.get('model') or False
        vals = {fname: config[fname] for fname in CONFIG_FIELDS if fname in config}
        if 'width' in vals:
            vals['width'] = str(vals['width'])
        vals['model_id'] = model_name and self.env['ir.model']._get_id(model_name)
        for key, fname in CONFIG_FIELD_REFS.items():
            field_name = model_name and config.get(key)
            vals[fname] = field_name and IrModelFields._get(model_name, field_name).id
        list_fields = (model_name and config.get('list_fields')) or []
        vals['list_field_ids'] = [(6, 0, [IrModelFields._get(model_name, name).id for name in list_fields])]
        return vals

    @api.model
    def preview_block(self, config):
        """ Compute the data of a block being configured in the builder, without saving it. """
        self.check_access('create')
        block = self.new(self._config_to_vals(config))
        return block._get_block_data()

    # ------------------------------------------------------------
    # Data computation
    # ------------------------------------------------------------

    def _get_domain(self):
        self.ensure_one()
        eval_context = {
            'uid': self.env.uid,
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
            'context_today': lambda: fields.Date.context_today(self),
        }
        return Domain(safe_eval.safe_eval(self.domain or '[]', eval_context))

    def _get_aggregate_spec(self):
        self.ensure_one()
        if self.aggregate == 'count':
            return '__count'
        return f'{self.measure_field_id.name}:{self.aggregate}'

    def _get_group_by_spec(self, field):
        self.ensure_one()
        if field.ttype in ('date', 'datetime'):
            return f'{field.name}:{self.date_granularity or "month"}'
        return field.name

    def _get_measure_label(self):
        self.ensure_one()
        if self.aggregate == 'count' or not self.measure_field_id:
            return self.env._("Count")
        return self.measure_field_id.field_description

    def _format_group_label(self, field, value):
        if isinstance(value, (list, tuple)):
            return value[1]
        if field.type == 'selection':
            return dict(field._description_selection(self.env)).get(value, value)
        if field.type == 'boolean':
            return self.env._("Yes") if value else self.env._("No")
        if value is False or value is None:
            return self.env._("None")
        return str(value)

    def _format_record_value(self, field, value):
        if field.type == 'many2one':
            return value.display_name or ''
        if field.type == 'boolean':
            return self.env._("Yes") if value else self.env._("No")
        if value is False or value is None:
            return ''
        if field.type == 'selection':
            return dict(field._description_selection(self.env)).get(value, value)
        if field.type == 'date':
            return format_date(self.env, value)
        if field.type == 'datetime':
            return format_datetime(self.env, value)
        if field.type in ('float', 'monetary'):
            return formatLang(self.env, value)
        return str(value)

    def get_block_data_filtered(self, filter_domain=None):
        """ Compute the block with the filters chosen by its viewer.

        :param list filter_domain: domain combined with the block's own domain
        """
        self.ensure_one()
        # _get_block_data reads the configuration as superuser: check the viewer first
        self.check_access('read')
        return self._get_block_data(extra_domain=filter_domain)

    def get_ai_analysis(self, filter_domain=None, filter_summary=''):
        """ Brief analysis of the block by Odoo's AI service, on the data its viewer sees.

        :param list filter_domain: the filters of the viewer, see ``get_block_data_filtered``
        :param str filter_summary: description of these filters, given to the AI as context
        :return: ``{'analysis': str}``
        """
        self.ensure_one()
        self.check_access('read')
        return self.env['dynamic.dashboard.ai.generator']._analyze_block(
            self, filter_domain=filter_domain, filter_summary=filter_summary,
        )

    def _get_block_data(self, extra_domain=None):
        """ Return the configuration and the computed values of the block. The aggregation
        runs with the rights of the current user, so a block never shows data its viewer
        cannot read.

        :param list extra_domain: optional domain restricting the records further
        """
        self.ensure_one()
        # field metadata is read as superuser: viewers of a dashboard opened from a menu
        # may not be dashboard users. The computation below still runs as the viewer.
        block = self.sudo()
        data = block._get_block_config()
        data.update({'measure_label': block._get_measure_label(), 'error': False})
        if error := block._get_configuration_error():
            data['error'] = error
            return data
        if self.block_type in STATIC_BLOCK_TYPES:
            return data
        if self.model_name not in self.env:
            data['error'] = self.env._("Model %s is not available.", self.model_name)
            return data
        Model = self.env[self.model_name]
        try:
            domain = self._get_domain()
            if extra_domain:
                domain &= Domain(extra_domain)
            data['record_domain'] = list(domain)
            if self.block_type == 'view':
                Model.check_access('read')
            elif self.block_type == 'record_list':
                data.update(block._compute_record_list(Model, domain))
            elif self.block_type in VALUE_BLOCK_TYPES:
                [[value]] = Model._read_group(domain, aggregates=[block._get_aggregate_spec()])
                data['value'] = value or 0
            else:
                data.update(block._compute_series(Model, domain))
        except AccessError:
            data['error'] = self.env._("You are not allowed to access this data.")
        except (ValueError, SyntaxError, NameError, KeyError, TypeError, UserError) as e:
            _logger.info("Dynamic dashboard block %s could not be computed: %s", self._origin.id, e)
            data['error'] = self.env._("This block is misconfigured: %s", e)
        return data

    def _compute_series(self, Model, domain):
        """ Group the records by the group by (the labels) and, for multi-series blocks, by
        the second group by (one series per value). """
        aggregate_spec = self._get_aggregate_spec()
        group_by_spec = self._get_group_by_spec(self.group_by_field_id)
        group_field = Model._fields[self.group_by_field_id.name]
        is_temporal = self.group_by_field_id.ttype in ('date', 'datetime')
        groups = Model.formatted_read_group(
            domain, [group_by_spec], [aggregate_spec],
            limit=self.group_limit or None,
            order=group_by_spec if is_temporal else f'{aggregate_spec} desc',
        )
        labels = [self._format_group_label(group_field, group[group_by_spec]) for group in groups]
        label_domains = [list(domain & Domain(group['__extra_domain'])) for group in groups]
        if not (self.sub_group_by_field_id and self.block_type in MULTI_SERIES_BLOCK_TYPES):
            return {
                'labels': labels,
                'label_domains': label_domains,
                'series': [{
                    'label': self._get_measure_label(),
                    'values': [group[aggregate_spec] or 0 for group in groups],
                    'domains': label_domains,
                }],
            }

        sub_group_by_spec = self._get_group_by_spec(self.sub_group_by_field_id)
        sub_field = Model._fields[self.sub_group_by_field_id.name]
        label_indexes = {repr(group[group_by_spec]): index for index, group in enumerate(groups)}
        sub_groups = Model.formatted_read_group(
            domain, [group_by_spec, sub_group_by_spec], [aggregate_spec], order=sub_group_by_spec,
        )
        series = {}
        for sub_group in sub_groups:
            index = label_indexes.get(repr(sub_group[group_by_spec]))
            if index is None:
                continue
            serie = series.setdefault(repr(sub_group[sub_group_by_spec]), {
                'label': self._format_group_label(sub_field, sub_group[sub_group_by_spec]),
                'values': [0] * len(groups),
                'domains': list(label_domains),
                'total': 0,
            })
            value = sub_group[aggregate_spec] or 0
            serie['values'][index] = value
            serie['domains'][index] = list(domain & Domain(sub_group['__extra_domain']))
            serie['total'] += value
        series = sorted(series.values(), key=lambda serie: serie.pop('total'), reverse=True)[:MAX_SERIES]
        return {'labels': labels, 'label_domains': label_domains, 'series': series}

    def _compute_record_list(self, Model, domain):
        field_names = [name for name in self.list_field_ids.mapped('name') if name in Model._fields]
        field_names = field_names or ['display_name']
        order = None
        if self.order_field_id.name in Model._fields:
            order = f'{self.order_field_id.name} {"desc" if self.order_desc else "asc"}'
        records = Model.search(domain, limit=self.group_limit or None, order=order)
        return {
            'columns': [
                {
                    'name': name,
                    'label': Model._fields[name]._description_string(self.env),
                    'numeric': Model._fields[name].type in NUMERIC_FIELD_TYPES,
                }
                for name in field_names
            ],
            'rows': [
                {
                    'id': record.id,
                    'values': [self._format_record_value(Model._fields[name], record[name]) for name in field_names],
                }
                for record in records
            ],
        }
