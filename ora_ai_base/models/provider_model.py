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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProviderModel(models.Model):
    """AI model configurations provided by external AI service providers."""
    _name = "provider.model"
    _description = "Provider Model"

    name = fields.Char(string="Model Name",
                       help="Display name of the AI model")
    key = fields.Char(string="Model Key",
                      help="Technical identifier used when calling"
                           " the AI provider's API ")
    provider = fields.Char(help="The name of the AI service provider")

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.context.get('install_mode'):
            raise UserError(self.env._("AI Provider Models cannot be created manually."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.is_superuser() and not self.env.context.get('install_mode'):
            raise UserError(self.env._("AI Provider Models cannot be edited."))
        return super().write(vals)
