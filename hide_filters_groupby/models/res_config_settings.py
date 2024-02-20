# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.tools._monkeypatches import literal_eval


class ResConfigSettings(models.TransientModel):
    """Inheriting ResConfigSettings Model"""
    _inherit = 'res.config.settings'

    is_hide_filters_groupby_enabled = fields.Boolean(
        string='Hide Filters and Group By Enabled', default=False,
        config_parameter='hide_filters_groupby.is_hide_filters_groupby_enabled',
        help='If set to True, it enables hiding filters and group by globally.')
    hide_filters_groupby = fields.Selection(selection=[
        ('global', 'Globally'), ('custom', 'Custom'), ],
        string='Hide Filters and Group By', default='global',
        config_parameter='hide_filters_groupby.hide_filters_groupby',
        help='Choose the option to hide filters and group by globally or'
             ' use custom settings.')
    ir_model_ids = fields.Many2many(
        'ir.model',
        'res_config_ir_model_rel',
        'res_config', 'model',
        string='Models',
        readonly=False,
        help='Models that are affected by the '
             'hide filters and group by settings.')

    def set_values(self):
        """this function helps to save values in the settings
         inherited choose_product_ids field"""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'hide_filters_groupby.ir_model_ids',
            self.ir_model_ids.ids)
        return res

    @api.model
    def get_values(self):
        """this function retrieve the values from the ir_config_parameters"""
        res = super().get_values()
        model_ids = self.env['ir.config_parameter'].sudo().get_param(
            'hide_filters_groupby.ir_model_ids')
        res.update(
            ir_model_ids=[
                fields.Command.set(literal_eval(model_ids))
            ] if model_ids else False)
        return res
