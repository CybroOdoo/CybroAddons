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
from odoo import fields, http
from odoo.http import request
from odoo.fields import Command


class PipedriveWebhook(http.Controller):
    """ This controller is responsible for receiving Webhooks from Pipedrive"""

    @http.route('/update_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_product_details(self, **kw):
        """ Webhook for receiving the updates on products."""
        payload = json.loads(request.httprequest.data.decode('utf-8'))
        current = payload.get('data', {})
        if not current:
            return {"status": "no data"}
        uom_id = 1
        if current.get('unit'):
            uom = request.env['uom.uom'].sudo().search(
                [('name', 'ilike', current['unit'])], limit=1
            )
            if uom:
                uom_id = uom.id
        pipedrive_product = request.env['pipedrive.record'].sudo().search([
            ('record_type', '=', 'product'),
            ('pipedrive_reference', '=', current['id'])
        ], limit=1)
        if not pipedrive_product:
            return {"status": "product not found"}
        product_template = request.env['product.template'].sudo().browse(
            pipedrive_product.odoo_ref
        )
        category_id = 1
        if current.get('category'):
            pipedrive_categ = request.env['pipedrive.record'].sudo().search([
                ('record_type', '=', 'categ'),
                ('pipedrive_reference', '=', current['category'])
            ], limit=1)
            if pipedrive_categ:
                category_id = pipedrive_categ.odoo_ref
        list_price = standard_price = 0.0
        if current.get('prices'):
            price_data = current['prices'][0]
            currency = request.env['res.currency'].sudo().search(
                [('name', '=', price_data['currency'])], limit=1
            )
            if currency and not currency.active:
                currency.active = True
            list_price = currency._convert(
                price_data.get('price', 0),
                request.env.company.currency_id,
                request.env.company,
                fields.Date.today()
            )
            standard_price = currency._convert(
                price_data.get('cost', 0),
                request.env.company.currency_id,
                request.env.company,
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
            product_template.with_context(update_from_pipedrive=True).sudo().write(
                update_values)
        return {"status": "success"}

    @http.route('/add_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_added_product_details(self, **kw):
        """Webhook for receiving the new product details."""
        if json.loads(request.httprequest.data.decode('utf-8'))[
            'meta']['change_source'] == 'api':
            added_data = json.loads(request.httprequest.data.decode('utf-8'))[
                'data']
            request.env.company.sudo().create_product_category()
            uom = 1
            currency = request.env['res.currency']
            if added_data['prices']:
                currency = request.env['res.currency'].sudo().search(
                    [('name', '=', added_data['prices'][0]['currency']),
                     ('active', 'in', [True, False])])
                if not currency.active:
                    currency.active = True
            if added_data['unit']:
                for rec in request.env['uom.uom'].sudo().search([]).mapped(
                        'name'):
                    if rec.lower() == added_data['unit'].lower():
                        uom = request.env['uom.uom'].sudo().search(
                            [('name', '=', rec)]).id
            if not request.env['pipedrive.record'].sudo().search(
                    [('pipedrive_reference', '=', added_data['id']),
                     ('record_type', '=', 'product')]):
                product = request.env['product.template'].sudo().create({
                    'name': added_data['name'],
                    'description': added_data['description'],
                    'uom_id': uom,
                    'taxes_id': False,
                    'list_price': currency._convert(
                        added_data['prices'][0]['price'],
                        request.env.company.currency_id, request.env.company,
                        fields.Date.today()) if
                    added_data['prices'][0][
                        'price'] else 0.0,
                    'standard_price': currency._convert(
                        added_data['prices'][0]['cost'],
                        request.env.company.currency_id, request.env.company,
                        fields.date.today()) if
                    added_data['prices'][0][
                        'cost'] else 0.0,
                    'categ_id': request.env['pipedrive.record'].sudo().search(
                        [(
                            'pipedrive_reference', '=',
                            added_data['category'])])[0].odoo_ref if request.env[
                        'pipedrive.record'].sudo().search(
                        [(
                            'pipedrive_reference', '=',
                            added_data['category'])]) else 1
                    if added_data['category'] else 1,
                    'pipedrive_reference': added_data['id']
                })
                request.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': added_data['id'],
                    'record_type': 'product',
                    'odoo_ref': product.id
                })
                product.write(
                    {'taxes_id': [Command.clear()]})
                if added_data['tax'] != 0:
                    tax = request.env['account.tax'].sudo().search(
                        [('amount_type', '=', 'percent'),
                         ('type_tax_use', '=', 'sale'), ('amount',
                                                         '=',
                                                         added_data['tax'])])
                    if not tax:
                        tax = request.env['account.tax'].sudo().create({
                            'name': 'Tax ' + str(added_data['tax']) + '%',
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                            'amount': added_data['tax']
                        })
                    product.sudo().write({
                        "taxes_id": [Command.link(tax.id)]
                    })

    @http.route('/delete_pipedrive_product', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_deleted_product_details(self, **kw):
        """Webhook for receiving the deleted product details."""
        deleted_data = json.loads(request.httprequest.data.decode('utf-8'))
        product_id = deleted_data['meta']['entity_id']
        pipedrive_product = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product'),
             ('pipedrive_reference', '=', product_id)])
        if pipedrive_product:
            product = request.env['product.template'].sudo().browse(
                pipedrive_product.odoo_ref)
            if product.exists():
                product.write({'active': False})
            pipedrive_product.write({'active': False})

    @http.route('/update_pipedrive_contact', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_contact_details(self, **kw):
        """Webhook for receiving the updated contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        pipedrive_contact = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner'), ('pipedrive_reference', '=', data['data']['id'])])
        partner = request.env['res.partner'].sudo().browse([(
            pipedrive_contact.odoo_ref)])
        if partner:
            partner.sudo().write({
                'name': data['data']['name'],
                'email': data['data']['emails'][0]['value'] if data['data']['emails'] else None,
                'phone': data['data']['phones'][0]['value'] if data['data']['phones'] else None,
            })

    @http.route('/add_pipedrive_contact', type="jsonrpc", auth="public", csrf=False,
                methods=['POST'])
    def get_added_contact_details(self, **kw):
        """Webhook for receiving the added contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))['data']
        if not request.env['pipedrive.record'].sudo().search(
                [('record_type', '=', 'partner'), ('pipedrive_reference', '=', data['id'])]):
            person = request.env['res.partner'].sudo().create({
                'name': data['name'],
                'phone': data['phones'][0]['value'] if data['phones'] else None,
                'email': data['emails'][0]['value'] if data['emails'] else None,
                'pipedrive_reference': data['id']
            })
            request.env['pipedrive.record'].sudo().create({
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
        data = json.loads(request.httprequest.data.decode('utf-8'))
        person_id = data.get('meta', {}).get('entity_id')
        if not person_id:
            return {'status': 'error', 'message': 'No entity_id found'}
        pipedrive_contact = request.env['pipedrive.record'].sudo().search(
            [
                ('record_type', '=', 'partner'),
                ('pipedrive_reference', '=', str(person_id))
            ],
            limit=1
        )
        if pipedrive_contact:
            request.env['res.partner'].sudo().browse(
                pipedrive_contact.odoo_ref
            ).write({'active': False})
            pipedrive_contact.write({'active': False})
        return {'status': 'success'}
