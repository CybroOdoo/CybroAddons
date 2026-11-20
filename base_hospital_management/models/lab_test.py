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


class LabTest(models.Model):
    """Class holding lab test details"""
    _name = 'lab.test'
    _description = 'Laboratory Test'

    name = fields.Char(string='Test', help='Name of the test')
    patient_lead = fields.Float(string='Result Within',
                                help='Time taken to get the result')
    price = fields.Monetary(help="The cost for the test")
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self:
                                  self.env.company.currency_id.id,
                                  required=True, help='Currency in which '
                                                      'payments will be done')
    tax_ids = fields.Many2many('account.tax',
                               help='Tax for the test')
    medicine_ids = fields.One2many('lab.medicine.line',
                                   'test_id',
                                   help='Medicines used for the test')
    test_type = fields.Selection(
        [('range', 'Range'), ('objective', 'Objective')],
        string='Type', required=True, help='Type of test')
