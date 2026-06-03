# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import fields, models


class BreedTypes(models.Model):
    """
    Model for storing breed types in veterinary management.
    """
    _name = 'breed.types'
    _description = "Breed Types"

    animal_type_id = fields.Many2one(
        string="Animal Type",
        comodel_name="animal.types",
        help="Type of animal for this breed",
    )
    name = fields.Char(
        string="Breed Name",
        required=True,
        help="Name of the breed",
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This Breed Type already exists!"),
    ]
