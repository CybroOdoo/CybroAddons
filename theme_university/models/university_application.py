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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api


class UniversityApplication(models.Model):
    """Stores an admission application submitted by a prospective student from
    the website 'Start Your Application' form, and lets staff track it through
    a simple review workflow in the backend."""
    _name = 'university.application'
    _description = 'University Application'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char('Applicant Name', required=True, tracking=True,
                       help='Full name of the prospective student submitting the application.')
    email = fields.Char('Email', required=True, tracking=True,
                        help='Email address used to contact the applicant about their application.')
    phone = fields.Char('Phone',
                        help='Optional phone number for contacting the applicant.')
    application_type_id = fields.Many2one(
        'university.application.type', string='Application Type', tracking=True,
        help='Type of application selected by the applicant (e.g. Undergraduate, Graduate).')
    admission_round_id = fields.Many2one(
        'university.admission.round', string='Admission Round', tracking=True,
        help='Admission round the applicant is applying for (e.g. Early Decision, Regular Decision).')
    program = fields.Char('Program of Interest',
                          help='Intended program, major or field of study the applicant is interested in.')
    message = fields.Text('Message',
                          help='Additional information or a personal note provided by the applicant.')
    state = fields.Selection([
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], string='Status', default='submitted', required=True, tracking=True,
        help='Current stage of the application in the admissions review workflow.')

    def action_set_in_review(self):
        """Move the selected applications to the 'In Review' stage."""
        self.write({'state': 'in_review'})

    def action_accept(self):
        """Mark the selected applications as accepted."""
        self.write({'state': 'accepted'})

    def action_reject(self):
        """Mark the selected applications as rejected."""
        self.write({'state': 'rejected'})
