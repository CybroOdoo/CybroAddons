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
"""Defines the Medicare Department model representing hospital departments."""

from odoo import models, fields

class MedicareDepartment(models.Model):
    """Model for managing hospital departments and specialties."""
    _name = 'medicare.department'
    _description = 'Medicare Department'

    name = fields.Char(string='Department Name', required=True)
    description = fields.Text(string='Description')
    icon = fields.Image(string='Icon')
    active = fields.Boolean(default=True)
