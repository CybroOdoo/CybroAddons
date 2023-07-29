# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
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


class MemberSlotReservation(models.Model):
    """Details for MemberSlotReservation"""
    _name = 'member.slot.reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'slot_id'
    _description = 'Member Slot Reservation'

    slot_id = fields.Many2one('slot.details', string='Slot', tracking=True,
                              required=True,
                              help='Field for the ID of the slot')
    partner_id = fields.Many2one('res.partner', string='Member',
                                 tracking=True, required=True,
                                 help='Field for Reserved Member')
    start_date = fields.Date(string='Start Date', tracking=True,
                             required=True,
                             help='Field for adding the start date')
    end_date = fields.Date(string='End Date', tracking=True, required=True,
                           help='Field for adding end date')
