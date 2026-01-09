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
from odoo import api, fields, models


class ThemeFashion(models.AbstractModel):
    """Inherit the model theme.utils for adding new header file"""
    _inherit = 'theme.utils'

    def _theme_fasion_post_copy(self, mod):
        """For viewing default header"""
        self.enable_view(
            'theme_fasion.template_header_hamburger_oe_structure_header_fasions')
        self.disable_view('website.template_header_default')


class Website(models.Model):
    """
    To add a field in website model to save the values.
    """
    _inherit = 'website'

    category_ids = fields.Many2many('product.public.category',
                                    help="Category ids")
    smart_clothing_ids = fields.One2many("smart.clothing",
                                         "website_id",
                                         help="Smart clothing ids")
    insta_shopping_ids = fields.One2many("insta.shopping",
                                         "website_id",
                                         help="Insta shopping ids")


class SmartClothing(models.Model):
    """
    To create model for smart clothing
    """
    _name = 'smart.clothing'
    _description = "Smart Clothing"

    theme_fasion_wizard_id = fields.Many2one("theme.fasion.wizard",
                                             "Theme Fasion Wizard",
                                             help="Theme fasion wizard id")
    website_id = fields.Many2one("website", "Website",
                                 help="Website id")
    category_id = fields.Many2one("product.public.category",
                                  string="Category", help="Category id")
    product_ids = fields.Many2many("product.template",
                                   string="Products", help="Products")
    dynamic_category_id = fields.Integer(string="Dynamic Category",
                                         help="Dynamic category id")

    # Onchange Methods
    @api.onchange("category_id")
    def _onchange_category_id(self):
        """
        Used to make dynamic domain for product_ids
        """
        if self.category_id:
            self.dynamic_category_id = self.category_id.id


class InstaShopping(models.Model):
    """
    To create model for insta shopping
    """
    _name = 'insta.shopping'
    _description = "Insta Shopping"

    theme_fasion_wizard_id = fields.Many2one("theme.fasion.wizard",
                                             "Theme Fasion Wizard",
                                             help="Theme fasion wizard id")

    website_id = fields.Many2one("website", "Website",
                                 help="Website id")
    image_1920 = fields.Binary(string="Upload Image", help="Image")
    insta_link = fields.Char(string="Instagram Link", help="Instagram post link")
