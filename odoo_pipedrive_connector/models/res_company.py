# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import requests
from odoo import fields, models
from odoo.tools import _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Inherits Res Company for including Pipedrive credential fields"""
    _inherit = 'res.company'

    api_key = fields.Char(string='Token',
                          help="It is used to connect with Pipedrive"
                          )
    product_synced = fields.Boolean(string='Product Synced', readonly=True,
                                    help='True if the products are synced between Odoo and Pipedrive')
    contact_synced = fields.Boolean(string='Contact Synced', readonly=True,
                                    help='True if the contacts are synced between Odoo and Pipedrive')
    lead_synced = fields.Boolean(string='Lead Synced', readonly=True,
                                 help='True if the leads are synced between Odoo and Pipedrive')

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

    def action_sync_products(self):
        """Synchronize products between Odoo and Pipedrive."""
        if not self.api_key:
            raise ValidationError(_('Please Enter an API Key'))
        self.get_products()
        self.export_products_to_pipedrive()
        self.create_webhook(
            'delete',
            '/delete_pipedrive_product',
            'product')

        self.create_webhook(
            'change',
            '/update_pipedrive_product',
            'product')

        self.create_webhook(
            'create',
            '/add_pipedrive_product',
            'product')

        self.product_synced = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Products synced successfully with Pipedrive"),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_contacts(self):
        """Synchronize contacts between Odoo and Pipedrive."""
        if not self.api_key:
            raise ValidationError(_('Please Enter an API Key'))
        self.get_contacts()
        self.export_contacts_to_pipedrive()
        self.create_webhook(
            'change', '/update_pipedrive_contact',
            'person')
        self.create_webhook(
            'delete', '/delete_pipedrive_contact',
            'person')
        self.create_webhook(
            'create', '/add_pipedrive_contact',
            'person')
        self.contact_synced = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Contacts synced successfully with Pipedrive"),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_leads(self):
        """Synchronize leads between Odoo and Pipedrive."""
        if not self.api_key:
            raise ValidationError(_('Please Enter an API Key'))
        self.get_leads()
        self.export_leads_to_pipedrive()
        self.lead_synced = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Leads synced successfully with Pipedrive"),
                'type': 'success',
                'sticky': False,
            }
        }

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
                if not self.env['pipedrive.record'].sudo().search(
                        [('pipedrive_reference', '=', str(data['id'])), ('record_type', '=', 'product')]):
                    uom_id = 1
                    if data['unit']:
                        for rec in self.env['uom.uom'].sudo().search([]).mapped(
                                'name'):
                            if rec.lower() == data['unit'].lower():
                                uom_id = self.env['uom.uom'].sudo().search(
                                    [('name', '=', rec)]).id
                    if data['prices'][0]['price']:
                        currency = self.env['res.currency'].sudo().search(
                            [('name', '=', data['prices'][0]['currency']),
                             ('active', 'in', [True, False])])
                        if not currency.active:
                            currency.active = True
                    product = self.env['product.template'].sudo().create({
                        'name': data['name'],
                        'description': data['description'],
                        'uom_id': uom_id,
                        'uom_po_id': uom_id,
                        'list_price': data['prices'][0]['price'],
                        'standard_price': data['prices'][0]['cost'],
                        'taxes_id': False,
                        'categ_id': self.env['pipedrive.record'].sudo().search(
                            [(
                                'pipedrive_reference', '=',
                                data['category'])])[0].odoo_ref
                        if self.env['pipedrive.record'].sudo().search(
                            [(
                                'pipedrive_reference', '=',
                                data['category'])]) else 1
                    })
                    if product:
                        self.env['pipedrive.record'].sudo().create({
                            'pipedrive_reference': data['id'],
                            'record_type': 'product',
                            'odoo_ref': product.id
                        })
                        product.taxes_id.unlink()
                        if data['tax'] != 0:
                            tax = self.env['account.tax'].sudo().search(
                                [('amount_type', '=', 'percent'),
                                 ('type_tax_use', '=', 'sale'), ('amount',
                                                                 '=',
                                                                 data['tax'])])
                            if not tax:
                                tax = self.env['account.tax'].sudo().create({
                                    'name': 'Tax ' + str(data['tax']) + '%',
                                    'amount_type': 'percent',
                                    'type_tax_use': 'sale',
                                    'amount': data['tax']
                                })
                            product.sudo().write({
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
                    category = self.env['product.category'].sudo().search(
                        [('name', '=', item['label'])])
                    if not category:
                        category = self.env['product.category'].sudo().create(
                            {
                                'name': item['label']
                            }
                        )
                        self.env['pipedrive.record'].sudo().create({
                            'pipedrive_reference': item['id'],
                            'record_type': 'categ',
                            'odoo_ref': category[0].id
                        })
                    elif not self.env['pipedrive.record'].sudo().search(
                            [('record_type', '=', 'categ'), ('odoo_ref', '=', category[0].id)]):
                        self.env['pipedrive.record'].sudo().create({
                            'pipedrive_reference': item['id'],
                            'record_type': 'categ',
                            'odoo_ref': category[0].id
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
                pipedrive_reference = str(data['id'])
                pipedrive_record = self.env['pipedrive.record'].sudo().search(
                    [('pipedrive_reference', '=', pipedrive_reference),
                     ('record_type', '=', 'partner')], limit=1)
                if pipedrive_record:
                    continue
                email = data['email'][0]['value'] if data['email'] else False
                phone = data['phone'][0]['value'] if data['phone'] else False
                partner_domain = []
                if email:
                    partner_domain.append(('email', '=', email))
                if phone:
                    partner_domain = ['|'] + partner_domain + [
                        ('phone', '=', phone)] if partner_domain else [
                        ('phone', '=', phone)]
                partner = self.env['res.partner'].sudo().search(
                    partner_domain, limit=1) if partner_domain else False
                if not partner:
                    partner = self.env['res.partner'].with_context(
                        skip_pipedrive_sync=True).sudo().create({
                            'name': data['name'],
                            'phone': phone,
                            'email': email,
                            'pipedrive_reference': pipedrive_reference
                        })
                elif not partner.pipedrive_reference:
                    partner.with_context(skip_pipedrive_sync=True).sudo().write({
                        'pipedrive_reference': pipedrive_reference
                    })
                existing_partner_record = self.env['pipedrive.record'].sudo().search([
                    ('record_type', '=', 'partner'),
                    ('odoo_ref', '=', partner.id)
                ], limit=1) if partner else False
                if partner and not existing_partner_record:
                    self.env['pipedrive.record'].sudo().create({
                        'pipedrive_reference': pipedrive_reference,
                        'record_type': 'partner',
                        'odoo_ref': partner.id
                    })

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
                expected_revenue = 0
                if data['value']:
                    currency = self.env['res.currency'].sudo().search(
                        [('name', '=', data['value']['currency']),
                         ('active', 'in', [True, False])])
                    if not currency.active:
                        currency.active = True
                    expected_revenue = currency._convert(
                        data['value']['amount'],
                        self.env.company.currency_id,
                        self.env.company,
                        fields.Date.today()
                    )

                if not self.env['pipedrive.record'].sudo().search(
                        [('pipedrive_reference', '=', str(data['id'])), ('record_type', '=', 'lead')]):
                    lead = self.env['crm.lead'].sudo().create({
                        'name': data['title'],
                        'type': 'opportunity',
                        'expected_revenue': expected_revenue
                    })
                    self.env['pipedrive.record'].sudo().create({
                        'pipedrive_reference': data['id'],
                        'record_type': 'lead',
                        'odoo_ref': lead.id
                    })

    def export_products_to_pipedrive(self):
        """Export Products from Odoo to Pipedrive"""
        pipedrive_products = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product')]).mapped('odoo_ref')
        for product in self.env['product.template'].sudo().search(
                [('id', 'not in', pipedrive_products)]):
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
            self.env['pipedrive.record'].sudo().create({
                'pipedrive_reference': response.json()['data']['id'],
                'record_type': 'product',
                'odoo_ref': product.id
            })

    def export_contacts_to_pipedrive(self):
        """Export Contacts from Odoo to Pipedrive"""
        pipedrive_partner = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner')]).mapped('odoo_ref')
        for partner in self.env['res.partner'].sudo().search(
                [('id', 'not in', pipedrive_partner)]):
            self.create_contact(partner)

    def create_contact(self, partner):
        """Create Persons in Pipedrive"""
        pipedrive_record = self.env['pipedrive.record'].sudo().search([
            ('record_type', '=', 'partner'),
            ('odoo_ref', '=', partner.id)
        ], limit=1)
        if pipedrive_record:
            return pipedrive_record
        if partner.pipedrive_reference:
            return self.env['pipedrive.record'].sudo().create({
                'pipedrive_reference': partner.pipedrive_reference,
                'record_type': 'partner',
                'odoo_ref': partner.id
            })
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
        if 'success' in response.json(
        ).keys() and not response.json()['success'] and 'error' in \
                response.json(
                ).keys():
            raise ValidationError(
                response.json()['error'])
        pipedrive_reference = response.json()['data']['id']
        pipedrive_record = self.env['pipedrive.record'].sudo().create({
            'pipedrive_reference': pipedrive_reference,
            'record_type': 'partner',
            'odoo_ref': partner.id
        })
        partner.with_context(skip_pipedrive_sync=True).sudo().write({
            'pipedrive_reference': pipedrive_reference
        })
        return pipedrive_record

    def create_webhook(self, event_action, url, event_object):
        """Create a Pipedrive webhook when it does not already exist."""

        base_url = self.env['ir.config_parameter'].sudo().get_param("web.base.url")
        full_url = base_url + url


        payload = {
            "subscription_url": full_url,
            "event_action": event_action,
            "event_object": event_object
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        params = {"api_token": self.api_key}

        # First check existing webhooks
        existing = requests.get("https://api.pipedrive.com/v1/webhooks", params=params)

        for wh in (existing.json().get("data") or []):
            if (
                    wh.get("event_action") == event_action
                    and wh.get("event_object") == event_object
                    and wh.get("subscription_url") == full_url
            ):
                return

        response = requests.post(
            "https://api.pipedrive.com/v1/webhooks",
            params=params,
            json=payload,
            headers=headers,
            timeout=10
        )

        if not response.json().get("success"):
            raise ValidationError("Webhook creation failed: %s" % response.json())

    def export_leads_to_pipedrive(self):
        """Export Leads from Odoo to Pipedrive"""
        pipedrive_lead = self.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'lead')]).mapped('odoo_ref')
        for lead in self.env['crm.lead'].sudo().search(
                [('id', 'not in', pipedrive_lead)]):
            if lead.partner_id:
                if not self.env['pipedrive.record'].sudo().search(
                        [('record_type', '=', 'partner'), ('odoo_ref', '=', lead.partner_id.id)]):
                    self.create_contact(lead.partner_id)
                data = {
                    'title': lead.name,
                    'person_id': int(self.env['pipedrive.record'].sudo().search(
                        [('record_type', '=', 'partner'), ('odoo_ref', '=', lead.partner_id.id)]).pipedrive_reference),
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
                self.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': response.json()['data']['id'],
                    'record_type': 'lead',
                    'odoo_ref': lead.id
                })
