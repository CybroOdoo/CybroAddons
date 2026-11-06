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


class ResPartner(models.Model):
    """
       This class inherits the 'res.partner' model to represent patients and
       physicians in the system.
    """
    _inherit = 'res.partner'

    is_patient = fields.Boolean(help="Patient Identification")
    is_physician = fields.Boolean(help="Physician Identification")
    speciality_id = fields.Many2one('physician.speciality',
                                    help="Specialty of the physician")
    hospital_id = fields.Many2one('res.partner',
                                  help="Name of the hospital")
