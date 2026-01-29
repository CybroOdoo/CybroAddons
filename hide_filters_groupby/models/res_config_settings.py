# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from ast import literal_eval
from odoo import fields, models


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
    ir_model_ids = fields.Many2many('ir.model',
                                    'res_config_ir_model_rel',
                                    'res_config', 'model',
                                    string='Models',
                                    help='Models that are affected by the '
                                         'hide filters and group by settings.')

    def set_values(self):
        """Update the values of the configuration settings"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'hide_filters_groupby.ir_model_ids', self.ir_model_ids.ids)
        return res

    def get_values(self):
        """Get the current values for the configuration settings"""
        res = super(ResConfigSettings, self).get_values()
        ir_model_ids = self.env['ir.config_parameter'].sudo().get_param(
            'hide_filters_groupby.ir_model_ids')
        res.update(
            ir_model_ids=literal_eval(ir_model_ids) if ir_model_ids else False)
        return res


