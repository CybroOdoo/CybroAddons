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
from odoo import fields, models


class BloodDonation(models.Model):
    """Class holding blood donation details"""
    _name = 'blood.donation'
    _description = 'Blood Donation'
    _rec_name = 'questions'

    questions = fields.Text(string='Contra Indications',
                            help='Contraindications of the blood donor')
    is_true = fields.Boolean(help='True for contraindications')
    blood_bank_id = fields.Many2one('blood.bank',
                                    help='Blood bank corresponding to the '
                                         'donor')
