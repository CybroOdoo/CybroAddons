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
"""Defines the Medicare Doctor model representing medical professionals."""

from odoo import models, fields

class MedicareDoctor(models.Model):
    """Model for managing doctors, their specialties, and department affiliations."""
    _name = 'medicare.doctor'
    _description = 'Medicare Doctor'

    name = fields.Char(string='Doctor Name', required=True)
    image = fields.Image(string='Photo')
    specialization = fields.Char(string='Specialization')
    department_id = fields.Many2one('medicare.department', string='Department')
    biography = fields.Text(string='Biography')
    active = fields.Boolean(default=True)
