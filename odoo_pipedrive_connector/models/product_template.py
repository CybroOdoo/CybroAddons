# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherits product template for including Pipedrive fields ab=nd
    functions"""
    _inherit = 'product.template'

    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive Id of the Product")
    update_from_pipedrive = fields.Boolean(string='Update from Pipedrive',
                                           help="True if the update is from pipedrive")

    def write(self, vals):
        """Inherited to update the Pipedrive product."""
        data = {}
        if 'name' in vals.keys():
            data['name'] = vals['name']
        if 'uom_id' in vals.keys():
            data['unit'] = self.env['uom.uom'].browse(vals['uom_id']).name
        if 'taxes_id' in vals.keys():
            if vals['taxes_id'] and type(vals['taxes_id'][0]) == list:
                total_tax = 0.0
                for tax in self.env['account.tax'].sudo().search(
                        [('id', 'in', vals['taxes_id'][0][2])]):
                    total_tax += self.calculate_total_tax_percentage(tax)
                data['tax'] = total_tax
        if 'list_price' in vals.keys():
            data['prices'] = [{'price': vals['list_price'],
                               'currency': self.env.company.currency_id.name}
                              ]
        pipedrive_product = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product'), ('odoo_ref', '=', self.id)])
        if pipedrive_product and data:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.put(
                url=f'https://api.pipedrive.com/v1/products/'
                    f'{pipedrive_product.pipedrive_reference}',
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
        pipedrive_product = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product'), ('odoo_ref', '=', self.id)])
        if pipedrive_product:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.delete(
                url=f'https://api.pipedrive.com/v1/products/'
                    f'{pipedrive_product.pipedrive_reference}',
                params={
                    'api_token': self.env.user.company_id.api_key,
                }, timeout=10, headers=headers)
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited to add the product to pipedrive"""
        res = super().create(vals_list)
        if self.env.company.product_synced and not res.pipedrive_reference:
            if not self.env['pipedrive.record'].search(
                    [('record_type', '=', 'product',), ('odoo_ref', '=', res.id)]):
                for product in vals_list:
                    tax_ids = product.get('taxes_id', [])
                    total_percentage_tax = 0.0
                    if tax_ids:
                        for tax_id in tax_ids[0][2]:
                            tax = self.env['account.tax'].sudo().browse(tax_id)
                            if tax.amount_type == 'percent':
                                total_percentage_tax += tax.amount
                            elif tax.amount_type == 'group':
                                for child_tax in tax.children_tax_ids:
                                    if child_tax.amount_type == 'percent':
                                        total_percentage_tax += child_tax.amount
                            elif tax.amount_type == 'fixed':
                                total_percentage_tax += (tax.amount / product[
                                    'list_price']) * 100
                    data = {
                        'name': product['name'],
                        'tax': total_percentage_tax,
                        'code': product['default_code'],
                        'prices': [{
                            'price': product['list_price'],
                            'currency': self.env.company.currency_id.name,
                            'cost': product['standard_price']
                        }]
                    }
                    if 'uom_id' in product.keys():
                        data['unit'] = self.env['uom.uom'].sudo().browse(
                            product['uom_id']).name
                    response = requests.post(
                        url='https://api.pipedrive.com/v1/products',
                        params={
                            'api_token': self.env.company.api_key,
                        }, json=data, timeout=10)
                    if not response.json()['success']:
                        raise ValidationError(
                            response.json()['error'] + '. ' + response.json()[
                                'error_info'])
                    self.env['pipedrive.record'].sudo().create({
                        'pipedrive_reference': response.json()['data']['id'],
                        'record_type': 'product',
                        'odoo_ref': res.id
                    })
        return res
