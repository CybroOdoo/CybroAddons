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


class SeatArrangement(models.Model):
    """This class handle to the seat arrangement details."""
    _name = 'seat.arrangement'
    _description = 'Seat Arrangement'

    event = fields.Char(string='Event', help='Current event name.',
                        readonly=True)
    ticket_type = fields.Char(string='Ticket Type',
                              help='Current event type.', readonly=True)
    total_row = fields.Integer(string='Total Row',
                               help='Enter total row of this ticket type '
                                    'in screen.')
    max_seat_single_row = fields.Integer(string='Max Seat Number in Single Row',
                                         help='Enter maximum number of seat in '
                                              'single row of particular this'
                                              ' ticket type.')
    prepare_seat_ids = fields.One2many('seat.arrangement.line',
                                       'seat_manage_id',
                                       string='Arranged Seat'
                                       )
    seats_max = fields.Integer(string="Maximum Attendees",
                               help='Define number of available tickets.')
    current_event_id = fields.Integer(string='Event ID',
                                      help='Get current event id.',
                                      readonly=True)

    def action_create_one_two_many_record(self):
        """Create seat records based on total_row and max_seat_single_row."""
        # Clear existing seat records before creating new ones
        if self.prepare_seat_ids:
            self.prepare_seat_ids.unlink()
        # Create seat.column records if they don't already exist
        if not self.env['seat.column'].search([]):
            for column_num in range(1, self.max_seat_single_row + 1):
                d = self.env['seat.column'].create({'column_no': column_num})
        row = 1
        while row <= self.total_row:
            seat_line_ids = []
            # Case 1: When both blank_row and blank_seat are not enabled
            for column_num in range(1, self.max_seat_single_row + 1):
                column_record = self.env['seat.column'].create(
                    {'column_no': column_num})
                seat_line_ids.append((4, column_record.id))
            # Create the seat arrangement line
            self.env['seat.arrangement.line'].create({
                'row_no': row,
                'column_ids': seat_line_ids if seat_line_ids else None,
                'seat_manage_id': self.id
            })
            row += 1
        cr = self.env.cr
        # updating the maximum seat
        query = f"""select count(seat_column_id) from seat_arrangement_line as a
                 join seat_arrangement_line_seat_column_rel as b on 
                 a.id=b.seat_arrangement_line_id join seat_arrangement as c on 
                 c.id=a.seat_manage_id where a.seat_manage_id = {self.id}"""
        cr.execute(query)
        seat_count = cr.fetchone()[0]
        self.seats_max = seat_count
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'seat.arrangement',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_clear_seat_arrangement(self):
        """Clear the entire seat arrangement."""
        self.prepare_seat_ids.unlink()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'seat.arrangement',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_save_record(self):
        """Save button to save the seat arrangement details"""
        event_ticket = self.env['event.event.ticket'].browse(
            self.current_event_id)
        if event_ticket:
            event_ticket.write({
                'total_row': self.total_row,
                'seats_max': self.seats_max,
                'seat_arrangement_id': self.id
            })
