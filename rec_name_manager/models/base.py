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
from odoo import api, models
from odoo.fields import Domain
from odoo.tools import format_amount, format_date, format_datetime, formatLang

from .rec_name_config import ALLOWED_FIELD_TYPES, EXCLUDED_MODELS

#: Field types on which a text search can be done for ``name_search``.
SEARCHABLE_FIELD_TYPES = ('char', 'text', 'selection', 'many2one')


class Base(models.AbstractModel):
    """Use the configured field as the display name of every model."""
    _inherit = 'base'

    def _get_rec_name_config(self):
        """Return ``(field_name, field_type)`` configured for this model,
        or ``None`` when the model keeps its default display name."""
        if self._name in EXCLUDED_MODELS:
            return None
        config = self.env['rec.name.config']._get_active_configs().get(
            self._name)
        # The field may have disappeared, e.g. when the module defining it
        # was uninstalled after the configuration was saved. A field
        # restricted to some user groups is never exposed through the
        # display name, which every user can read.
        field = config and self._fields.get(config[0])
        if field and not field.groups and field.type in ALLOWED_FIELD_TYPES:
            return config
        return None

    def _compute_field_value(self, field):
        """Replace the computed display name by the configured field value.

        Falls back to the default display name when the configured field is
        empty on a record.
        """
        super()._compute_field_value(field)
        if field.name != 'display_name':
            return
        config = self._get_rec_name_config()
        if not config:
            return
        field_name = config[0]
        for record in self:
            value = record[field_name]
            if value:
                record.display_name = record._format_rec_name_value(
                    field_name, value)

    def _format_rec_name_value(self, field_name, value):
        """Return ``value`` of ``field_name`` formatted as the user sees it
        in the interface, i.e. in the user's language, timezone and
        currency."""
        self.ensure_one()
        field = self._fields[field_name]
        env = self.env
        if field.type == 'selection':
            return field.convert_to_export(value, self)
        if field.type == 'many2one':
            return value.display_name
        if field.type == 'date':
            return format_date(env, value)
        if field.type == 'datetime':
            return format_datetime(env, value, tz=env.context.get('tz'))
        if field.type == 'monetary':
            currency_field = field.get_currency_field(self)
            currency = currency_field and self[currency_field]
            if currency:
                return format_amount(env, value, currency)
            return formatLang(env, value)
        if field.type == 'float':
            digits = field.get_digits(env)
            return formatLang(env, value, digits=digits[1] if digits else 2)
        if field.type == 'integer':
            return formatLang(env, value, digits=0)
        return field.convert_to_display_name(value, self)

    def write(self, vals):
        """Refresh the display name when a configuration exists, so that a
        change of the chosen field, including a computed or related one, is
        shown immediately."""
        result = super().write(vals)
        if self._get_rec_name_config():
            self.invalidate_recordset(['display_name'])
        return result

    @api.model
    @api.readonly
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Also match the configured field when searching by name, so that
        a many2one dropdown finds records by the value it displays."""
        config = self._get_rec_name_config()
        if (not config or not name or config[1] not in SEARCHABLE_FIELD_TYPES
                or operator in Domain.NEGATIVE_OPERATORS):
            return super().name_search(name, domain, operator, limit)
        field_name, field_type = config
        if not self._fields[field_name]._description_searchable:
            return super().name_search(name, domain, operator, limit)
        path = (f'{field_name}.display_name' if field_type == 'many2one'
                else field_name)
        search_domain = (
            (Domain(path, operator, name)
             | Domain('display_name', operator, name))
            & Domain(domain or Domain.TRUE)
        )
        records = self.search_fetch(search_domain, ['display_name'],
                                    limit=limit)
        return [(record.id, record.display_name) for record in records.sudo()]
