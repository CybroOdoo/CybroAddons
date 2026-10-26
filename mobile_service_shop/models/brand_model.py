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


class BrandModel(models.Model):
    """This class represents a mobile brand model"""
    _name = 'brand.model'
    _description = 'Brand Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'mobile_brand_models'

    mobile_brand_name = fields.Many2one('mobile.brand',
                                        string="Mobile Brand", required=True,
                                        help="Brand name of the mobile")
    mobile_brand_models = fields.Char(string="Model Name", required=True,
                                      help="Model name of the mobile")
    image_medium = fields.Binary(string='Image', store=True, attachment=True,
                                 help="Mobile image space")
