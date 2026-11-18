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


class ProductCategory(models.Model):
    """Inherits product_category for including Pipedrive fields and functions"""
    _inherit = 'product.category'

    pipedrive_reference = fields.Char(help="Pipedrive Id of the Category")

    def write(self, vals):
        """Inherited to update product field in pipedrive"""
        for rec in self:
            pipedrive_categ = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'categ'), ('odoo_ref', '=', rec.id)])
            if 'name' in vals.keys() and pipedrive_categ:
                data = {'label': vals['name']}
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.put(
                    url=f'https://api.pipedrive.com/v1/productFields/'
                        f'{rec.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers, data=json.dumps(data))
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_pipedrive_category(self):
        """Delete the product field from Pipedrive before the category is
        removed from Odoo"""
        for rec in self:
            pipedrive_categ = self.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'categ'), ('odoo_ref', '=', rec.id)])
            if pipedrive_categ:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                response = requests.delete(
                    url=f'https://api.pipedrive.com/v1/productFields/'
                        f'{rec.pipedrive_reference}',
                    params={
                        'api_token': self.env.company.api_key,
                    }, timeout=10, headers=headers)
                if 'error' in response.json().keys():
                    raise ValidationError(
                        response.json()['error'])
