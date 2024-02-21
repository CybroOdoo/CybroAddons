# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import api, fields, models, _


class EmployeeTraining(models.Model):
    """This class creates a model employee training and adds fields"""
    _name = 'employee.training'
    _rec_name = 'program_name'
    _description = "Employee Training"
    _inherit = 'mail.thread'

    program_name = fields.Char(string='Training Program', required=True,
                               help="Program name in training.")
    program_department_id = fields.Many2one('hr.department',
                                            string='Department', required=True,
                                            help="Department on training.")
    program_convener_id = fields.Many2one('res.users',
                                          string='Responsible User',
                                          required=True, help="Responsible "
                                                              "person.")
    training_ids = fields.One2many('hr.employee', string='Employee Details',
                                   compute="_compute_employee_details",
                                   help="Employee details on training.")
    note_id = fields.Text('Description', help="Give the description"
                                              " if any.")
    date_from = fields.Datetime(string="Date From", help="Give the from date.")
    date_to = fields.Datetime(string="Date To", help="Mention the to date.")
    user_id = fields.Many2one('res.users', string='users',
                              default=lambda self: self.env.user,
                              help="Mention the user.")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Mention the company.")
    state = fields.Selection([
        ('new', 'New'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled'),
        ('complete', 'Completed'),
        ('print', 'Print'),
    ], string='Status', readonly=True, copy=False, index=True,
        default='new', help="Status of training.")

    @api.depends('program_department_id')
    def _compute_employee_details(self):
        """Function to search for employee details"""
        datas = self.env['hr.employee'].search(
            [('department_id', '=', self.program_department_id.id)])
        self.training_ids = datas

    def print_event(self):
        """Reports to print the event"""
        self.ensure_one()
        started_date = datetime.strftime(self.create_date, "%Y-%m-%d ")
        duration = (self.write_date - self.create_date).days
        pause = relativedelta(hours=0)
        difference = relativedelta(self.write_date, self.create_date) - pause
        hours = difference.hours
        minutes = difference.minutes
        data = {
            'dept_id': self.program_department_id.id,
            'program_name': self.program_name,
            'company_name': self.company_id.name,
            'date_to': started_date,
            'duration': duration,
            'hours': hours,
            'minutes': minutes,
            'program_convener': self.program_convener_id.name,

        }
        return self.env.ref(
            'employee_orientation.print_pack_certificates').report_action(self,
                                                                          data=data)

    def action_complete_event(self):
        """Function executes if the event is completed and state changed to
        complete"""
        self.write({'state': 'complete'})

    def action_confirm_event(self):
        """Function executes if the event is confirmed and state changed to
              confirm"""
        self.write({'state': 'confirm'})

    def action_cancel_event(self):
        """Function executes if the event is cancelled and state changed to
              cancel"""
        self.write({'state': 'cancel'})

    def action_confirm_send_mail(self):
        """Function execute to confirm send mail and update values
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup(
                'employee_orientation.orientation_training_mailer')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup(
                'mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'employee.training',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
