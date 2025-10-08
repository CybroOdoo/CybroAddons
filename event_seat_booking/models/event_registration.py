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


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    row_number = fields.Char(string="Row Number", help="Row Number he booked",
                             readonly=True)
    column_number = fields.Char(string="Column Number",
                                help="Column Number he booked", readonly=True)
    unique_column_id = fields.Char(string="Unique Column Number",
                                   help="Column Number ID he booked",
                                   readonly=True)
    complete_name = fields.Char(string="Seat No",
                                compute='_compute_seat_name', store=True)

    @api.depends('row_number', 'column_number')
    def _compute_seat_name(self):
        """Compute the complete seat name based on row and column numbers."""
        for record in self:
            rec_name = f"R{record.row_number or ''} S{record.column_number or ''}"
            record.complete_name = rec_name.strip()

    def _get_website_registration_allowed_fields(self):
        """Get the fields allowed for website registration."""
        return {'name', 'phone', 'email', 'mobile', 'event_id', 'partner_id',
                'event_ticket_id', 'row_number', 'column_number',
                'unique_column_id'}

    def action_cancel(self):
        """Cancel the event registration and update the seat reservation
        status to 'available'."""

        res = super(EventRegistration,self).action_cancel()
        unique_column_id = self.unique_column_id
        seat_record = self.env[
            'seat.arrangement.line'].sudo().search([
            ('seat_manage_id.current_event_id', '=', self.event_ticket_id.id),
        ])
        if seat_record:
            column_record = seat_record.column_ids.filtered(
                lambda c: c.unique_seat_identifier == unique_column_id)
            column_record.write({'reservation_status': 'available'})
        return res

    def action_confirm(self):
        """Confirm the event registration and update the seat
         reservation status to 'booked'."""
        res = super(EventRegistration,self).action_confirm()
        unique_column_id = self.unique_column_id
        seat_record = self.env[
            'seat.arrangement.line'].sudo().search([
            ('seat_manage_id.current_event_id', '=', self.event_ticket_id.id),
        ])
        if seat_record:
            # for col in seat_record.column_ids:
            column_record = seat_record.column_ids.filtered(
                lambda c: c.unique_seat_identifier == unique_column_id)
            column_record.write({'reservation_status': 'booked'})

        return res
