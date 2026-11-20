# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """Inherited to add more fields and functions"""
    _inherit = 'hr.employee'

    doctor = fields.Boolean(compute='_compute_doctor',
                            store=True, readonly=False, help='True for Doctors')

    @api.depends('job_id', 'job_title')
    def _compute_doctor(self):
        """Compute whether the employee is a doctor based on job title or job position"""
        for record in self:
            record.doctor = (record.job_title == 'Doctor' or
                             (record.job_id and record.job_id.name == 'Doctor'))

    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  help='Currency in which consultation fee '
                                       'is calculating')
    coach_id = fields.Many2one('hr.employee',
                               help='Name of the coach')
    consultancy_charge = fields.Monetary(string="Consultation Charge",
                                         help='Charge for consultation')
    consultancy_type = fields.Selection([('resident', 'Residential'),
                                         ('special', 'Specialist')],
                                        string="Consultation Type",
                                        help='Select the type of Consultation')
    time_avg = fields.Float(string='Average Time for a Patient',
                            help="Average Consultation time "
                                 "per Patient in minutes")
    degree_ids = fields.Many2many('hospital.degree',
                                  help='Degrees of staff')
    pharmacy_id = fields.Many2one('hospital.pharmacy',
                                  help='Name of the pharmacy')
    specialization_ids = fields.Many2many('doctor.specialization',
                                          help="Doctors specialization for"
                                               " an area")

    def action_create_user(self):
        """Updating employee field of res user to true"""
        self.ensure_one()
        if self.user_id:
            raise ValidationError(self.env._("This employee already has an user."))
        return {
            'name': self.env._('Create User'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'view_id': self.env.ref('hr.view_users_simple_form').id,
            'target': 'new',
            'context': {
                'default_create_employee_id': self.id,
                'default_name': self.name,
                'default_phone': self.work_phone,
                'default_mobile_phone': self.mobile_phone,
                'default_login': self.work_email,
                'default_employee': True
            }
        }

    def _inverse_work_contact_details(self):
        """Override to prevent creating patient while creating a staff"""
        for employee in self:
            if not employee.work_contact_id:
                employee.work_contact_id = self.env[
                    'res.partner'].sudo().create(
                    {
                        'email': employee.work_email,
                        'phone': employee.mobile_phone,
                        'name': employee.name,
                        'image_1920': employee.image_1920,
                        'company_id': employee.company_id.id,
                        'patient_seq': 'Employee'
                    })
            else:
                employee.work_contact_id.sudo().write({
                    'email': employee.work_email,
                    'phone': employee.mobile_phone,
                    'patient_seq': 'Employee'
                })

    @api.model
    def fetch_doctors_for_reception(self, domain):
        """
        Fetch doctors (employees with job_id.name = 'Doctor') for reception dashboard.
        Uses sudo to bypass access restrictions.
        """
        return self.sudo().search_read(domain=domain)


class HrEmployeePublic(models.Model):
    """Inherited to expose hospital fields on employee public profile"""
    _inherit = 'hr.employee.public'

    doctor = fields.Boolean(related='employee_id.doctor', readonly=True)
    currency_id = fields.Many2one('res.currency',
                                  related='employee_id.currency_id',
                                  readonly=True)
    consultancy_charge = fields.Monetary(related='employee_id.consultancy_charge',
                                         readonly=True)
    consultancy_type = fields.Selection(related='employee_id.consultancy_type',
                                        readonly=True)
    time_avg = fields.Float(related='employee_id.time_avg', readonly=True)
    degree_ids = fields.Many2many(related='employee_id.degree_ids', readonly=True)
    pharmacy_id = fields.Many2one(related='employee_id.pharmacy_id', readonly=True)
    specialization_ids = fields.Many2many(related='employee_id.specialization_ids',
                                          readonly=True)

