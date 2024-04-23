# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class AppointmentPrice(models.Model):
    """this is used to inherit the appointment.type model to add some custom
    fields"""
    _inherit = 'appointment.type'

    has_payment_step = fields.Boolean("Up-front Payment",
                                      help="Require visitors to pay to "
                                           "confirm their booking")
    product_id = fields.Many2one(
        'product.product', string="Product",
        help="Product configured for appointment booking",
        domain=[('detailed_type', '=', 'booking_fees')],
        readonly=False, store=True)
