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
#############################################################################
import math
import re
from odoo import api, fields, models


class AccountMove(models.Model):
    """
    Extends 'account.move' model to add custom fields and methods related to
    EAN generation and validation.
    """
    _inherit = "account.move"

    account_barcode = fields.Char(
        string='Account Barcode',
        help='Barcode associated with the account move.')

    @api.model
    def create(self, vals):
        """
        Overrides the 'create' method to generate and assign a valid EAN13
        barcode to the account move.
        vals: Dictionary of field values for creating the account move.
        return: Created account move record with the assigned EAN13 barcode.
        """
        res = super(AccountMove, self).create(vals)
        ean = self.generate_ean(str(res.id))
        res.account_barcode = ean
        return res

    def ean_checksum(self, eancode):
        """
        Calculates the checksum digit of an EAN13 string.
        eancode: EAN13 string without the last digit.
        return: Checksum digit.
        """
        if len(eancode) != 13:
            return -1
        oddsum = 0
        evensum = 0
        eanvalue = eancode
        reversevalue = eanvalue[::-1]
        finalean = reversevalue[1:]
        for i in range(len(finalean)):
            if i % 2 == 0:
                oddsum += int(finalean[i])
            else:
                evensum += int(finalean[i])
        total = (oddsum * 3) + evensum
        check = int(10 - math.ceil(total % 10.0)) % 10
        return check

    def check_ean(self, eancode):
        """
        Checks if an EAN13 string is valid.
        eancode: EAN13 string to be validated.
        return: True if the EAN13 string is valid, False otherwise.
        """
        if not eancode:
            return True
        if len(eancode) != 13:
            return False
        try:
            int(eancode)
        except:
            return False
        return eancode.ean_checksum(eancode) == int(eancode[-1])

    def generate_ean(self, ean):
        """
        Generates a valid EAN13 barcode from an input string.
        ean: Input string for generating the EAN13 barcode.
        return: Valid EAN13 barcode.
        """
        if not ean:
            return "0000000000000"
        ean = re.sub("[A-Za-z]", "0", ean)
        ean = re.sub("[^0-9]", "", ean)
        ean = ean[:13]
        if len(ean) < 13:
            ean = ean + '0' * (13 - len(ean))
        return ean[:-1] + str(self.ean_checksum(ean))
