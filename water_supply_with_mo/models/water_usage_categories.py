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


class WaterUsageCategories(models.Model):
    """Creating water usage categories."""
    _name = 'water.usage.categories'
    _description = 'Water Usage Categories'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'usage_category_name'

    code = fields.Char(string='Usage Category Code',
                       help='Usage category code', required=True)
    usage_category_name = fields.Char(string='Usage Category Name',
                                      help='Usage category name', required=True)
