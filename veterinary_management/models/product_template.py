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


class ProductTemplate(models.Model):
    """
        Inherits the product.template model to add fields specific to veterinary products.
    """
    _inherit = 'product.template'

    grooming_product = fields.Boolean(
        string='Grooming Product',
        default=False,
        help='Indicates if the product is used for grooming services.'
    )
    medicine_product = fields.Boolean(
        string='Medicine',
        default=False,
        help='Indicates if the product is a type of medicine.'
    )
    medical_report = fields.Boolean(
        string="Medical Test",
        help='Indicates if the product is related to medical reports.'
    )
