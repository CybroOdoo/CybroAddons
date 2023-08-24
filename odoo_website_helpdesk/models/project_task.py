# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    """Extends the 'project.task' model to add a Many2one field to link the task
    with a help ticket, and a boolean field to indicate whether the linked help
    ticket has been invoiced or not.
    """
    _inherit = 'project.task'

    ticket_id = fields.Many2one('help.ticket', string='Ticket',
                                help='The help ticket associated with this '
                                     'recordThis field allows you to link '
                                     'this record to an existing help ticket.')
    ticket_billed = fields.Boolean(string='Billed', default=False,
                                   help="Whether the Ticket has been Invoiced "
                                        "or Not")
