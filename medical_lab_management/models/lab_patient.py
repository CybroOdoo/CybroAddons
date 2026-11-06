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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class LabPatient(models.Model):
    """
        This class represents Patient information in a laboratory system.
    """
    _name = 'lab.patient'
    _rec_name = 'patient_id'
    _description = 'Patient'

    patient_id = fields.Many2one('res.partner', string='Partner',
                              required=True)
    patient_image = fields.Binary(string='Photo',
                                  help="Profile image of the patient")
    patient = fields.Char(readonly=True)
    name = fields.Char(string='Patient ID', default=lambda self: ('New'), readonly=True)
    title = fields.Selection([
        ('ms', 'Miss'),
        ('mister', 'Mister'),
        ('mrs', 'Mrs'),
    ], default='mister', required=True)
    gender = fields.Selection(
        [('m', 'Male'), ('f', 'Female'),
         ('ot', 'Other')], help="Gender of the patient", required=True)
    dob = fields.Date(string='Date Of Birth', help="Date of birth of the patient",
                      required=True)
    age = fields.Char(help="Age of the patient",
                      compute='_compute_age', store=True)
    blood_group = fields.Selection(
        [('A+', 'A+ve'), ('B+', 'B+ve'), ('O+', 'O+ve'),
         ('AB+', 'AB+ve'), ('A-', 'A-ve'), ('B-', 'B-ve'), ('O-', 'O-ve'),
         ('AB-', 'AB-ve')])
    visa_info = fields.Char(size=64, help="Visa information of the patient")
    id_proof_number = fields.Char(string='ID Proof Number',
                                  help="ID proof information of the patient")
    note = fields.Text()
    date = fields.Datetime(string='Date Requested',
                           default=lambda s: fields.Datetime.now(),
                           help="Requested date of lab request")
    phone = fields.Char(required=True,
                        help="Phone number of the patient")
    email = fields.Char(required=True, help="Email of the patient")
    patient_image_base64 = fields.Char(compute='_compute_patient_image_base64')

    @api.depends('patient_image')
    def _compute_patient_image_base64(self):
        for rec in self:
            rec.patient_image_base64 = (
                rec.patient_image.to_base64() if rec.patient_image else False)

    @api.depends('dob')
    def _compute_age(self):
        """
           Compute the patient's age based on their date of birth.
           :param self: The record itself.
        """
        for data in self:
            if data.dob:
                dob = fields.Datetime.from_string(data.dob)
                date = fields.Datetime.from_string(data.date)
                delta = relativedelta(date, dob)
                data.age = str(delta.years) + ' ' + 'years'
            else:
                data.age = ''

    @api.model_create_multi
    def create(self, vals_list):
        """
            Create a new patient record and generate a unique patient ID
            :param self: The record itself.
            :param dict vals_list: A dictionary of values for creating the patient record.
            :return: The created patient record.
            :rtype: LabPatient
        """
        for vals in vals_list:
            sequence = self.env['ir.sequence'].next_by_code('lab.patient')
            vals['name'] = sequence or ('New')
        return super().create(vals_list)

    @api.onchange('patient')
    def detail_get(self):
        """
           Update patient contact details based on the selected partner
           :param self: The record itself.
        """
        self.phone = self.patient.phone
        self.email = self.patient.email
