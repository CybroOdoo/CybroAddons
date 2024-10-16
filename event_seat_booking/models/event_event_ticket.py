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


class EventEventTicket(models.Model):
    """Inheriting the module to add a field"""
    _inherit = 'event.event.ticket'

    total_row = fields.Integer(string="Total Row",
                               help='Total row used in this event.')
    sequence = fields.Integer(string='Sequence', help='Drag the records')
    seat_arrangement_id = fields.Many2one('seat.arrangement',
                                          string='Seat Arrangement Id',
                                          help='Seat arrangement model '
                                               'reference')

    def seat_arrangement_action(self):
        """Opening the seat arrangement model"""
        context = self.env.context
        default_seat_arrangement_id = context.get(
            'default_seat_arrangement_id',
            False)
        if default_seat_arrangement_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'seat.arrangement',
                'view_mode': 'form',
                'res_id': default_seat_arrangement_id,
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'seat.arrangement',
                'view_mode': 'form',
                'target': 'new',
            }
