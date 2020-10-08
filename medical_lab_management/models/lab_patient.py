# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P @ cybrosys and Niyas Raphy @ cybrosys(odoo@cybrosys.com)
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
from odoo import models, fields, api, _


class LabPatient(models.Model):
    _name = 'lab.patient'
    _rec_name = 'patient'
    _description = 'Patient'

    patient = fields.Many2one('res.partner', string='Partner', required=True)
    patient_image = fields.Binary(string='Photo')
    patient_id = fields.Char(string='Patient ID', readonly=True)
    name = fields.Char(string='Patient ID', default=lambda self: _('New'))
    title = fields.Selection([
         ('ms', 'Miss'),
         ('mister', 'Mister'),
         ('mrs', 'Mrs'),
    ], string='Title', default='mister', required=True)
    emergency_contact = fields.Many2one(
        'res.partner', string='Emergency Contact')
    gender = fields.Selection(
        [('m', 'Male'), ('f', 'Female'),
         ('ot', 'Other')], 'Gender', required=True)
    dob = fields.Date(string='Date Of Birth', required=True)
    age = fields.Char(string='Age', compute='compute_age')
    blood_group = fields.Selection(
        [('A+', 'A+ve'), ('B+', 'B+ve'), ('O+', 'O+ve'), ('AB+', 'AB+ve'),
         ('A-', 'A-ve'), ('B-', 'B-ve'), ('O-', 'O-ve'), ('AB-', 'AB-ve')],
        'Blood Group')
    visa_info = fields.Char(string='Visa Info', size=64)
    id_proof_number = fields.Char(string='ID Proof Number')
    note = fields.Text(string='Note')
    date = fields.Datetime(string='Date Requested', default=lambda s: fields.Datetime.now(), invisible=True)
    phone = fields.Char(string="Phone", required=True)
    email = fields.Char(string="Email", required=True)

    def compute_age(self):
        for data in self:
            if data.dob:
                dob = fields.Datetime.from_string(data.dob)
                date = fields.Datetime.from_string(data.date)
                delta = relativedelta(date, dob)
                data.age = str(delta.years) + ' years'
            else:
                data.age = ''

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('lab.patient')
        vals['name'] = sequence or _('New')
        result = super(LabPatient, self).create(vals)
        return result

    @api.onchange('patient')
    def detail_get(self):
        self.phone = self.patient.phone
        self.email = self.patient.email
