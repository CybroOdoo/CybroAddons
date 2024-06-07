# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
from odoo import models


class Product(models.Model):
    """This class is used to inherit the 'product.product' model in Odoo."""
    _inherit = 'product.product'

    def check_ean(self, ean_code):
        """Returns True if ean_code is a valid EAN-13 string, or False."""
        if not ean_code or len(ean_code) != 13:
            return False
        if not ean_code.isdigit():
            return False
        return self.ean_checksum(ean_code)

    def ean_checksum(self, ean_code):
        """Returns the checksum of an ean string of length 13, returns -1 if
        the string has the wrong length."""
        if len(ean_code) != 13:
            return -1
        odd_sum = 0
        even_sum = 0
        ean_value = ean_code
        reverse_value = ean_value[::-1]
        final_ean = reverse_value[1:]
        for i, digit in enumerate(final_ean):
            if i % 2 == 0:
                odd_sum += int(digit)
            else:
                even_sum += int(digit)
        total = (odd_sum * 3) + even_sum
        check = int(10 - math.ceil(total % 10.0)) % 10
        return check

    def generate_ean(self):
        """Creates and returns a valid ean13 from an invalid one."""
        if not self.id:
            return "0000000000000"
        product_identifier = '00000000000' + str(self.id)
        ean = product_identifier[-11:]
        check_number = self.check_ean(ean + '00')
        return f'{ean}0{check_number}'

    def action_generate_barcode(self):
        """To generate barcode for the product."""
        if not self.id:
            return "0000000000000"
        product_identifier = '00000000000' + str(self.id)
        ean = product_identifier[-11:]
        check_number = self.check_ean(ean + '00')
        ean = f'{ean}0{check_number}'
        self.barcode = '21' + ean[2:]
