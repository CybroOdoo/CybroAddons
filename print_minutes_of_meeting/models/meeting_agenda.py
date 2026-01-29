# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Irfan T @ Cybrosys, (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class MeetingAgenda(models.Model):
    """Model meeting agenda to note the agenda of the meeting"""
    _name = 'meeting.agenda'
    _description = 'Meeting Agenda'
    _rec_name = 'topic'

    topic = fields.Char(string="Topic", help="Agenda topic on meeting")
    description = fields.Char(string="Description",
                              help="Description on the topic")
    is_discussed = fields.Boolean(string="Discussed",
                                  help="Is this topic discussed or not")
    calendar_event_id = fields.Many2one('calendar.event',
                                        help="Calendar event of meeting",
                                        string="Calendar Event")
