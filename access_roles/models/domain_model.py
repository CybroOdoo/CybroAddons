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


class DomainModel(models.Model):
    """Class for storing domain rules for models."""
    _name = 'domain.model'
    _description = 'Model Domain'

    name = fields.Text(string='Domain', default='[]', required=True)
    domain_model_name = fields.Char(string='Model Name', compute='_compute_domain_model_name', store=True)
    domain_model_id = fields.Many2one('ir.model', string='Model', domain="[('model', '!=', 'access.role')]")

    @api.depends('domain_model_id')
    def _compute_domain_model_name(self):
        """Computes the technical name of the selected model."""
        for record in self:
            record.domain_model_name = record.domain_model_id.model if record.domain_model_id else False

    @api.depends('domain_model_id', 'name')
    def _compute_display_name(self):
        for record in self:
            model_name = record.domain_model_id.name or record.domain_model_name or ''
            record.display_name = f"{model_name} ({record.name})" if model_name else (record.name or '')
