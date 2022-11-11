# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class SeedDetails(models.Model):
    _name = 'seed.details'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Seed Details"

    name = fields.Char(string='Name', required=True, tracking=True)
    quantity = fields.Integer(string='Quantity', required=True, tracking=True)
    unit = fields.Selection([('kg', 'Kilograms'), ('gms', 'Grams')],
                            string='Unit', required=True, tracking=True)
    seed_type = fields.Selection(
        [('registered', 'Registered'), ('breeder', 'Breeder'),
         ('foundation', 'Foundation'),
         ('certified', 'Certified')], string='Type', required=True,
        tracking=True)
    note = fields.Text(string='Note', tracking=True)
