"""Pets"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
from odoo import fields, models


class PetVaccines(models.Model):
    """This is used to identify the vaccines"""
    _name = 'pet.vaccines'
    _rec_name = 'vaccine_name'
    _description = "Pet Vaccines"

    pet_vaccine_id = fields.Many2one('product.product',
                                     string='Vaccine',
                                     help='Vaccine product id')
    vaccine_name = fields.Char(string='Vaccine Name',
                               help='Name of the vaccine')
    date = fields.Date(string='Date', help='Date')
    date_exp = fields.Date(string='Date Expired', help='Date expired')
    veterinarian_id = fields.Many2one('hr.employee',
                                      string='Veterinarian',
                                      help='Veterinarian of the pet',
                                      domain="[('is_veterinarian', '=', True)]")
