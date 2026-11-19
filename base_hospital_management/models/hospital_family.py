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


class HospitalFamily(models.Model):
    """Class holding hospital family details"""
    _name = 'hospital.family'
    _description = 'Hospital Family'

    name = fields.Char(help='Name of family member')
    relation = fields.Char(help='Relation with the patient')
    age = fields.Integer(help='Age of family member')
    deceased = fields.Selection([('yes', 'Yes'), ('no', 'NO')],
                                string="Deceased", help='Specify whether the '
                                                        'family member is '
                                                        'alive or not')
    family_id = fields.Many2one('res.partner', help='Choose the family '
                                                         'member')
