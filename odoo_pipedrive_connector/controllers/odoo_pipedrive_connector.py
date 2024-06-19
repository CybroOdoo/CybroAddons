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
from odoo import fields, http
from odoo.http import request


class PipedriveWebhook(http.Controller):
    """ This controller is responsible for receiving Webhooks from Pipedrive"""

    @http.route('/update_pipedrive_product', type="json", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_product_details(self, **kw):
        """Webhook for receiving the updated product details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        request.env.company.sudo().create_product_category()
        uom_id = 1
        if data['current']['unit']:
            for rec in request.env['uom.uom'].sudo().search([]).mapped(
                    'name'):
                if rec.lower() == data['current']['unit'].lower():
                    uom_id = request.env['uom.uom'].sudo().search(
                        [('name', '=', rec)]).id
        pipedrive_product = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product'),
             ('pipedrive_reference', '=', data['current']['id'])])
        product_template = request.env['product.template'].sudo().browse(
            pipedrive_product.odoo_ref)
        pipedrive_categ = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'categ'), ('pipedrive_reference', '=',
                                             data['current']['category'])])
        category_id = request.env['product.category'].sudo().browse(
            pipedrive_categ.odoo_ref) if pipedrive_categ else 1
        currency = request.env['res.currency']
        if data['current']['prices']:
            currency = request.env['res.currency'].sudo().search(
                [('name', '=', data['current']['prices'][0]['currency']),
                 ('active', 'in', [True, False])])
            if not currency.active:
                currency.active = True
        list_price = currency._convert(
            data['current']['prices'][0]['price'],
            request.env.company.currency_id, request.env.company,
            fields.date.today()) if data['current']['prices'][0][
            'price'] else 0.0,
        standard_price = currency._convert(
            data['current']['prices'][0]['cost'],
            request.env.company.currency_id, request.env.company,
            fields.date.today()) if data['current']['prices'][0][
            'cost'] else 0.0,
        if product_template:
            update_values = {}
            if product_template.name != data['current']['name']:
                update_values['name'] = data['current']['name']
            if product_template.description != data['current']['description']:
                update_values['description'] = data['current']['description']
            if product_template.uom_id.id != uom_id:
                update_values['uom_id'] = uom_id
                update_values['uom_po_id'] = uom_id
            if product_template.active != data['current']['active_flag']:
                update_values['active'] = data['current']['active_flag']
            if product_template.standard_price != standard_price[0]:
                update_values['standard_price'] = standard_price[0]
            if product_template.list_price != list_price[0]:
                update_values['list_price'] = list_price[0]
            if product_template.categ_id.id != category_id:
                update_values['categ_id'] = category_id
            product_template.update_from_pipedrive = False
            if update_values:
                product_template['update_from_pipedrive'] = True
                product_template.sudo().write(update_values)

    @http.route('/add_pipedrive_product', type="json", auth="public",
                csrf=False, methods=['POST'])
    def get_added_product_details(self, **kw):
        """Webhook for receiving the new product details."""

        if json.loads(request.httprequest.data.decode('utf-8'))[
            'meta']['change_source'] != 'api':
            added_data = json.loads(request.httprequest.data.decode('utf-8'))[
                'current']
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
                    'default_code': added_data['code'],
                    'uom_po_id': uom,
                    'taxes_id': False,
                    'list_price': currency._convert(
                        added_data['prices'][0]['price'],
                        request.env.company.currency_id, request.env.company,
                        fields.date.today()) if
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
                            added_data['category'])])[0].odoo_ref if request.env['pipedrive.record'].sudo().search(
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
                product.taxes_id.unlink()
                if added_data['tax'] != 0:
                    tax = request.env['account.tax'].sudo().search(
                        [('amount_type', '=', 'percent'),
                         ('type_tax_use', '=', 'sale'), ('amount',
                                                         '=',
                                                         added_data['tax'])],limit=1)
                    if not tax:
                        tax = request.env['account.tax'].sudo().create({
                            'name': 'Tax ' + str(added_data['tax']) + '%',
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                            'amount': added_data['tax']
                        })
                    product.sudo().write({
                        "taxes_id": [(4, tax.id)]
                    })

    @http.route('/delete_pipedrive_product', type="json", auth="public",
                csrf=False, methods=['POST'])
    def get_deleted_product_details(self, **kw):
        """Webhook for receiving the deleted product details."""
        deleted_data = json.loads(request.httprequest.data.decode('utf-8'))
        pipedrive_product = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'product'), ('pipedrive_reference', '=', deleted_data['meta']['id'])])
        request.env['product.template'].sudo().browse(pipedrive_product.odoo_ref).sudo().write(
            {'active': False})
        pipedrive_product.sudo().write(
            {'active': False})

    @http.route('/update_pipedrive_contact', type="json", auth="public", csrf=False,
                methods=['POST'])
    def get_updated_contact_details(self, **kw):
        """Webhook for receiving the updated contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        pipedrive_contact = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner'),
             ('pipedrive_reference', '=', data['current']['id'])])
        partner = request.env['res.partner'].sudo().browse([(
            pipedrive_contact.odoo_ref)])
        if partner:
            partner.sudo().write({
                'name': data['current']['name'],
                'email': data['current']['email'][0]['value'],
                'phone': data['current']['phone'][0]['value'],
            })

    @http.route('/add_pipedrive_contact', type="json", auth="public", csrf=False,
                methods=['POST'])
    def get_added_contact_details(self, **kw):
        """Webhook for receiving the added contact details."""
        if json.loads(request.httprequest.data.decode('utf-8'))['meta']['change_source'] != 'api':
            data = json.loads(request.httprequest.data.decode('utf-8'))['current']
            if not request.env['pipedrive.record'].sudo().search(
                    [('record_type', '=', 'partner'), ('pipedrive_reference', '=', data['id'])]):
                person = request.env['res.partner'].sudo().create({
                    'name': data['name'],
                    'phone': data['phone'][0]['value'],
                    'email': data['email'][0]['value'],
                    'pipedrive_reference': data['id']
                })
                request.env['pipedrive.record'].sudo().create({
                    'pipedrive_reference': data['id'],
                    'record_type': 'partner',
                    'odoo_ref': person.id
                })

    @http.route('/delete_pipedrive_contact', type="json", auth="public",
                methods=['POST'], csrf=False)
    def get_deleted_contact_details(self, **kw):
        """Webhook for receiving the deleted contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        pipedrive_contact = request.env['pipedrive.record'].sudo().search(
            [('record_type', '=', 'partner'),
             ('pipedrive_reference', '=', data['meta']['id'])])
        request.env['product.template'].sudo().browse(pipedrive_contact.odoo_ref).sudo().write(
            {'active': False})
        pipedrive_contact.sudo().write(
            {'active': False})
