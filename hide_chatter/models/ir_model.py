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
from ast import literal_eval
from odoo import api, models


class IrModel(models.Model):
    """Extend 'ir.model' to expose the models whose chatter must be hidden."""
    _inherit = 'ir.model'

    @api.model
    def get_hidden_chatter_models(self):
        """Return the technical names of the models whose chatter is hidden.

        The configuration is stored in a system parameter that only
        administrators may read, so the lookup is done with sudo. This keeps
        the client-side call working for every user regardless of access
        rights.
        """
        param = self.env['ir.config_parameter'].sudo().get_str(
            'hide_chatter.model_ids')
        model_ids = literal_eval(param) if param else []
        return self.sudo().browse(model_ids).mapped('model')
