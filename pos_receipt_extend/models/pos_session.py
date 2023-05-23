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
import re

from odoo import models, fields, api
import math


class PosSessionLoadFields(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result += [
            'res.config.settings',

        ]
        return result

    def _loader_params_res_config_settings(self):
        return {
            'search_params': {
                'fields': ['qr_code', 'invoice_number', 'customer_name',
                           'customer_address', 'customer_mobile',
                           'customer_phone', 'customer_email', 'customer_vat'],

            },
        }

    def _get_pos_ui_res_config_settings(self, params):
        return self.env['res.config.settings'].search_read(
            **params['search_params'])


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sale_barcode = fields.Char()

    @api.model
    def get_invoice(self, id):
        pos_id = self.search([('pos_reference', '=', id)])
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        invoice_id = self.env['account.move'].search(
            [('ref', '=', pos_id.name)])
        return {
            'invoice_id': invoice_id.id,
            'invoice_name': invoice_id.name,
            'base_url': base_url,
            'qr_code': invoice_id.account_barcode,
        }


class AccountMove(models.Model):
    _inherit = "account.move"

    account_barcode = fields.Char()

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        ean = self.generate_ean(str(res.id))
        res.account_barcode = ean
        return res

    def ean_checksum(self, eancode):
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
