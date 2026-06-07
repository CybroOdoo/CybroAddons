# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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

    pipedrive_reference = fields.Char(string='Pipedrive Reference',
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

        if self.env.company.product_synced:
            for rec in res:
                # Skip if already has pipedrive reference or already synced
                if rec.pipedrive_reference or self.env['pipedrive.record'].search([
                    ('record_type', '=', 'product'),
                    ('odoo_ref', '=', rec.id)
                ]):
                    continue

                # Calculate total tax percentage
                total_percentage_tax = 0.0
                if rec.taxes_id:
                    for tax in rec.taxes_id:
                        if tax.amount_type == 'percent':
                            total_percentage_tax += tax.amount
                        elif tax.amount_type == 'group':
                            for child_tax in tax.children_tax_ids:
                                if child_tax.amount_type == 'percent':
                                    total_percentage_tax += child_tax.amount
                        elif tax.amount_type == 'fixed':
                            if rec.list_price:
                                total_percentage_tax += (tax.amount / rec.list_price) * 100
                # Prepare data for Pipedrive
                data = {
                    'name': rec.name,
                    'tax': total_percentage_tax,
                    'prices': [{
                        'price': rec.list_price,
                        'currency': self.env.company.currency_id.name,
                        'cost': rec.standard_price
                    }]
                }
                if rec.uom_id:
                    data['unit'] = rec.uom_id.name
                # Create product in Pipedrive
                response = requests.post(
                    url='https://api.pipedrive.com/v1/products',
                    params={
                        'api_token': self.env.company.api_key,
                    }, json=data, timeout=10)

                response_data = response.json()
                if not response_data.get('success'):
                    error_msg = response_data.get('error', 'Unknown error')
                    error_info = response_data.get('error_info', '')
                    raise ValidationError(f"{error_msg}. {error_info}")

                pipedrive_id = str(response_data['data']['id'])
                rec.pipedrive_reference = pipedrive_id
                self.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': pipedrive_id,
                    'record_type': 'product',
                    'odoo_ref': rec.id
                })
        return res
