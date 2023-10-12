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


class MeetingAction(models.Model):
    """Model meeting actions to add the action tobe taken from the meetings """
    _name = 'meeting.action'
    _description = 'Meeting Action'

    def _domain_responsible_partner_id(self):
        """Return the domain for responsible partner"""
        return [('id', 'in', self.calendar_event_id.partner_ids.ids)]

    action = fields.Char(string="Action", help="Action of meeting")
    description = fields.Char(string="Description",
                              help="Description of meeting")
    agenda_item_id = fields.Many2one('meeting.agenda', string="Agenda Item",
                                     help="Agenda of the meeting")
    responsible_partner_id = fields.Many2one(
        'res.partner', domain=_domain_responsible_partner_id,
        string="Responsible Partner",
        help="Responsible partner of the meeting")
    assigned_partner_ids = fields.Many2many('res.partner',
                                            string="Assigned Partner",
                                            help="Assigned Partner of meeting")
    calendar_event_id = fields.Many2one('calendar.event',
                                        string="calendar Event",
                                        help="Calendar event which about "
                                             "the meeting is taking")
    deadline = fields.Date(string="Deadline",
                           help="Deadline to take an action")
