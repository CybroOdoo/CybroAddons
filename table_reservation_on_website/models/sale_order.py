# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """ Inherit sale order for adding new fields """
    _inherit = 'sale.order'

    table_reservation_id = fields.Many2one(
        comodel_name='table.reservation',
        string="Table Reservation",
        help="Can view the table reservation", readonly=True)
    tables_ids = fields.Many2many("restaurant.table", string="tables",
                                  help="Booked Tables")
    floors = fields.Integer(string="Floor Number", help="Number of the Floor")
    date = fields.Date(string="Date", help="Date of reservation")
    starting_at = fields.Char(string="Starting At",
                              help="starting time of reservation")
    ending_at = fields.Char(string="Ending At",
                            help="Ending time of reservation")
    booking_amount = fields.Float(string="Booking Amount",
                                  help="Booking Charge")
