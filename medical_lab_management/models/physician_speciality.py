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


class PhysicianSpeciality(models.Model):
    """
       Model for managing physician details
    """
    _name = 'physician.speciality'
    _description = 'Medical Specialty'

    code = fields.Char(string='ID')
    name = fields.Char(string='Specialty', help='Name of the specialty',
                       required=True)

    _name_uniq = models.Constraint(
        'UNIQUE(name)', 'Name must be unique!',
    )
