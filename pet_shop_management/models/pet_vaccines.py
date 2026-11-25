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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class PetVaccines(models.Model):
    """ This is used to identify the vaccines """
    _name = 'pet.vaccines'
    _rec_name = 'vaccine_name'
    _description = "Pet Vaccines"

    pet_vaccine_id = fields.Many2one(
        'product.product', string='Pet', ondelete='cascade',
        domain="[('is_pet', '=', True)]",
        help='Pet record to which this vaccination dose applies.'
    )
    vaccine_name = fields.Char(
        string='Vaccine Name', required=True,
        help='Brand or medical name of vaccine (e.g. Rabies, DHPP).'
    )
    date = fields.Date(
        string='Administered Date',
        help='Calendar date on which this vaccination dose was administered.'
    )
    date_exp = fields.Date(
        string='Expiration Date',
        help='Date when this vaccine dosage expires and booster is due.'
    )
    veterinarian_id = fields.Many2one(
        'hr.employee', string='Veterinarian', ondelete='set null',
        domain="[('is_veterinarian', '=', True)]",
        help='Licensed veterinarian employee who administered vaccination.'
    )
