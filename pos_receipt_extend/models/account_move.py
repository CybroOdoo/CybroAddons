# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
# #############################################################################
import math
import re
from odoo import api, fields, models


class AccountMove(models.Model):
    """Extends the 'account.move' model to include additional fields and
    methods for managing account barcodes."""
    _inherit = "account.move"

    account_barcode = fields.Char(string='Account Barcode',
                                  help='Enter the barcode associated with this'
                                       'account.')

    @api.model
    def create(self, vals):
        """Changed variable name from res.account_barcode to
           self.account_barcode"""
        res = super(AccountMove, self).create(vals)
        ean = self.generate_ean(str(res.id))
        self.account_barcode = ean
        return res

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
        for i in range(len(final_ean)):
            if i % 2 == 0:
                odd_sum += int(final_ean[i])
            else:
                even_sum += int(final_ean[i])
        total = (odd_sum * 3) + even_sum
        check = int(10 - math.ceil(total % 10.0)) % 10
        return check

    def check_ean(self, ean_code):
        """Returns True if ean_code is a valid ean13 string, or null"""
        if not ean_code:
            return True
        if len(ean_code) != 13:
            return False
        try:
            int(ean_code)
        except:
            return False
        return self.ean_checksum(ean_code) == int(ean_code[-1])

    def generate_ean(self, ean):
        """Creates and returns a valid ean13 from an invalid one"""
        if not ean:
            return "0000000000000"
        ean_code = re.sub("[A-Za-z]", "0", ean)
        ean_code = re.sub("[^0-9]", "", ean_code)
        ean_code = ean_code[:13]
        if len(ean_code) < 13:
            ean_code = ean_code + '0' * (13 - len(ean_code))
        return ean_code[:-1] + str(self.ean_checksum(ean_code))
