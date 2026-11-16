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
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.sql import table_exists

#: Field types that can be used as a display name.
ALLOWED_FIELD_TYPES = [
    'char', 'text', 'integer', 'float', 'monetary', 'selection',
    'date', 'datetime', 'many2one',
]
#: Models whose display name must never be changed, otherwise the
#: configuration screen itself would become unreadable.
EXCLUDED_MODELS = ['rec.name.config', 'ir.model', 'ir.model.fields']


class RecNameConfig(models.Model):
    """Store the field used as the display name (rec_name) of a model.

    One active configuration per model. When a configuration exists, the
    display name of every record of that model is taken from the chosen
    field instead of the model's default ``_rec_name``.
    """
    _name = 'rec.name.config'
    _description = 'Rec Name Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        comodel_name='ir.model',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False),
                ('model', 'not in', EXCLUDED_MODELS)],
        help='The model whose display name field you want to change.',
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Technical Model Name',
        store=True,
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Display Field',
        required=True,
        ondelete='cascade',
        domain="[('model_id', '=', model_id),"
               " ('ttype', 'in', %s),"
               " ('groups', '=', False)]" % ALLOWED_FIELD_TYPES,
        help='The field whose value will be shown as the record display '
             'name. Fields restricted to specific user groups cannot be '
             'used, as the display name is visible to every user.',
    )
    field_name = fields.Char(
        related='field_id.name',
        string='Technical Field Name',
        store=True,
    )
    field_ttype = fields.Selection(
        related='field_id.ttype',
        string='Field Type',
        store=True,
    )
    active = fields.Boolean(
        default=True,
        help='Uncheck to disable this configuration and revert to the '
             'default display name.',
    )

    _unique_model = models.Constraint(
        'UNIQUE(model_id)',
        'A rec name configuration already exists for this model.',
    )

    @api.constrains('model_id', 'field_id')
    def _check_field_belongs_to_model(self):
        """Ensure the selected field belongs to the chosen model and type."""
        for rec in self:
            if rec.model_id.model in EXCLUDED_MODELS:
                raise ValidationError(self.env._(
                    'The display name of model "%(model)s" cannot be '
                    'changed.', model=rec.model_id.name))
            if rec.field_id.model_id != rec.model_id:
                raise ValidationError(self.env._(
                    'The field "%(field)s" does not belong to model '
                    '"%(model)s".',
                    field=rec.field_id.name, model=rec.model_id.name))
            if rec.field_id.ttype not in ALLOWED_FIELD_TYPES:
                raise ValidationError(self.env._(
                    'Fields of type "%(ttype)s" cannot be used as a '
                    'display name.', ttype=rec.field_id.ttype))
            if rec.field_id.groups or rec._is_group_restricted_field():
                raise ValidationError(self.env._(
                    'The field "%(field)s" is restricted to specific user '
                    'groups and cannot be used as a display name, because '
                    'the display name is visible to every user.',
                    field=rec.field_id.name))

    def _is_group_restricted_field(self):
        """Return whether the selected field is declared with ``groups=``
        on its model, i.e. its value is hidden from some users."""
        self.ensure_one()
        model = self.env.get(self.model_id.model)
        if model is None:
            return False
        field = model._fields.get(self.field_id.name)
        return bool(field and field.groups)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Clear the field selection when the model changes."""
        if self.field_id.model_id != self.model_id:
            self.field_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Reset the configuration cache after creating configurations."""
        records = super().create(vals_list)
        self.env.transaction.invalidate_ormcache()
        return records

    def write(self, vals):
        """Reset the configuration cache after updating configurations."""
        result = super().write(vals)
        self.env.transaction.invalidate_ormcache()
        return result

    def unlink(self):
        """Reset the configuration cache after deleting configurations."""
        result = super().unlink()
        self.env.transaction.invalidate_ormcache()
        return result

    @api.model
    @api.ormcache()
    def _get_active_configs(self):
        """Return ``{model_name: (field_name, field_type)}`` for every
        active configuration.

        The result is cached in the registry, so the database is only
        queried again after a configuration changes. The cache is shared by
        all workers through the registry signaling mechanism.
        """
        if not table_exists(self.env.cr, self._table):
            # The module is being installed or uninstalled.
            return {}
        configs = self.sudo().with_context(active_test=True).search_fetch(
            [], ['model_name', 'field_name', 'field_ttype'])
        return {
            config.model_name: (config.field_name, config.field_ttype)
            for config in configs
        }
