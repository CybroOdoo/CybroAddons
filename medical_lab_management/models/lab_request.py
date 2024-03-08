# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LabRequest(models.Model):
    """
        Model for managing Lab Requests
    """
    _name = 'lab.request'
    _inherit = ['mail.thread']
    _rec_name = 'lab_request_id'
    _description = 'Lab Request'

    name = fields.Char(string='Lab Test', size=16, readonly=True,
                       required=True, help="Lab result ID",
                       default=lambda *a: '#')
    lab_request_id = fields.Char(string='Appointment ID',
                                 help="Lab appointment ID")
    app_id = fields.Many2one('lab.appointment',
                             string='Appointment')
    lab_requestor = fields.Many2one('lab.patient',
                                    string='Patient', required=True,
                                    select=True, help='Patient Name')
    test_request = fields.Many2one('lab.test', string='Test')
    lab_requesting_date = fields.Datetime(string='Requested Date')
    comment = fields.Text('Comment')
    request_line = fields.One2many('lab.test.attribute',
                                   'test_request_reverse',
                                   string="Test Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sample_collection', 'Sample Collected'),
        ('test_in_progress', 'Test In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, copy=False, index=True, tracking=True,
        default='draft')

    @api.model
    def create(self, vals):
        """
            Create a new lab request
            :param self: The record itself.
            :param dict vals: A dictionary of values for creating the lab request.
            :return: The created lab request record.
            :rtype: LabRequest
        """
        sequence = self.env['ir.sequence'].next_by_code('lab.request')
        vals['name'] = sequence or '/'
        return super(LabRequest, self).create(vals)

    def action_set_to_sample_collection(self):
        """
           Set the lab request's state to 'Sample Collected
           :param self: The record itself.
        """
        return self.write({'state': 'sample_collection'})

    def action_set_to_test_in_progress(self):
        """
           Set the lab request's state to 'Test In Progress'
           :param self: The record itself.
        """
        return self.write({'state': 'test_in_progress'})

    def action_cancel_lab_test(self):
        """
            Cancel the lab test.
            :param self: The record itself.
        """
        return self.write({'state': 'cancel'})

    def action_set_to_test_completed(self):
        """
           Set the lab request's state to 'Completed'
           :param self: The record itself.
        """
        if not self.request_line:
            raise ValidationError(_("No Result Lines Entered !"))
        req_obj = self.env['lab.request'].search_count(
            [('app_id', '=', self.app_id.id), ('id', '!=', self.id)])
        req_obj_count = (self.env['lab.request'].search_count
                         ([('app_id', '=', self.app_id.id),
                           ('id', '!=', self.id), ('state', '=', 'completed')]
                          ))
        if req_obj == req_obj_count:
            app_obj = self.env['lab.appointment'].search(
                [('id', '=', self.app_id.id)])
            app_obj.write({'state': 'completed'})
        return self.write({'state': 'completed'})

    def action_print_lab_test(self):
        """
            Print the lab test report
            :param self: The record itself.
        """
        return self.env.ref('medical_lab_management.action_lab_request_report').report_action(self)
