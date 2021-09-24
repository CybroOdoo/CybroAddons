# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy and Sreejith P (odoo@cybrosys.com)
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

import math
import re
from odoo import api, models


class ProductAutoBarcode(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(ProductAutoBarcode, self).create(vals)
        barcode_id = res.id
        barcode_search = False
        while not barcode_search:
            ean = generate_ean(str(barcode_id))
            if self.env['product.product'].search([('barcode', '=', ean)]):
                barcode_search = False
                barcode_id += 1
            else:
                barcode_search = True
        res.barcode = ean
        return res


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
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


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '0' * (13 - len(ean))
    print("barcode : ", ean[:-1] + str(ean_checksum(ean)))
    return ean[:-1] + str(ean_checksum(ean))


class ProductTemplateAutoBarcode(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals_list):
        templates = super(ProductTemplateAutoBarcode, self).create(vals_list)
        barcode_id = templates.id
        barcode_search = False
        while not barcode_search:
            ean = generate_ean(str(barcode_id))
            if self.env['product.product'].search([('barcode', '=', ean)]):
                barcode_search = False
                barcode_id += 1
            else:
                barcode_search = True
        templates.barcode = ean
        return templates


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
