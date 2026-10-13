# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import math
from odoo import api, models


class ProductProduct(models.Model):
    """Inherit product_product model for adding EAN13 Standard Barcode"""
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        """Function to add EAN13 Standard barcode at the time
                create new product"""
        products = super().create(vals_list)
        for product in products:
            ean = generate_ean(str(product.id))
            product.barcode = '21' + ean[2:]
        return products


def ean_checksum(eancode):
    """Returns the checksum of an EAN string of length 13."""
    if len(eancode) != 13:
        return -1

    odd_sum = 0
    even_sum = 0

    for rec in range(len(eancode[::-1][1:])):
        if rec % 2 == 0:
            odd_sum += int(eancode[::-1][1:][rec])
        else:
            even_sum += int(eancode[::-1][1:][rec])

    total = (odd_sum * 3) + even_sum
    return int(10 - math.ceil(total % 10.0)) % 10


def check_ean(eancode):
    """Returns the checksum for an EAN13."""
    if not eancode:
        return True

    if len(eancode) != 13:
        return False

    try:
        int(eancode)
    except (ValueError, TypeError):
        return False

    return ean_checksum(eancode)


def generate_ean(ean):
    """Creates and returns a valid EAN13 from an identifier."""
    if not ean:
        return "0000000000000"

    product_identifier = '00000000000' + ean
    ean = product_identifier[-11:]

    check_number = check_ean(ean + '00')

    return f'{ean}0{check_number}'
