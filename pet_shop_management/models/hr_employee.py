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


class HrEmployee(models.Model):
    """ Inheriting employee to identifies the walker /veterinarian """
    _inherit = 'hr.employee'

    is_veterinarian = fields.Boolean(
        string='Is Veterinarian', default=False,
        help='Check this box if the employee is a licensed veterinarian '
             'eligible to perform pet health checks and vaccinations.'
    )
    is_walker_sitters = fields.Boolean(
        string='Is Pet Walker/Sitter', default=False,
        help='Check this box if the employee is qualified and available '
             'to accept pet walking and sitting appointments.'
    )
