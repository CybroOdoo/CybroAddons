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
from odoo import fields, models


class SeatArrangementLine(models.Model):
    """Prepared seat based on the row and column count"""
    _name = 'seat.arrangement.line'
    _description = 'Seat Arrangement Line'

    row_no = fields.Integer(string='Row No', help='Enter the row Number.')
    column_ids = fields.Many2many('seat.column',
                                  string='Column Selection',
                                  help='Selected Columns.')
    seat_manage_id = fields.Many2one('seat.arrangement',
                                     string='Arrange seat',
                                     help='Seat arrangement co-model.')
    reservation_status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('booked', 'Booked'),
    ], string='Reservation Status', default='available')

    def action_delete_row(self):
        """Delete the current seat arrangement line."""
        skip_save = self.env.context.get('seat_arrangement_skip_save', False)
        self.unlink()
        if not skip_save:
            self.env.cr.commit()
