# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherits product template for including Pipedrive fields and
    functions"""
    _inherit = 'product.template'

    pipedrive_reference = fields.Char(help="Pipedrive Id of the Product")

    def write(self, vals):
        """Inherited to update the Pipedrive product."""
        # Changes coming from Pipedrive must not be pushed back to it
        if (self.env.context.get('update_from_pipedrive') or
                self.env.context.get('skip_pipedrive_sync')):
            return super().write(vals)
        data = {}
        if 'name' in vals.keys():
            data['name'] = vals['name']
        if 'uom_id' in vals.keys():
            data['unit'] = self.env['uom.uom'].browse(vals['uom_id']).name
        taxes = self.env['account.tax']
        if 'taxes_id' in vals.keys():
            if vals['taxes_id'] and isinstance(vals['taxes_id'][0], list):
                taxes = self.env['account.tax'].sudo().search(
                    [('id', 'in', vals['taxes_id'][0][2])])
        if 'list_price' in vals.keys():
            data['prices'] = [{'price': vals['list_price'],
                               'currency': self.env.company.currency_id.name}
                              ]
        for rec in self:
            pipedrive_product = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'product'), ('odoo_ref', '=', rec.id)])
            rec_data = dict(data)
            if taxes:
                rec_data['tax'] = sum(
                    rec.calculate_total_tax_percentage(tax) for tax in taxes)
            if pipedrive_product and rec_data:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.put(
                    url=f'https://api.pipedrive.com/v1/products/'
                        f'{pipedrive_product.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers, data=json.dumps(rec_data))
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
            if self.list_price:
                total_percentage_tax = (tax.amount / self.list_price) * 100
        # Division Taxes
        else:
            total_percentage_tax = tax.amount
        return total_percentage_tax

    @api.ondelete(at_uninstall=False)
    def _unlink_pipedrive_product(self):
        """Delete the product from Pipedrive before it is removed from Odoo"""
        for rec in self:
            pipedrive_product = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'product'), ('odoo_ref', '=', rec.id)])
            if pipedrive_product:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.delete(
                    url=f'https://api.pipedrive.com/v1/products/'
                        f'{pipedrive_product.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers)
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])

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
                    raise ValidationError(self.env._(
                        "%(error)s. %(info)s",
                        error=error_msg, info=error_info))

                pipedrive_id = str(response_data['data']['id'])
                rec.pipedrive_reference = pipedrive_id
                self.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': pipedrive_id,
                    'record_type': 'product',
                    'odoo_ref': rec.id
                })
        return res
