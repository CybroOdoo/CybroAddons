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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """
    Extend the 'res.config.settings' model to manage configuration settings for
    enabling/disabling the chatter feature.
    """
    _inherit = 'res.config.settings'

    model_ids = fields.Many2many('ir.model', string="Models",
                                 help="Choose the models to hide their "
                                      "chatter")

    def set_values(self):
        """
        Override the 'set_values' method to save the selected models as
        configuration parameters.
        """
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_str(
            'hide_chatter.model_ids', str(self.model_ids.ids))
        return res

    @api.model
    def get_values(self):
        """
        Override the 'get_values' method to retrieve the selected models from
        configuration parameters.
        """
        res = super().get_values()
        selected_models = self.env['ir.config_parameter'].sudo().get_str(
            'hide_chatter.model_ids')
        res.update(model_ids=[(6, 0, literal_eval(
            selected_models))] if selected_models else [(6, 0, [])])
        return res
