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
from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class MergeTicket(models.Model):
    """Merge the selected tickets into one ticket"""
    _name = 'merge.ticket'
    _description = 'Merging the selected tickets'
    _rec_name = 'support_ticket_id'

    user_id = fields.Many2one('res.partner',
                              string='Responsible User',
                              help='User name of responsible person.',
                              default=lambda self: self.env.user.partner_id.id)
    support_team_id = fields.Many2one('team.helpdesk',
                                      help='Name of the support team.')
    customer_id = fields.Many2one('res.partner', help='Name of the Customer ')
    support_ticket_id = fields.Many2one('ticket.helpdesk',
                                        help="Ticket receiving the merged "
                                             "tickets")
    new_ticket = fields.Boolean(string='Create New Ticket ?',
                                help='Merge the tickets into a new ticket.',
                                default=False)
    subject = fields.Char(help='Enter the New Ticket Subject')
    merge_reason = fields.Char(help='Reason for Merging the tickets. ')
    support_ticket_ids = fields.One2many('support.ticket',
                                         'support_ticket_id',
                                         string='Support Tickets',
                                         help='Merged tickets')
    active = fields.Boolean(string='Disable Record', help='Disable Record',
                            default=True)

    @api.model
    def default_get(self, fields_list):
        """Fill the wizard with the tickets selected in the list"""
        defaults = super().default_get(fields_list)
        tickets = self.env['ticket.helpdesk'].browse(
            self.env.context.get('active_ids', []))
        if tickets:
            defaults.update({
                'customer_id': tickets.customer_id[:1].id,
                'support_team_id': tickets.team_id[:1].id,
                'support_ticket_ids': [Command.create({
                    'ticket_id': ticket.id,
                    'subject': ticket.subject,
                    'description': ticket.description,
                }) for ticket in tickets],
            })
        return defaults

    def action_merge_ticket(self):
        """Merge the tickets into the selected ticket or into a new ticket,
        and archive the merged tickets"""
        self.ensure_one()
        if not self.support_ticket_ids:
            raise UserError(self.env._('Select the tickets to merge.'))
        description = "\n\n".join(
            f"{line.subject}\n{'-' * len(line.subject or '')}\n"
            f"{line.description or ''}"
            for line in self.support_ticket_ids)
        if self.new_ticket:
            if not self.subject:
                raise UserError(self.env._('Enter the subject of the new '
                                           'ticket.'))
            target = self.env['ticket.helpdesk'].create({
                'subject': self.subject,
                'description': description,
                'customer_id': self.customer_id.id,
                'team_id': self.support_team_id.id,
            })
        else:
            if not self.support_ticket_id:
                raise UserError(self.env._('Select the ticket receiving the '
                                           'merged tickets.'))
            target = self.support_ticket_id
            target.description = description
        merged = self.support_ticket_ids.ticket_id - target
        self.support_ticket_ids.merged_ticket = target.id
        target.write({
            'merge_ticket_invisible': True,
            'merge_count': len(merged),
        })
        merged.action_archive()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ticket.helpdesk',
            'res_id': target.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
        }
