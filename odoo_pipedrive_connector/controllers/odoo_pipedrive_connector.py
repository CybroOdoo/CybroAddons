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
import hmac
from werkzeug.exceptions import Forbidden
from odoo import fields, http
from odoo.http import request
from odoo.fields import Command
from ..models.res_company import WEBHOOK_AUTH_USER


class PipedriveWebhook(http.Controller):
    """ This controller is responsible for receiving Webhooks from Pipedrive"""

    def _get_webhook_env(self):
        """Authenticate the webhook with the HTTP Basic credentials registered
        on Pipedrive and return a superuser env bound to the owning company.
        Data changes are flagged with update_from_pipedrive so they are not
        pushed back to Pipedrive."""
        auth = request.httprequest.authorization
        if not auth or auth.username != WEBHOOK_AUTH_USER or not auth.password:
            raise Forbidden()
        company = request.env['res.company'].sudo().search(
            [('pipedrive_webhook_token', '=', auth.password)], limit=1)
        if not company or not hmac.compare_digest(
                company.pipedrive_webhook_token, auth.password):
            raise Forbidden()
        return request.env(su=True, context=dict(
            request.env.context,
            allowed_company_ids=company.ids,
            update_from_pipedrive=True,
        ))

    @http.route('/update_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_product_details(self, **kw):
        """ Webhook for receiving the updates on products."""
        env = self._get_webhook_env()
        payload = json.loads(request.httprequest.data.decode('utf-8'))
        current = payload.get('data', {})
        if not current:
            return {"status": "no data"}
        uom_id = env.ref('uom.product_uom_unit').id
        if current.get('unit'):
            uom = env['uom.uom'].search(
                [('name', 'ilike', current['unit'])], limit=1
            )
            if uom:
                uom_id = uom.id
        pipedrive_product = env['pipedrive.record'].search([
            ('record_type', '=', 'product'),
            ('pipedrive_reference', '=', current['id'])
        ], limit=1)
        if not pipedrive_product:
            return {"status": "product not found"}
        product_template = env['product.template'].browse(
            pipedrive_product.odoo_ref
        )
        category_id = False
        if current.get('category'):
            pipedrive_categ = env['pipedrive.record'].search([
                ('record_type', '=', 'categ'),
                ('pipedrive_reference', '=', current['category'])
            ], limit=1)
            if pipedrive_categ:
                category_id = pipedrive_categ.odoo_ref
        list_price = standard_price = 0.0
        if current.get('prices'):
            price_data = current['prices'][0]
            currency = env['res.currency'].with_context(
                active_test=False).search(
                [('name', '=', price_data['currency'])], limit=1
            )
            if currency and not currency.active:
                currency.active = True
            list_price = currency._convert(
                price_data.get('price', 0),
                env.company.currency_id,
                env.company,
                fields.Date.today()
            )
            standard_price = currency._convert(
                price_data.get('cost', 0),
                env.company.currency_id,
                env.company,
                fields.Date.today()
            )
        update_values = {}
        if product_template.name != current.get('name'):
            update_values['name'] = current.get('name')
        if product_template.description != current.get('description'):
            update_values['description'] = current.get('description')
        if product_template.uom_id.id != uom_id:
            update_values['uom_id'] = uom_id
        if product_template.standard_price != standard_price:
            update_values['standard_price'] = standard_price
        if product_template.list_price != list_price:
            update_values['list_price'] = list_price
        if product_template.categ_id.id != category_id:
            update_values['categ_id'] = category_id
        if update_values:
            product_template.write(update_values)
        return {"status": "success"}

    @http.route('/add_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_added_product_details(self, **kw):
        """Webhook for receiving the new product details."""
        env = self._get_webhook_env()
        payload = json.loads(request.httprequest.data.decode('utf-8'))
        if payload['meta']['change_source'] == 'api':
            added_data = payload['data']
            env.company.create_product_category()
            uom = env.ref('uom.product_uom_unit').id
            currency = env['res.currency']
            if added_data['prices']:
                currency = env['res.currency'].search(
                    [('name', '=', added_data['prices'][0]['currency']),
                     ('active', 'in', [True, False])])
                if not currency.active:
                    currency.active = True
            if added_data['unit']:
                unit = env['uom.uom'].search(
                    [('name', '=ilike', added_data['unit'])], limit=1)
                if unit:
                    uom = unit.id
            pipedrive_categ = env['pipedrive.record'].search(
                [('record_type', '=', 'categ'),
                 ('pipedrive_reference', '=', added_data['category'])],
                limit=1) if added_data['category'] else False
            if not env['pipedrive.record'].search(
                    [('pipedrive_reference', '=', added_data['id']),
                     ('record_type', '=', 'product')]):
                product = env['product.template'].create({
                    'name': added_data['name'],
                    'description': added_data['description'],
                    'uom_id': uom,
                    'taxes_id': False,
                    'list_price': currency._convert(
                        added_data['prices'][0]['price'],
                        env.company.currency_id, env.company,
                        fields.Date.today()) if
                    added_data['prices'][0][
                        'price'] else 0.0,
                    'standard_price': currency._convert(
                        added_data['prices'][0]['cost'],
                        env.company.currency_id, env.company,
                        fields.Date.today()) if
                    added_data['prices'][0][
                        'cost'] else 0.0,
                    'categ_id': pipedrive_categ.odoo_ref
                    if pipedrive_categ else False,
                    'pipedrive_reference': added_data['id']
                })
                env['pipedrive.record'].create({
                    'pipedrive_reference': added_data['id'],
                    'record_type': 'product',
                    'odoo_ref': product.id
                })
                product.write(
                    {'taxes_id': [Command.clear()]})
                if added_data['tax'] != 0:
                    tax = env['account.tax'].search(
                        [('amount_type', '=', 'percent'),
                         ('type_tax_use', '=', 'sale'), ('amount',
                                                         '=',
                                                         added_data['tax'])])
                    if not tax:
                        tax = env['account.tax'].create({
                            'name': 'Tax ' + str(added_data['tax']) + '%',
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                            'amount': added_data['tax']
                        })
                    product.write({
                        "taxes_id": [Command.link(tax.id)]
                    })

    @http.route('/delete_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_deleted_product_details(self, **kw):
        """Webhook for receiving the deleted product details."""
        env = self._get_webhook_env()
        deleted_data = json.loads(request.httprequest.data.decode('utf-8'))
        product_id = deleted_data['meta']['entity_id']
        pipedrive_product = env['pipedrive.record'].search(
            [('record_type', '=', 'product'),
             ('pipedrive_reference', '=', product_id)])
        if pipedrive_product:
            product = env['product.template'].browse(
                pipedrive_product.odoo_ref)
            if product.exists():
                product.write({'active': False})
            pipedrive_product.write({'active': False})

    @http.route('/update_pipedrive_contact', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_contact_details(self, **kw):
        """Webhook for receiving the updated contact details."""
        env = self._get_webhook_env()
        data = json.loads(request.httprequest.data.decode('utf-8'))
        pipedrive_contact = env['pipedrive.record'].search(
            [('record_type', '=', 'partner'), ('pipedrive_reference', '=', data['data']['id'])])
        partner = env['res.partner'].browse([(
            pipedrive_contact.odoo_ref)])
        if partner:
            partner.write({
                'name': data['data']['name'],
                'email': data['data']['emails'][0]['value'] if data['data']['emails'] else None,
                'phone': data['data']['phones'][0]['value'] if data['data']['phones'] else None,
            })

    @http.route('/add_pipedrive_contact', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_added_contact_details(self, **kw):
        """Webhook for receiving the added contact details."""
        env = self._get_webhook_env()
        data = json.loads(request.httprequest.data.decode('utf-8'))['data']
        if not env['pipedrive.record'].search(
                [('record_type', '=', 'partner'), ('pipedrive_reference', '=', data['id'])]):
            person = env['res.partner'].create({
                'name': data['name'],
                'phone': data['phones'][0]['value'] if data['phones'] else None,
                'email': data['emails'][0]['value'] if data['emails'] else None,
                'pipedrive_reference': data['id']
            })
            env['pipedrive.record'].create({
                'pipedrive_reference': data['id'],
                'record_type': 'partner',
                'odoo_ref': person.id
            })

    @http.route(
        '/delete_pipedrive_contact',
        type="jsonrpc",
        auth="public",
        methods=['POST'],
        csrf=False
    )
    def get_deleted_contact_details(self, **kw):
        """Webhook for receiving the deleted contact details."""
        env = self._get_webhook_env()
        data = json.loads(request.httprequest.data.decode('utf-8'))
        person_id = data.get('meta', {}).get('entity_id')
        if not person_id:
            return {'status': 'error', 'message': 'No entity_id found'}
        pipedrive_contact = env['pipedrive.record'].search(
            [
                ('record_type', '=', 'partner'),
                ('pipedrive_reference', '=', str(person_id))
            ],
            limit=1
        )
        if pipedrive_contact:
            env['res.partner'].browse(
                pipedrive_contact.odoo_ref
            ).write({'active': False})
            pipedrive_contact.write({'active': False})
        return {'status': 'success'}
