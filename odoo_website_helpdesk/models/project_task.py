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
from odoo import fields, models


class ProjectTask(models.Model):
    """
    This class extends the 'project.task' model in Odoo to add a custom field
     called 'ticket_billed' and 'ticket_id'.
     ticket_billed: A boolean field indicating whether the ticket has
     been billed or not.
     ticket_id : A many2One field to link the task
    with a help ticket
    """
    _inherit = 'project.task'

    ticket_billed = fields.Boolean(string='Billed',
                                   help='Whether the Ticket has been Invoiced'
                                        'or Not')
    ticket_id = fields.Many2one('help.ticket', string='Ticket',
                                help='The help ticket associated with this '
                                     'recordThis field allows you to link '
                                     'this record to an existing help ticket.')
