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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Inherits Res Company for including Pipedrive credential fields"""
    _inherit = 'res.company'

    api_key = fields.Char(string='Token',
                          help="It is used to connect with Pipedrive"
                          )
    import_product = fields.Boolean(string="Import Product",
                                    help="Check if you want to Import Products "
                                         "from Pipedrive")
    import_contact = fields.Boolean(string="Import Contact",
                                    help="Check if you want to Import Contacts "
                                         "from Pipedrive")
    import_lead = fields.Boolean(string="Import Lead",
                                 help="Check if you want to Import Leads from"
                                      " Pipedrive")
    export_product = fields.Boolean(string="Export Product",
                                    help="Check if you want to Export Products "
                                         "to Pipedrive")
    export_contact = fields.Boolean(string="Export Contact",
                                    help="Check if you want to Export Contacts"
                                         " to Pipedrive")
    export_lead = fields.Boolean(string="Export Lead",
                                 help="Check if you want to Export Leads to"
                                      " Pipedrive")
    pipedrive_reference = fields.Char(string='Pipedrive Id',
                                      help="Pipedrive Id of the Company")
    product_webhook = fields.Boolean(string='Product Webhook',
                                     help='True if update webhook for '
                                          'products is created')
    contact_webhook = fields.Boolean(string='Contact Webhook',
                                     help='True if update webhook for '
                                          'contact is created')

    def calculate_total_tax_percentage(self, product):
        """Method for calculating total tax"""
        total_percentage_tax = 0.0
        # Percentage Taxes
        for tax in product.taxes_id.filtered(
                lambda t: t.amount_type == 'percent'):
            total_percentage_tax += tax.amount
        # Group Taxes
        for tax in product.taxes_id.filtered(
                lambda t: t.amount_type == 'group'):
            for child_tax in tax.children_tax_ids.filtered(
                    lambda t: t.amount_type == 'percent'):
                total_percentage_tax += child_tax.amount
        # Fixed Taxes
        for tax in product.taxes_id.filtered(
                lambda t: t.amount_type == 'fixed'):
            total_percentage_tax += (tax.amount / product.list_price) * 100
        # Division Taxes
        for tax in product.taxes_id.filtered(
                lambda t: t.amount_type == 'division'):
            total_percentage_tax += (product.list_price / tax.factor) * 100
        return total_percentage_tax

    def action_execute(self):
        """For executing Import and Export between Odoo and Pipedrive"""
        if not self.api_key:
            raise ValidationError(_('Please Enter an API Key'))
        if self.import_product:
            self.get_products()
        if self.import_contact:
            self.get_contacts()
        if self.import_lead:
            self.get_leads()
        if self.export_product:
            self.export_products_to_pipedrive()
        if self.export_contact:
            self.export_contacts_to_pipedrive()
        if self.export_lead:
            self.export_leads_to_pipedrive()

    def get_products(self):
        """Receives Products from Pipedrive"""
        response = requests.get(url='https://api.pipedrive.com/v1/products',
                                params={
                                    'api_token': self.api_key,
                                }, timeout=10)
        if not response.json()['success']:
            raise ValidationError(
                response.json()['error'] + '. ' + response.json()[
                    'error_info'])
        if response.json()['data']:
            self.create_product_category()
            for data in response.json()['data']:
                pipedrive_reference = self.env['product.template'].search(
                    []).mapped(
                    'pipedrive_reference')
                if str(data['id']) not in pipedrive_reference:
                    if not self.product_webhook:
                        self.create_webhook(
                            'deleted',
                            '/delete_pipedrive_product',
                            'product')
                        self.create_webhook(
                            "updated",
                            '/update_pipedrive_product',
                            'product')
                    uom_id = 1
                    if data['unit']:
                        for rec in self.env['uom.uom'].search([]).mapped(
                                'name'):
                            if rec.lower() == data['unit'].lower():
                                uom_id = self.env['uom.uom'].search(
                                    [('name', '=', rec)]).id
                    if data['prices'][0]['price']:
                        currency = self.env['res.currency'].search(
                            [('name', '=', data['prices'][0]['currency']),
                             ('active', 'in', [True, False])])
                        if not currency.active:
                            currency.active = True
                    product = self.env['product.template'].create({
                        'name': data['name'],
                        'description': data['description'],
                        'uom_id': uom_id,
                        'uom_po_id': uom_id,
                        'list_price': data['prices'][0]['price'],
                        'standard_price': data['prices'][0]['cost'],
                        'taxes_id': False,
                        'pipedrive_reference': data['id'],
                        'categ_id': self.env['product.category'].search([(
                            'pipedrive_reference', '=', data['category'])]).id
                        if data['category'] else 1
                    })
                    product.taxes_id.unlink()
                    if data['tax'] != 0:
                        tax = self.env['account.tax'].search(
                            [('amount_type', '=', 'percent'),
                             ('type_tax_use', '=', 'sale'), ('amount',
                                                             '=',
                                                             data['tax'])])
                        if not tax:
                            tax = self.env['account.tax'].create({
                                'name': 'Tax ' + str(data['tax']) + '%',
                                'amount_type': 'percent',
                                'type_tax_use': 'sale',
                                'amount': data['tax']
                            })
                        product.write({
                            "taxes_id": [(4, tax.id)]
                        })

    def create_product_category(self):
        """Returns product category from category_id"""
        response = requests.get(
            url='https://api.pipedrive.com/v1/productFields',
            params={
                'api_token': self.api_key,
            }, timeout=10)
        if not response.json()['success']:
            raise ValidationError(
                response.json()['error'] + '. ' + response.json()[
                    'error_info'])
        for rec in response.json()['data']:
            if rec['key'] == 'category':
                for item in rec['options']:
                    category = self.env['product.category'].search(
                        [('name', '=', item['label'])])
                    if not category:
                        self.env['product.category'].create(
                            {
                                'name': item['label'],
                                'pipedrive_reference': item['id']
                            }
                        )
                    else:
                        category.write({
                            'pipedrive_reference': item['id']
                        })

    def get_contacts(self):
        """Receives contacts from Pipedrive"""
        response = requests.get(url='https://api.pipedrive.com/v1/persons',
                                params={
                                    'api_token': self.api_key,
                                }, timeout=10)
        if not response.json()['success']:
            raise ValidationError(
                response.json()['error'] + '. ' + response.json()[
                    'error_info'])
        if response.json()['data']:
            for data in response.json()['data']:
                partner_id = self.env['res.partner'].search([]).mapped(
                    'pipedrive_reference')
                if str(data['id']) not in partner_id:
                    self.env['res.partner'].create({
                        'name': data['name'],
                        'phone': data['phone'][0]['value'],
                        'email': data['email'][0]['value'],
                        'pipedrive_reference': data['id']
                    })
                if not self.contact_webhook:
                    self.create_webhook(
                        'updated', '/update_pipedrive_contact',
                        'person')
                    self.create_webhook(
                        'deleted', '/delete_pipedrive_contact',
                        'person')

    def get_leads(self):
        """Receives leads from Pipedrive"""
        response = requests.get(url='https://api.pipedrive.com/v1/leads',
                                params={
                                    'api_token': self.api_key,
                                }, timeout=10)
        if not response.json()['success']:
            raise ValidationError(
                response.json()['error'] + '. ' + response.json()[
                    'error_info'])
        if response.json()['data']:
            for data in response.json()['data']:
                lead_id = self.env['crm.lead'].search([]).mapped(
                    'pipedrive_reference')
                expected_revenue = 0
                if data['value']:
                    currency = self.env['res.currency'].search(
                        [('name', '=', data['value']['currency']),
                         ('active', 'in', [True, False])])
                    if not currency.active:
                        currency.active = True
                    expected_revenue = currency.compute(
                        data['value']['amount'], self.env.company.currency_id)
                if str(data['id']) not in lead_id:
                    self.env['crm.lead'].create({
                        'name': data['title'],
                        'type': 'opportunity',
                        'expected_revenue': expected_revenue,
                        'pipedrive_reference': data['id']
                    })

    def export_products_to_pipedrive(self):
        """Export Products from Odoo to Pipedrive"""
        for product in self.env['product.template'].search(
                [('pipedrive_reference', '=', False)]):
            data = {
                'name': product.name,
                'unit': product.uom_id.name,
                'tax': self.calculate_total_tax_percentage(product),
                'prices': [{
                    'price': product.list_price,
                    'currency': self.env.company.currency_id.name
                }]
            }
            response = requests.post(
                url='https://api.pipedrive.com/v1/products',
                params={
                    'api_token': self.api_key,
                }, json=data, timeout=10)
            if not response.json()['success']:
                raise ValidationError(
                    response.json()['error'] + '. ' + response.json()[
                        'error_info'])
            product.write(
                {'pipedrive_reference': response.json()['data']['id']})
            if not self.product_webhook:
                self.create_webhook(
                    'updated', '/update_pipedrive_product',
                    'product')
                self.create_webhook(
                    'deleted', '/delete_pipedrive_product',
                    'product')

    def export_contacts_to_pipedrive(self):
        """Export Contacts from Odoo to Pipedrive"""
        for partner in self.env['res.partner'].search(
                [('pipedrive_reference', '=', False)]):
            self.create_contact(partner)

    def create_contact(self, partner):
        """Create Persons in Pipedrive"""
        data = {
            'name': partner.name,
            'email': partner.email,
            'phone': partner.phone
        }
        response = requests.post(
            url='https://api.pipedrive.com/v1/persons',
            params={
                'api_token': self.api_key,
            }, json=data, timeout=10)
        if not response.json()['success']:
            raise ValidationError(
                response.json()['error'] + '. ' + response.json()[
                    'error_info'])
        partner.sudo().write(
            {'pipedrive_reference': response.json()['data']['id']})
        if not self.contact_webhook:
            self.create_webhook(
                'updated', '/update_pipedrive_contact',
                'person')
            self.create_webhook(
                'deleted', '/delete_pipedrive_contact',
                'person')
        return response.json()['data']['id']

    def create_webhook(self, event_action, url, event_object):
        """Method for creating contact webhook in Pipedrive"""
        payload = json.dumps({
            "subscription_url": self.env['ir.config_parameter'].get_param(
                'web.base.url') + url,
            "event_action": event_action,
            "event_object": event_object
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        params = {
            'api_token': self.api_key,
        }
        response = requests.request("POST",
                                    "https://api.pipedrive.com/v1/"
                                    "webhooks",
                                    headers=headers, data=payload,
                                    params=params,
                                    timeout=10)
        if not response.json()['success']:
            if 'error' in response.json().keys():
                raise ValidationError(
                    response.json()['error'])
            if 'message' in response.json().keys():
                raise ValidationError(
                    response.json()['message'])
        if event_object == 'person':
            self.contact_webhook = True
        elif event_object == 'product':
            self.product_webhook = True

    def export_leads_to_pipedrive(self):
        """Export Leads from Odoo to Pipedrive"""
        for lead in self.env['crm.lead'].search(
                [('pipedrive_reference', '=', False),
                 ('partner_id', '!=', False)]):
            if not lead.partner_id.pipedrive_reference:
                self.create_contact(lead.partner_id)
            data = {
                'title': lead.name,
                'person_id': int(lead.partner_id.pipedrive_reference),
                'value': {
                    'amount': lead.expected_revenue,
                    'currency': self.env.company.currency_id.name
                }
            }
            response = requests.post(
                url='https://api.pipedrive.com/v1/leads',
                params={
                    'api_token': self.api_key,
                }, json=data, timeout=10)
            if not response.json()['success']:
                raise ValidationError(
                    response.json()['error'] + '. ' + response.json()[
                        'error_info'])
            lead.write(
                {'pipedrive_reference': response.json()['data']['id']})
