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

class GroomingServiceLine(models.Model):
    """
    Model for storing individual Grooming Service Line details in veterinary clinic Management.
    """
    _name = "grooming.service.line"
    _description = "Grooming Service Line"

    service_id = fields.Many2one(
        comodel_name="product.product",
        string="Service",
        domain=[('type', '=', 'service'), ('is_grooming_product', '=', True)],
        context={'default_type': 'service', 'default_grooming_product': True},
        help="Service provided during grooming",
    )
    description = fields.Char(
        string="Description",
        help="Description of the grooming service provided",
    )
    price = fields.Float(
        string="Price",
        related="service_id.lst_price",
        help="Price of the grooming service based on the related product's list price",
    )
    grooming_id = fields.Many2one(
        string="Grooming ID",
        comodel_name="animal.grooming",
        help="Reference to the parent grooming case",
    )