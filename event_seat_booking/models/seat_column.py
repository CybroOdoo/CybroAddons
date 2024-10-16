# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (<https://www.cybrosys.com>)
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


class SeatColumn(models.Model):
    """Column selection creation"""
    _name = 'seat.column'
    _description = 'Seat Column'
    _rec_name = 'column_no'

    unique_seat_identifier = fields.Char(string='Unique Seat Identifier',
                                         readonly=True)

    column_no = fields.Integer(string='Column Number',
                               help='Enter column number.')

    reservation_status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('booked', 'Booked'),
    ], string='Reservation Status', default='available')

    @api.model
    def create(self, vals):
        vals['unique_seat_identifier'] = self.env['ir.sequence'].next_by_code(
            'seat.column')
        return super(SeatColumn, self).create(vals)
