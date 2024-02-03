# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class EventManagement(models.Model):
    """Adding catering details in Event management model"""
    _inherit = 'event.management'

    is_catering_on = fields.Boolean(string="Catering Active",
                                    help="Indicates whether catering services "
                                         "are active for this event.")
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id",
                                  help="Reference to the catering service "
                                       "associated with this event.")
    catering_pending = fields.Integer(string='Catering Pending',
                                      compute='_compute_catering_pending',
                                      help="Number of pending catering "
                                           "services for this event.")
    catering_done = fields.Integer(string='Catering Done',
                                   compute='_compute_catering_done',
                                   help="Number of completed catering "
                                        "services for this event.")

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_pending(self):
        """Compute pending catering"""
        self.catering_pending = False
        for order in self.catering_id:
            pending = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'open':
                    pending += 1
            self.catering_pending = pending

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_done(self):
        """Compute all the done work status"""
        self.catering_done = False
        for order in self.catering_id:
            done = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'done':
                    done += 1
            self.catering_done = done

    def action_event_confirm(self):
        """Confirm the Event"""
        catering_service = self.env['event.management.catering']
        catering_line = self.service_line_ids.search([
            ('service', '=', 'catering'), ('event_id', '=', self.id)])
        if self.service_line_ids.search_count([('service', '=', 'catering'),
                                               ('event_id', '=', self.id)]) > 0:
            self.is_catering_on = True
            sequence_code = 'catering.order.sequence'
            name = self.env['ir.sequence'].next_by_code(sequence_code)
            event = self.id
            event_type = self.type_of_event_id.id
            start_date = catering_line.date_from
            end_date = catering_line.date_to
            catering_id = catering_line.id
            data = {
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'parent_event_id': event,
                'event_type_id': event_type,
                'catering_id': catering_id,
            }
            catering_map = catering_service.create(data)
            self.catering_id = catering_map.id
        super(EventManagement, self).action_event_confirm()

    def action_view_catering_service(self):
        """This function returns an action that displays existing catering
        service of the event."""
        action = self.env.ref(
            'event_catering.event_management_catering_action').sudo().read()[0]
        action['views'] = [(self.env.ref(
            'event_catering.event_management_catering_view_form').id, 'form')]
        action['res_id'] = self.catering_id.id
        if self.catering_id.id is not False:
            return action
