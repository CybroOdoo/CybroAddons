# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
import re
from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherit the account_move module to add new fields and functions"""
    _inherit = "account.move"

    account_barcode = fields.Char(string='Barcode',
                                  help='Barcode associated with the account '
                                       'move.')

    @api.model
    def create(self, vals):
        """Super the create function to It generates an EAN barcode based on
        the ID of the created record and assigns it to the `account_barcode`
         field."""
        res = super(AccountMove, self).create(vals)
        res.account_barcode = self.generate_ean(str(res.id))
        return res

    def ean_checksum(self, eancode):
        """Returns the checksum of an ean string of length 13, returns -1 if
        the string has the wrong length"""
        if len(eancode) != 13:
            return -1
        oddsum = 0
        evensum = 0
        finalean = eancode[::-1][1:]
        for i in range(len(finalean)):
            if i % 2 == 0:
                oddsum += int(finalean[i])
            else:
                evensum += int(finalean[i])
        return int(10 - math.ceil((oddsum * 3) + evensum % 10.0)) % 10

    def check_ean(eancode):
        """Returns True if eancode is a valid ean13 string, or null"""
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
        """Creates and returns a valid ean13 from an invalid one"""
        if not ean:
            return "0000000000000"
        ean = re.sub("[A-Za-z]", "0", ean)
        ean = re.sub("[^0-9]", "", ean)
        ean = ean[:13]
        if len(ean) < 13:
            ean = ean + '0' * (13 - len(ean))
        return ean[:-1] + str(self.ean_checksum(ean))
