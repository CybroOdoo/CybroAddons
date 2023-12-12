# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
import json
import requests
from odoo import fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherits product template for including Pipedrive fields and
    functions"""
    _inherit = 'product.template'

    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive Id of the Product")

    def write(self, vals):
        """Inherited to update the Pipedrive product."""
        data = {}
        if 'name' in vals.keys():
            data['name'] = vals['name']
        if 'uom_id' in vals.keys():
            data['unit'] = self.env['uom.uom'].browse(vals['uom_id']).name
        if 'taxes_id' in vals.keys():
            if vals['taxes_id'] and isinstance(vals['taxes_id'][0], list):
                total_tax = 0.0
                for tax in self.env['account.tax'].search(
                        [('id', 'in', vals['taxes_id'][0][2])]):
                    total_tax += self.calculate_total_tax_percentage(tax)
                data['tax'] = total_tax
        if 'list_price' in vals.keys():
            data['prices'] = [{'price': vals['list_price'],
                               'currency': self.env.company.currency_id.name}
                              ]
        if self.pipedrive_reference and data:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.put(
                url=f'https://api.pipedrive.com/v1/products/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers, data=json.dumps(data))
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().write(vals)

    def calculate_total_tax_percentage(self, tax):
        """Method for calculating total tax"""
        total_percentage_tax = 0.0
        # Percentage Taxes
        if tax.amount_type == 'percent':
            total_percentage_tax = tax.amount
        # Group Taxes
        elif tax.amount_type == 'group':
            for child_tax in tax.children_tax_ids.filtered(
                    lambda t: t.amount_type == 'percent'):
                total_percentage_tax += child_tax.amount
        # Fixed Taxes
        elif tax.amount_type == 'fixed':
            total_percentage_tax = (tax.amount / tax.list_price) * 100
        # Division Taxes
        else:
            total_percentage_tax = (tax.list_price / tax.factor) * 100
        return total_percentage_tax

    def unlink(self):
        """Method for deleting a product from Pipedrive"""
        if self.pipedrive_reference:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.delete(
                url=f'https://api.pipedrive.com/v1/products/'
                    f'{self.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers)
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().unlink()
