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
from odoo.exceptions import ValidationError


class DentalPatients(models.Model):
    """To create Patients in the clinic, use res.partner model and customize it"""
    _inherit = 'res.partner'

    company_type = fields.Selection(selection_add=[('person', 'Patient'),
                                                   ('company', 'Medicine Distributor')],
                                    help="Patient type")
    dob = fields.Date(string="Date of Birth",
                      help="DOB of the patient")
    patient_age = fields.Integer(compute='_compute_patient_age',
                                 store=True,
                                 string="Age",
                                 help="Age of the patient")
    insurance_company_id = fields.Many2one('insurance.company',
                                           string="Insurance Company",
                                           help="Mention the insurance company")
    start_date = fields.Date(string="Member Since",
                             help="Patient insurance start date")
    expiration_date = fields.Date(string="Expiration Date",
                                  help="Patient insurance expiration date")
    insureds_name = fields.Char(string="Insured's Name",
                                help="Name of the insured's")
    identification_number = fields.Char(string="Identification Number",
                                        help="Identification Number of insured's")
    is_patient = fields.Boolean(string="Is Patient",
                                help="To set it's a patient")
    medical_questionnaire_ids = fields.One2many('medical.questionnaire',
                                                'patient_id',
                                                readonly=False,
                                                help="connect model medical questionnaire in patients")
    report_ids = fields.One2many('xray.report', 'patient_id',
                                 string='X-Ray',
                                 help="To add the xray reports of the patient")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['company_type'] = 'person'
            vals['is_patient'] = True
        res = super(DentalPatients, self).create(vals_list)

        for record in res:
            if record.email:
                wizard = self.env['portal.wizard'].create([{
                    'partner_ids': [fields.Command.link(record.id)]
                }])
                portal_user = self.env['portal.wizard.user'].sudo().create([{
                    'partner_id': record.id,
                    'email': record.email,
                    'wizard_id': wizard.id
                }])
                portal_user.action_grant_access()
        return res

    @api.depends('dob')
    def _compute_patient_age(self):
        """Computes the age of the patient based on their date of birth (dob)
        and updates the `patient_age` field. The age is calculated by subtracting
        the year of the patient's dob from the current year. If the current
        date is before the patient's birthday in the current year, one year is
        subtracted from the age."""
        for record in self:
            patient_age = (fields.Date.today().year - record.dob.year -
                           ((fields.Date.today().month, fields.Date.today().day) <
                            (record.dob.month, record.dob.day))) if record.dob else False
            if patient_age > 0:
                record.patient_age = patient_age
            else:
                record.patient_age = 0

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
