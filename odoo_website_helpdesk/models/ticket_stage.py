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


class HelpDeskStage(models.Model):
    """
    This model represents the stages of a helpdesk ticket. A stage is used to
    indicate the current state of a ticket, such as 'New', 'In Progress',
    'Resolved', or 'Closed'. Stages are used to organize and track the
    progress of tickets throughout their lifecycle.
    """
    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'

    name = fields.Char(
        string='Name',
        help='The name of the stage. This field is used to identify the stage '
             'and is displayed in various views and reports.')
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether the stage is active or not. If this field is set to '
             'False,the stage will not be displayed in various views and '
             'reports.')
    sequence = fields.Integer(
        string='Sequence',
        default=50,
        help='The sequence number of the stage. This field is used to specify '
             'the order in which the stages are displayed'
             'in various views and reports.')
    closing_stage = fields.Boolean(
        string='Closing Stage',
        default=False,
        help='Whether the stage is a closing stage or not. A closing stage is a'
             'stage that indicates that the helpdesk ticket has been resolved '
             'or closed. This field is used to identify the closing stage and '
             'is used in various calculations and reports.')
    folded = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='Whether the stage is folded in the Kanban view or not. If this '
             'field is set to True, the stage will be displayed in a collapsed '
             'state in the Kanban view, which can be expanded by clicking on '
             'it.This field is used to control the behavior of the Kanban view.'
    )
