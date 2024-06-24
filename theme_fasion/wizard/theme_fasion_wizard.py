# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ThemeFasionWizard(models.Model):
    """
    Model for theme settings wizard
    """
    _name = "theme.fasion.wizard"
    _description = "Theme Fasion Wizard"

    website_id = fields.Many2one('website', "Website",
                                 help="Select website", required=True)
    category_ids = fields.Many2many("product.public.category",
                                    string="Categories",
                                    help="Categories for Category snippet",
                                    related='website_id.category_ids',
                                    readonly=False)
    smart_clothing_ids = fields.One2many("smart.clothing",
                                         "theme_fasion_wizard_id",
                                         related="website_id.smart_clothing_ids",
                                         readonly=False,
                                         help="Smart clothing ids")
    insta_shopping_ids = fields.One2many("insta.shopping",
                                         "theme_fasion_wizard_id",
                                         related="website_id.insta_shopping_ids",
                                         readonly=False,
                                         help="Insta shopping ids")

    # Action Methods

    def action_confirm(self):
        """
        To save the values
        """
        self.website_id.update({
            'category_ids': [(fields.Command.link(
                i)) for i in self.category_ids.ids
            ],
            'smart_clothing_ids': [(fields.Command.link(
                i)) for i in self.smart_clothing_ids.ids
            ],
            'insta_shopping_ids': [(fields.Command.link(
                i)) for i in self.insta_shopping_ids.ids
            ],
        })
