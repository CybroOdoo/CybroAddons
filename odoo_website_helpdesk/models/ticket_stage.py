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
from odoo import fields, models, _
from odoo.exceptions import UserError


class TicketStage(models.Model):
    """This model represents the stages of a helpdesk ticket. A stage is used to
    indicate the current state of a ticket, such as 'New', 'In Progress',
    'Resolved', or 'Closed'. Stages are used to organize and track the
    progress of tickets throughout their lifecycle."""

    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'
    _fold_name = 'fold'

    name = fields.Char(string='Name', help='The name of the stage. This field'
                                           ' is used to identify the stage and'
                                           ' is displayed in various views '
                                           'and reports.')
    active = fields.Boolean(default=True,
                            string='Active',
                            help='Whether the stage is active or not. If this '
                                 'field is set to False,the stage will not be '
                                 'displayed in various views and reports.')
    sequence = fields.Integer(string='Sequence',
                              default=50,
                              help='The sequence number of the stage. This '
                                   'field is used to specify the order in which'
                                   ' the stages are displayed in various views '
                                   'and reports.', )
    closing_stage = fields.Boolean(string='Closing Stage',
                                   help='Whether the stage is a closing stage '
                                        'or not. A closing stage is a stage '
                                        'that indicates that the helpdesk '
                                        'ticket has been resolved or closed.'
                                        ' This field is used to identify the '
                                        'closing stage and is used in various '
                                        'calculations and reports.')
    cancel_stage = fields.Boolean(string='Cancel Stage',
                                  help='Whether the stage is a cancel stage '
                                       'or not. A cancel stage is a stage that'
                                       'indicate the helpdesk tickets has been '
                                       'cancelled or removed')
    starting_stage = fields.Boolean(string='Start Stage',
                                    help='Starting  ticket Stage')
    folded = fields.Boolean(string='Folded in Kanban',
                            help='Whether the stage is folded in the Kanban '
                                 'view or not. If this field is set to True,'
                                 ' the stage will be displayed in a collapsed '
                                 'state in the Kanban view, which can be '
                                 'expanded by clicking on it.This field is '
                                 'used to control the behavior of the '
                                 'Kanban view.')
    template_id = fields.Many2one('mail.template',
                                  string='Template',
                                  help='Choose the template',
                                  domain="[('model', '=', 'help.ticket')]")
    group_ids = fields.Many2many('res.groups',
                                 string='Group',
                                 help='Choose the group ID')
    fold = fields.Boolean(string='Fold', help='When enabling this the ticket '
                                              'stage will folded on the view')

    def unlink(self):
        """Deleting the helpdesk tickets from various stage."""
        for rec in self:
            tickets = rec.search([])
            sequence = tickets.mapped('sequence')
            lowest_sequence = tickets.filtered(
                lambda x: x.sequence == min(sequence))
            if self.name == "Draft":
                raise UserError(_("Cannot Delete This Stage"))
            if rec == lowest_sequence:
                raise UserError(_("Cannot Delete '%s'" % (rec.name)))
            else:
                res = super().unlink()
                return res
