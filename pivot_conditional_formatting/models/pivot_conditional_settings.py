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
"""Models for setting conditional formatting rules in settings"""
from odoo import api, fields, models


class PivotConditionalSetting(models.Model):
    """Model Class for choosing the model and view to set the default rules"""
    _name = 'pivot.conditional.settings'
    _description = 'Pivot conditional setting'
    _rec_name = "model_id"

    model_id = fields.Many2one('ir.model', string="Model",
                               help="The model to set the rules for")
    view_id = fields.Many2one('ir.ui.view', string="View",
                              help="Pivot view of the model")
    rules_ids = fields.One2many('conditional.rules',
                                'conditional_id', string="Rules",
                            help="List View Showing details of different rules")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Company id related to the Pivot "
                                      "Condition setting")
    view_id_domain = fields.Binary(string="View Domain",
                                   compute="_compute_view_id_domain")


    @api.depends('model_id')
    def _compute_view_id_domain(self):
        """
            This method is called when the 'model_id' field is changed. It
            updates the domain of the 'view_id' field to filter records based
             on the selected model and view type as 'pivot'.

            :return: Dictionary containing the updated domain for the 'view_id'
                     field.
            :rtype: dict
        """
        for rec in self:
            rec.view_id_domain = [('model', '=', rec.model_id.model),
                                  ('type', '=', 'pivot')]
