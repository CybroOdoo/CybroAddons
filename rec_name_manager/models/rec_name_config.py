# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RecNameConfig(models.Model):
    """
    Stores the user-chosen display field (rec_name) for any installed model.
    One record per model — if a config exists for a model, name_get() on that
    model will use the chosen field instead of the default _rec_name.
    """
    _name = 'rec.name.config'
    _description = 'Rec Name Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
        help='The model whose display name field you want to change.',
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Technical Model Name',
        store=True,
        readonly=True,
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Display Field',
        required=True,
        ondelete='cascade',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['char','text','integer','float','selection','date','datetime','many2one','boolean'])]",
        help='The field whose value will be shown as the record display name.',
    )
    field_name = fields.Char(
        related='field_id.name',
        string='Technical Field Name',
        store=True,
        readonly=True,
    )

    field_ttype = fields.Char(
        string='Field Type',
        compute='_compute_field_ttype',
        store=True,
        readonly=True,
    )

    @api.depends('field_id')
    def _compute_field_ttype(self):
        """Compute the selected field type."""
        for rec in self:
            ttype = rec.field_id.ttype if rec.field_id else False
            rec.field_ttype = ttype

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to disable this configuration and revert to the default rec_name.',
    )

    _sql_constraints = [
        ('unique_model', 'UNIQUE(model_id)', 'A rec name configuration already exists for this model.'),
    ]

    @api.constrains('model_id', 'field_id')
    def _check_field_belongs_to_model(self):
        """Ensure the selected field belongs to the chosen model."""
        for rec in self:
            if rec.field_id and rec.model_id:
                if rec.field_id.model_id != rec.model_id:
                    raise ValidationError(
                        f'The field "{rec.field_id.name}" does not belong to model "{rec.model_id.name}".'
                    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Clear field selection when model changes."""
        self.field_id = False
        if self.model_id:
            return {
                'domain': {
                    'field_id': [
                        ('model_id', '=', self.model_id.id),
                        ('ttype', 'in', [
                            'char', 'text', 'integer', 'float',
                            'selection', 'date', 'datetime',
                            'many2one', 'boolean',
                        ]),
                    ]
                }
            }