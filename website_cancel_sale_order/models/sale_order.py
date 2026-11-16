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
    """inherited sale order to add reason for cancel """
    _inherit = 'sale.order'

    cancellation_reason = fields.Text(string='Cancellation Reason',
                                      help='Here we can see the cancellation '
                                           'reason')
    is_cancel = fields.Boolean(string='Is Cancel',
                               help='This field is used to identify the '
                                    'cancelled order')
