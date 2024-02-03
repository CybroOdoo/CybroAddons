# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
from ast import literal_eval
from odoo import fields, models


class EventManagementType(models.Model):
    """Model for managing the Event types"""
    _name = 'event.management.type'
    _description = 'Event Management Type'

    name = fields.Char(string="Name", help="Name of event type")
    image = fields.Binary(string="Image", attachment=True,
                          help="This field holds the image used as "
                               "image for the event, limited to 1080x720px.")
    event_count = fields.Integer(string="# of Events",
                                 compute='_compute_event_count',
                                 help="Count of event")

    def _compute_event_count(self):
        """Computes the count of event """
        for records in self:
            records.event_count = self.env['event.management'].search_count([
                ('type_of_event_id', '=', records.id)])

    def _get_action(self, action_xml_id):
        """ Passes the values to Event management kanban """
        action = self.env['ir.actions.actions']._for_xml_id(action_xml_id)
        if self:
            action['display_name'] = self.display_name
        context = {
            'search_default_type_of_event_id': [self.id],
            'default_type_of_event_id': self.id,
        }
        context = {**literal_eval(action['context']), **context}
        action['context'] = context
        return action

    def get_event_type_action_event(self):
        """Event type action """
        return self._get_action('event_management.event_management_action')
