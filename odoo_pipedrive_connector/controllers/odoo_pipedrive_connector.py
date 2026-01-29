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
from odoo import http
from odoo.http import request


class PipedriveWebhook(http.Controller):
    """ This controller is responsible for receiving Webhooks from Pipedrive"""

    @http.route('/update_pipedrive_product', type="json", auth="public",
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
        product_template = request.env['product.template'].sudo().search([(
            'pipedrive_reference', '=', data['current']['id'])])
        if product_template:
            product_template.sudo().write({
                'name': data['current']['name'],
                'description': data['current']['description'],
                'uom_id': uom_id,
                'active': data['current']['active_flag'],
                'uom_po_id': uom_id,
                'standard_price': data['current']['prices'][0]['cost'],
                'list_price': data['current']['prices'][0]['price'],
                'categ_id': request.env['product.category'].sudo().search([(
                    'pipedrive_reference', '=',
                    data['current']['category'])]).id if data[
                    'current']['category'] else 1
            })

    @http.route('/delete_pipedrive_product', type="json", auth="public",
                methods=['POST'])
    def get_deleted_product_details(self, **kw):
        """Webhook for receiving the deleted product details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        request.env['product.template'].sudo().search([(
            'pipedrive_reference', '=', data['meta']['id'])]).unlink()

    @http.route('/update_pipedrive_contact', type="json", auth="public",
                methods=['POST'])
    def get_updated_contact_details(self, **kw):
        """Webhook for receiving the updated contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        partner = request.env['res.partner'].sudo().search([(
            'pipedrive_reference', '=', data['current']['id'])])
        if partner:
            partner.sudo().write({
                'name': data['current']['name'],
                'email': data['current']['email'][0]['value'],
                'phone': data['current']['phone'][0]['value'],
            })

    @http.route('/delete_pipedrive_contact', type="json", auth="public",
                methods=['POST'])
    def get_deleted_contact_details(self, **kw):
        """Webhook for receiving the deleted contact details."""
        data = json.loads(request.httprequest.data.decode('utf-8'))
        request.env['res.partner'].sudo().search([(
            'pipedrive_reference', '=', data['meta']['id'])]).unlink()
