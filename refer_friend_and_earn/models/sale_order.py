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


class SaleOrder(models.Model):
    """Inherited the module sale.order to add a field which shows how
        much points applied for sale order"""
    _inherit = 'sale.order'

    points_applied = fields.Float(string='Points Applied',
                                  help='Points applied to the corresponding '
                                       'sale order.')
    discount_applied = fields.Float(string='Discount Applied',
                                    help='The percentage of discount applied.')
