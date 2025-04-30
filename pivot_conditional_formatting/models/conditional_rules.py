# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ConditionalRules(models.Model):
    """Model Class for the different Pivot view table, conditional formatting
    rules"""
    _name = 'conditional.rules'
    _description = 'Conditional formatting'
    _rec_name = "rule"

    rule = fields.Selection(string='Rule', selection=([
        ('greater_than', 'Greater than'), ('less_than', 'Less Than'),
        ('is_empty', 'Is Empty'), ('in_between', 'In Between')]),
                            help="Different conditions for rules")

    value = fields.Float(string='Value', help="Value for comparing the rule")
    second_value = fields.Float(string='Second Value', help="Second Value for "
                                                            "comparing the "
                                                            "inbetween rule")
    color = fields.Char(string='Color', required=True, help="Background "
                                                            "Color For the "
                                                            "Cells")
    text_color = fields.Char(string='Text Color',
                             required=True, help="Text "
                             "Color for the cells")
    model_id = fields.Many2one('ir.model', related='conditional_id.model_id',
                               help="model related to the rule",
                               string="Model")
    view_id = fields.Many2one('ir.ui.view', related='conditional_id.view_id',
                              help="view related to the rule", string="View")
    conditional_id = fields.Many2one('pivot.conditional.settings',
                                     help="Pivot Condition setting related to"
                                          " the rule", string="Condition")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Company id related to rule")
