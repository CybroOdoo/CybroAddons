# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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
    """
    This class is used to create catering details in Event management.
    It contains fields and functions for the model
    Methods:
        _compute_catering_pending(self):
            function to computes catering_pending field
        _compute_catering_done(self):
            function to computes catering done field
        action_event_confirm(self):
            actions to perform when clicking on the 'Confirm' button.
        action_view_catering_service(self):
            actions to perform when clicking on the 'Pending Done' smart button.
    """
    _inherit = 'event.management'

    catering_on = fields.Boolean(string="Catering Active", default=False,
                                 help="Shows thw catering is active or not")
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id",
                                  help="Corresponding catering in event")
    catering_pending = fields.Integer(string='Catering Pending',
                                      compute='_compute_catering_pending',
                                      help="Shows count of catering "
                                           "works are pending")
    catering_done = fields.Integer(string='Catering Done',
                                   compute='_compute_catering_done',
                                   help="Shows how many catering works are done"
                                   )

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_pending(self):
        """ Computes catering_pending field """
        self.catering_pending = False
        for order in self.catering_id:
            pending = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'open':
                    pending += 1
            self.catering_pending = pending

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_done(self):
        """ Computes catering_done field """
        self.catering_done = False
        for order in self.catering_id:
            done = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'done':
                    done += 1
            self.catering_done = done

    def action_event_confirm(self):
        """
        Extended function for the 'Confirm' button to create catering service
        when confirming event.
        """
        catering_line = self.service_line_ids.search([
            ('service', '=', 'catering'), ('event_id', '=', self.id)])
        if len(catering_line) > 0:
            self.catering_on = True
            self.catering_id = self.env['event.management.catering'].create({
                'name': self.env['ir.sequence'].next_by_code(
                    'catering.order.sequence'),
                'start_date': catering_line.date_from,
                'end_date': catering_line.date_to,
                'parent_event_id': self.id,
                'event_type_id': self.type_of_event_id.id,
                'catering_id': catering_line.id,
            }).id
        super(EventManagement, self).action_event_confirm()

    def action_view_catering_service(self):
        """
        This function returns an action that display existing catering
        service of the event.
        """
        action = self.env.ref(
            'event_catering.event_management_catering_action'). \
            sudo().read()[0]
        action['views'] = [(self.env.ref(
            'event_catering.event_management_catering_view_form').id, 'form')]
        action['res_id'] = self.catering_id.id
        if self.catering_id.id is not False:
            return action
        return False
