# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import json
import requests
from odoo.exceptions import UserError
from odoo import fields, models, _


class AssetAccountWizard(models.TransientModel):
    """A class that represents a transient model asset account wizard"""
    _name = "asset.account.product"
    _description = "Asset Account Wizard"

    product_ids = fields.Many2many("product.product",
                                   string="Products",
                                   help='All the products')
    account_type_id = fields.Many2one("account.account",
                                      string="Account Type",
                                      help='The account type')

    def get_import_query(self):
        """Fetch the import query"""
        quick_book = self.env['quickbooks.connector'].search(
            [('authorised', '=', True)])
        if quick_book.quickbooks_access_token:
            headers = {
                'Authorization': 'Bearer ' + quick_book.quickbooks_access_token,
                'Accept': 'application/json',
                'Content-Type': 'text/plain'
            }
            request_url = quick_book.quickbooks_api_url + quick_book.quickbooks_realm
            return {
                'url': request_url,
                'headers': headers
            }
        else:
            return False

    def action_export_products(self):
        """Function to export products"""
        url = self.get_import_query()
        total = 0
        if url:
            req_url = f'{url["url"]}/item?minorversion=40'
            headers = url.get('headers')
            headers['Content-Type'] = 'application/json'
            for product in self.product_ids:
                if product.qbooks_product:
                    continue
                else:
                    total += 1
                    self.create_product_data(product, req_url, headers)
        if total != 0:
            message = f'{total} products exported'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }

    def create_product_data(self, product, url, headers):
        """Function to create product data"""
        product_type = {
            'service': 'Service',
            'consu': 'NonInventory',
            'product': 'Inventory',
        }
        req_body = {
            "Name": product.name + '[CODE-' + str(product.id) + ']',
            "Description": product.description_sale,
            "Active": True,
            "UnitPrice": product.list_price,
            "PurchaseCost": product.standard_price,
            "Type": product_type.get(product.type),
            "PurchaseDesc": product.description_purchase,
            "IncomeAccountRef": {
                "value": product.categ_id.property_account_income_categ_id.qbooks_account
                if product.categ_id.property_account_income_categ_id.qbooks_account else '',
                "name": "Product Sales"
            },
            "AssetAccountRef": {
                "value": self.account_type_id.qbooks_account,
                "name": self.account_type_id.name
            },
            "ExpenseAccountRef": {
                "name": "Expenses",
                "value": product.categ_id.property_account_expense_categ_id.qbooks_account
                if product.categ_id.property_account_income_categ_id.qbooks_account else ''
            },
            "InvStartDate": "2022-03-19"
        }
        if product_type.get(product.type) == 'Inventory':
            quantity = (self.env['stock.quant'].search([]).filtered(
                lambda r: r.product_id.id ==
                          product.id and r.quantity > 0).mapped(
                'quantity'))
            if quantity:
                req_body.update({
                    "TrackQtyOnHand": True,
                    "QtyOnHand": sum(quantity)
                })
            else:
                req_body.update({
                    "TrackQtyOnHand": True,
                    "QtyOnHand": 0
                })
        else:
            req_body.update({"TrackQtyOnHand": False})
        response = requests.post(url, data=json.dumps(req_body),
                                 headers=headers)
        if response.json():
            if response.json().get('Item'):
                res = response.json().get('Item')
                if 'Id' in res:
                    product.write({
                        'qbooks_product': res.get('Id'),
                        'qbooks_sync_token': res.get('SyncToken')
                    })
            elif response.json().get('fault') and \
                    response.json().get('fault').get('error')[0].get(
                        'code') == '3200':
                raise UserError(_("Token expired. Kindly refresh token"))
