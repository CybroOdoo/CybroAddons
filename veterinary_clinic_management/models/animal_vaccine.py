# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
#############################################################################
from odoo import fields, models


class AnimalVaccine(models.Model):
    """
    Model for storing vaccines in veterinary clinic management.
    """
    _name = 'animal.vaccine'
    _description = "Animal Vaccines"

    name = fields.Char(
        string="Vaccine Name",
        required=True,
        help="Name of the vaccine",
    )
    charge = fields.Float(
        string="Charge",
        required=True,
        help="Charge of the vaccine",
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This Vaccine name already exists!"),
    ]
