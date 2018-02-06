# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<avinash@cybrosys.in>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api


class EventManagement(models.TransientModel):
    _name = 'event.management.report'

    event_type = fields.Many2many('event.management.type', 'event_type_rel', 'report_id', 'type_id', string="Type",
                                  required=True)
    event_state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('invoice', 'Invoiced'),
                                    ('close', 'Close'), ('cancel', 'Canceled')], string="State")

    @api.multi
    def pdf_report(self):
        type_select = self.event_type.ids
        state_select = self.event_state
        wizard_data = {"type_select": type_select, "state_select": state_select}
        return self.env['report'].get_action(self, 'event_management_report.event_report_template', data=wizard_data)

    @api.multi
    def xls_report(self):
        type_select = self.event_type.ids
        state_select = self.event_state
        wizard_data = {"type_select": type_select, "state_select": state_select}
        return {'type': 'ir.actions.report.xml',
                'report_name': 'event_management_report.event_report.xlsx',
                'report_type': 'xlsx',
                'datas': wizard_data,
                'name': 'Event Report'}
