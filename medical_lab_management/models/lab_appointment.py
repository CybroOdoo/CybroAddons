# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Fansa Jabeen A  (odoo@cybrosys.com)
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
import datetime
from odoo.exceptions import UserError
from odoo import api, fields, models


class LabAppointment(models.Model):
    """
       Model for managing lab appointments.This class defines the structure a
       nd behavior of lab appointments, including the creation of invoices and
       lab test requests.
    """
    _name = 'lab.appointment'
    _inherit = ['mail.thread']
    _description = "Appointment"
    _order = 'appointment_date'

    user_id = fields.Many2one('res.users', help="Responsible user",
                              string='Responsible', readonly=True)
    patient_id = fields.Many2one('lab.patient',
                                 string='Patient', required=True,
                                 help='Patient Name')
    name = fields.Char(string='Appointment ID', readonly=True,
                       default=lambda self: ('New'),
                       help='Name of the lab appointment')
    date = fields.Datetime(string='Requested Date',
                           default=lambda s: fields.Datetime.now(),
                           help="Date in which patient appointment is noted")
    appointment_date = fields.Datetime(string='Appointment Date',
                                       default=lambda s: fields.Datetime.now(),
                                       help="This is the appointment date")
    physician_id = fields.Many2one('res.partner',
                                   string='Referred By',
                                   help="Physician referred by")
    comment = fields.Text(string='Comments', help="Extra information")
    appointment_line_ids = fields.One2many('lab.appointment.lines',
                                           'test_line_appointment_id',
                                           string="Test Request",
                                           help="Test requests for appointment")
    request_count = fields.Integer(compute="_compute_state",
                                   string='# of Requests', copy=False,
                                   default=0,help="Number of Requests")
    inv_count = fields.Integer(compute="_compute_state",help="Number of Invoice",
                               string='# of Invoices', copy=False, default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('request_lab', 'Lab Requested'),
        ('completed', 'Test Result'),
        ('to_invoice', 'To Invoice'),
        ('invoiced', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True,
        default='draft',
    )
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], default='0')


    @api.model_create_multi
    def create(self, vals_list):
        """
           Create a new lab appointment record.This method creates a new lab
           appointment record and assigns a unique appointment ID to it.
           :param self: The record itself.
           :param dict vals_list: A dictionary of values for creating the lab
           appointment record.
           :return: The created lab appointment record.
           :rtype: LabAppointment

        """
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'lab.appointment') or ('New')
        return super().create(vals_list)

    def _compute_state(self):
        """
            Compute the number of test requests and invoices related to the
            appointment.This method calculates and updates the counts of test
            requests and invoices associated with the appointment.
            :param self: The record itself.
        """
        for obj in self:
            obj.request_count = self.env['lab.request'].search_count(
                [('app_id', '=', obj.id)])
            obj.inv_count = self.env['account.move'].search_count(
                [('lab_request_id', '=', obj.id)])

    def action_create_invoice(self):
        """
           Create an invoice for the lab appointment.This method creates an
           invoice for the lab appointment and adds invoice lines for the
           selected lab tests.
           :param self: The record itself.
        """
        account_move = self.env["account.move"]
        for lab in self:
            lab.write({'state': 'to_invoice'})
            curr_invoice = {
                'partner_id': lab.patient_id.patient_id.id,
                'state': 'draft',
                'move_type': 'out_invoice',
                'invoice_date': str(datetime.datetime.now()),
                'invoice_origin': "Lab Test# : " + lab.name,
                'lab_request_id': lab.id,
                'is_lab_invoice': True,
            }
            inv_ids = account_move.create(curr_invoice)
            inv_id = inv_ids.id
            if inv_ids:
                journal = self.env['account.journal'].search(
                    [('type', '=', 'sale')], limit=1)
                prd_account_id = journal.default_account_id.id
                list_value = []
                if lab.appointment_line_ids:
                    for line in lab.appointment_line_ids:
                        list_value.append((0, 0, {
                            'name': line.lab_test_id.lab_test,
                            'price_unit': line.cost,
                            'quantity': 1.0,
                            'account_id': prd_account_id,
                            'move_id': inv_id,
                        }))
                    inv_ids.write({'invoice_line_ids': list_value})
            view_id = self.env.ref('account.view_move_form').id
            return {
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'name': ('Lab Invoices'),
                'res_id': inv_id
            }

    def action_request(self):
        """
            Create lab test requests for the selected lab tests.This method
            creates lab test requests for the selected lab tests associated
            with the appointment
            :param self: The record itself.
        """
        if self.appointment_line_ids:
            for line in self.appointment_line_ids:
                lab_test = self.env['lab.test'].search(
                    [('lab_test', '=', line.lab_test_id.lab_test)])
                self.env['lab.request'].create(
                    {'lab_request_id': self.name,
                     'app_id': self.id,
                     'lab_requestor_id': self.patient_id.id,
                     'lab_requesting_date': self.appointment_date,
                     'test_request_id': line.lab_test_id.id,
                     'request_line_ids': [(6, 0,
                                       [x.id for x in lab_test.test_lines_ids])],
                     })
            self.state = 'request_lab'
        else:
            raise UserError(('Please Select Lab Test.'))

    def action_confirm_appointment(self):
        """
           Confirm the lab appointment and send a confirmation email to the
           patient.
           :param self: The record itself.
        """
        message_body = ("Dear " +
                        self.patient_id.name + "," +
                        "<br>Your Appointment Has been Confirmed " +
                        "<br>Appointment ID : " + self.name +
                        "<br>Date : " + str(self.appointment_date) +
                        '<br><br>Thank you')
        template_obj = self.env['mail.mail']
        template_data = {
            'subject': 'Appointment Confirmation',
            'body_html': message_body,
            'email_from': 'michaelmorbius915@gmail.com',
            'email_to': self.patient_id.email
        }
        template_id = template_obj.create(template_data)
        template_obj.send(template_id)
        self.write({'state': 'confirm'})

    def action_cancel_appointment(self):
        """
           Cancel the lab appointment.This method cancels the lab appointment
           by setting its state to 'cancel'.
           :param self: The record itself.
        """
        return self.write({'state': 'cancel'})
