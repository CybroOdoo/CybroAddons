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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


class OdooOcrAiConfig(models.Model):
    """Manage OCR AI model configurations."""
    _name = 'odoo.ocr.ai.config'
    _description = 'OCR AI Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        domain=[('is_ocr_tus', '=', True)],
        help='The Odoo model this configuration applies to. Only models '
             'flagged as OCR-enabled appear here.',
    )
    model_ids = fields.One2many(
        comodel_name='odoo.ocr.ai.config.line',
        inverse_name='model_id',
        string='Field Mapping',
        help='List of AI field titles mapped to Odoo fields. This mapping '
             'tells the OCR service which entities to extract and where to '
             'store each value on the created record.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Only one active configuration is allowed per model. '
             'Uncheck to disable this configuration without deleting it.',
    )
    create_products_if_not_found = fields.Boolean(
        string='Create Products if Not Found?',
        help='Auto-create products in Odoo when they are not found during line-item mapping.',
    )

    @api.constrains('model_id', 'active')
    def _check_unique_active_model(self):
        """Ensure only one active configuration exists per model."""
        for rec in self:
            if rec.active and rec.model_id:
                if self.search_count([
                    ('model_id', '=', rec.model_id.id),
                    ('active', '=', True),
                    ('id', '!=', rec.id),
                ]):
                    raise ValidationError(_(
                        'An active OCR configuration for model "%s" already exists.'
                    ) % rec.model_id.name)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Clear field mapping lines when the model changes."""
        if self._origin and self.model_id != self._origin.model_id:
            self.model_ids = [(5, 0, 0)]