# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_normalize
from odoo.exceptions import ValidationError


class DentalDoctor(models.Model):
    """To add the doctors of the clinic"""
    _inherit = 'hr.employee'

    job_position = fields.Char(string="Designation",
                               help="To add the job position of the doctor")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        help="Add the doctor specialised")
    dob = fields.Date(string="Date of Birth",
                      required=True,
                      help="DOB of the patient")
    doctor_age = fields.Integer(compute='_compute_doctor_age',
                                store=True,
                                string="Age",
                                help="Age of the patient")
    sex = fields.Selection([('male', 'Male'),
                            ('female', 'Female')],
                           string="Sex",
                           help="Sex of the patient")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift",
                                      help="Time shift of the doctor")

    def unlink(self):
        """Delete the corresponding user from res.users while
        deleting the doctor"""
        for record in self:
            self.env['res.users'].search([('id', '=', record.user_id.id)]).unlink()
        res = super(DentalDoctor, self).unlink()
        return res

    @api.depends('dob')
    def _compute_doctor_age(self):
        """To calculate the age of the doctor from the DOB"""
        for record in self:
            age = (fields.Date.today().year - record.dob.year -
                                  ((fields.Date.today().month,
                                    fields.Date.today().day) <
                                   (record.dob.month,
                                    record.dob.day))) if record.dob else False
            if age>0:
                record.doctor_age = age
            else:
                record.doctor_age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('work_email'):
                vals['work_email'] = email_normalize(vals['work_email'])
        employees = super().create(vals_list)
        for employee in employees:
            if not employee.work_email:
                continue
            try:
                email = employee.work_email
                existing_user = self.env['res.users'].search(
                    [('login', '=', email)], limit=1
                )
                if existing_user:
                    employee.user_id = existing_user.id
                    doctor_group = self.env.ref(
                        'dental_clinical_management.group_dental_doctor'
                    )
                    internal_group = self.env.ref('base.group_user')
                    portal_group = self.env.ref('base.group_portal')
                    existing_user.write({
                        'group_ids': [
                            (3, portal_group.id),
                            (4, internal_group.id),
                            (4, doctor_group.id)
                        ]
                    })
                    if existing_user.partner_id:
                        existing_user.partner_id.write({
                            'is_patient': False
                        })
                    continue
                user = self.env['res.users'].with_context(
                    no_reset_password=True
                )._create_user_from_template({
                    'name': employee.name,
                    'login': email,
                    'email': email,
                    'partner_id': employee.address_home_id.id or self.env.user.partner_id.id,
                    'group_ids': [(6, 0, [
                        self.env.ref("base.group_user").id,
                        self.env.ref('dental_clinical_management.group_dental_doctor').id,
                        self.env.ref('sales_team.group_sale_salesman').id,
                        self.env.ref('hr.group_hr_user').id,
                        self.env.ref('account.group_account_invoice').id,
                        self.env.ref('stock.group_stock_user').id,
                        self.env.ref('purchase.group_purchase_user').id
                    ])],
                    'company_id': self.env.company.id,
                    'company_ids': [(6, 0, self.env.company.ids)],
                })
                employee.user_id = user.id
            except Exception as e:
                raise UserError(_("Failed to create doctor user: %s") % str(e))
        return employees

    @api.constrains('dob')
    def _check_dob_validation(self):
        today = fields.Date.today()
        for record in self:
            if record.dob:
                if record.dob > today:
                    raise ValidationError("Date of Birth cannot be in the future.")
                age = (
                        today.year - record.dob.year -
                        ((today.month, today.day) < (record.dob.month, record.dob.day))
                )
                if age < 0:
                    raise ValidationError("Age cannot be negative.")
