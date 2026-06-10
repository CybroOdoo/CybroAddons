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
from odoo import models, fields
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """
        Extends Odoo's ResConfigSettings to allow administrators
        to configure the recommendation engine model.

        Fields:
            model_choice (Selection):
                Lets the user choose between:
                  - 'fast': High Speed (MiniLM)
                  - 'accurate': High Performance (Nomic)
    """
    _inherit = 'res.config.settings'

    model_choice = fields.Selection([
        ('fast', 'High Speed (MiniLM)'),
        ('accurate', 'High Performance (Nomic)')
    ], string="Recommendation Models", default='fast', config_parameter="product_recommendation_ai.model_choice")
    product_metadata = fields.Selection([
        ('name', 'Name'),
        ('name_categ', 'Name + Category '),
        ('name_description', 'Name + Description'),
        ('description', 'Description')
    ], default='description', config_parameter="product_recommendation_ai.product_metadata")
    recommendation_limit = fields.Integer(default=4, config_parameter="product_recommendation_ai.recommendation_limit")
    enable_recommendations = fields.Boolean(
        string="Enable Recommended Products",
        config_parameter='product_recommendation_ai.enable_recommendations',
    )
    nomic_token = fields.Char(string="Nomic Token", config_parameter="product_recommendation_ai.nomic_token")


    def execute(self):
        """
        Override the execute method to validate settings before saving.
        """
        for record in self:
            if record.model_choice == 'accurate' and not record.nomic_token:
                raise UserError(
                    "Configuration Error: You must provide a Nomic API Token "
                    "to use the High Performance (Nomic) model."
                )
        return super(ResConfigSettings, self).execute()
