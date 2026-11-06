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


class SupportTicket(models.Model):
    """Ticket selected in the merge wizard"""
    _name = 'support.ticket'
    _description = 'Support Tickets'
    _rec_name = 'subject'

    ticket_id = fields.Many2one('ticket.helpdesk', ondelete='cascade',
                                help='Ticket to merge')
    subject = fields.Char(help='Subject of the merged '
                                                 'tickets.')
    description = fields.Char(help='Description of the tickets.')
    support_ticket_id = fields.Many2one('merge.ticket',
                                        string='Support Tickets',
                                        ondelete='cascade',
                                        help='Support tickets')
    merged_ticket = fields.Integer(string='Merged Ticket ID',
                                   help='Storing merged ticket id')
