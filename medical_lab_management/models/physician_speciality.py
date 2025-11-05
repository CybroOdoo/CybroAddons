##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################

from odoo import models, fields


class PhysicianSpeciality(models.Model):
    _name = 'physician.speciality'
    _description = 'Medical Specialty'

    code = fields.Char(string='ID')
    name = fields.Char(string='Specialty', help='Name of the specialty', required=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]
