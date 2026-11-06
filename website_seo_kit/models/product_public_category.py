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
from odoo import fields, models


class SeoPublicCategory(models.Model):
    """Here user can include category by enabling is_auto_seo field"""
    _inherit = 'product.public.category'

    is_auto_seo = fields.Boolean(string="Auto Update SEO",
                                 help='enable for generate seo content '
                                      'automatically for this category')
    category_description = fields.Text(string='Description For This Category',
                                       help='Description For This Category in Seo')
