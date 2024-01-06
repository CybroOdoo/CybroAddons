# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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


class PosConfig(models.Model):
    """Inherit the model res config settings"""
    _inherit = 'pos.config'

    reservation_charge = fields.Boolean(string="Reservation Charge",
                                        help="Payment for pre booking tables",
                                        config_parameter="table_"
                                                         "reservation_on_"
                                                         "website.reservation"
                                                         "_charge")
    refund = fields.Text(string="No Refund Notes", help="No refund notes to "
                                                        "display in website",
                         config_parameter="table_reservation_on_website.refund")
