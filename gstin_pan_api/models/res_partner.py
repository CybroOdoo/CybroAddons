# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-September Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: SREERAG E (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = "Adding the PAN field and GSTIN details"

    pan_response_ids = fields.One2many('pan.response.data', 'res_partner_id',
                                       string='PAN Response')
    pan = fields.Char(string="PAN")

    @api.onchange('pan')
    def validate_pan(self):
        """
        Validating the PAN format
        """
        val = str(self.pan)
        self.pan = val.upper()
        regex = "[A-Z]{5}[0-9]{4}[A-Z]{1}"
        pattern = re.compile(regex)
        if not ((re.search(pattern, self.pan) and
                 len(self.pan) == 10)):
            raise ValidationError("Invalid PAN format !")


class PanResponse(models.Model):
    _name = 'pan.response.data'
    _description = "For fetching the GSTIN info using PAN"

    res_partner_id = fields.Many2one('res.partner', string="Contact",
                                     readonly=True)
    gstin_id = fields.Char(string='GSTIN', readonly=True)
    address = fields.Text(string='Address', readonly=True)
    sl_no = fields.Integer(readonly=True)
