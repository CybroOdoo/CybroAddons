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
from odoo import api, fields, models
from odoo.exceptions import UserError


class TicketStage(models.Model):
    """Stage of the helpdesk tickets"""
    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'
    _fold_name = 'fold'

    name = fields.Char(required=True, translate=True,
                       help='Name of the ticket stage')
    active = fields.Boolean(default=True,
                            help='Archive the stage to hide it.')
    sequence = fields.Integer(default=50,
                              help='Sequence number of the ticket stage.')
    closing_stage = fields.Boolean(default=False,
                                   help='The tickets in this stage are '
                                        'closed.')
    cancel_stage = fields.Boolean(default=False,
                                  help='The tickets in this stage are '
                                       'canceled.')
    starting_stage = fields.Boolean('Start Stage', default=False,
                                    help='The work on the tickets starts in '
                                         'this stage.')
    template_id = fields.Many2one('mail.template',
                                  help='Email sent to the customer when a '
                                       'ticket enters the stage',
                                  string='Email Template',
                                  domain="[('model', '=', 'ticket.helpdesk')]")
    group_ids = fields.Many2many('res.groups', help='Groups working on the '
                                                    'tickets of the stage',
                                 string='Groups')
    fold = fields.Boolean(string='Folded in Kanban',
                          help='Fold the stage in the kanban view.')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_first_stage(self):
        """New tickets start in the first stage: it cannot be deleted"""
        first_stage = self.search([], limit=1)
        if first_stage & self:
            raise UserError(self.env._(
                'You cannot delete the stage "%s": new tickets start in it.',
                first_stage.name))
