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


class MergeTickets(models.Model):
    """Tickets merging class
       This class allows users to merge support tickets or create new ones.
    It provides functionality to consolidate information from multiple tickets.
    """
    _name = 'merge.tickets'
    _description = 'Merge Tickets'
    _rec_name = 'support_ticket_id'

    user_id = fields.Many2one('res.partner',
                              string='Responsible User',
                              help='Responsible user name',
                              default=lambda self: self.env.user.partner_id.id)
    support_team_id = fields.Many2one('help.team',
                                      string='Support Team',
                                      help='Support Team Name')
    customer_id = fields.Many2one('res.partner',
                                  string='Customer',
                                  help='Customer Name'
                                  )
    support_ticket_id = fields.Many2one('help.ticket',
                                        string='Support Ticket')
    new_ticket = fields.Boolean(string='Create New Ticket ?',
                                help='Creating new tickets or not.',
                                )
    subject = fields.Char(string='Subject', help='Enter the New Ticket Subject')
    merge_reason = fields.Char(string='Merge Reason', help='Merging Reason')
    support_ticket_ids = fields.One2many('support.tickets',
                                         'support_ticket_id',
                                         string='Support Tickets',
                                         helps='Merged tickets')
    active = fields.Boolean(string='Disable Record', help='Disable Record')

    def default_get(self, fields_list):
        """It handles to get the default pre-filled the values """
        defaults = super().default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        selected_tickets = self.env['help.ticket'].browse(active_ids)
        customer_ids = selected_tickets.mapped('customer_id')
        subjects = selected_tickets.mapped('subject')
        display_names = selected_tickets.mapped('display_name')
        helpdesk_team = selected_tickets.mapped('team_id')
        descriptions = selected_tickets.mapped('description')
        # Ensure both selected records have the same customer
        if len(customer_ids):
            defaults.update({
                'customer_id': customer_ids[0].id,
                'support_team_id': helpdesk_team,

                'support_ticket_ids': [(0, 0, {
                    'subject': subject,
                    'display_name': display_name,
                    'description': description,

                }) for subject, display_name, description in
                                       zip(subjects, display_names,
                                           descriptions)]
            })
        return defaults

    def action_merge_ticket(self):
        """Merging the tickets or creating new tickets"""
        if self.new_ticket:
            description = "\n\n".join(
                f"{ticket.subject}\n{'-' * len(ticket.subject)}\n"
                f"{ticket.description}"
                for ticket in self.support_ticket_ids
            )
            self.env['help.ticket'].create({
                'subject': self.subject,
                'description': description,
                'customer_id': self.customer_id.id,
                'team_id': self.support_team_id.id,
            })
        else:
            if len(self.support_ticket_ids):
                description = "\n\n".join(
                    f"{ticket.subject}\n{'-' * len(ticket.subject)}\n"
                    f"{ticket.description}"
                    for ticket in self.support_ticket_ids
                )
                # Update the existing support_ticket with the combined
                # Information
                self.support_ticket_id.write({
                    'description': description,
                    'merge_ticket_invisible': True,
                    'merge_count': len(self.support_ticket_ids),
                })

    @api.onchange('support_ticket_id')
    def _onchange_support_ticket_id(self):
        """Onchange function to add the support ticket id."""
        self.support_ticket_ids.write({
            'merged_ticket': self.support_ticket_id
        })
