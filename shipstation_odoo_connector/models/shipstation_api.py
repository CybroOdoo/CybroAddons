# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

import json
from odoo import fields, models, api, _
from odoo.http import request
from odoo.exceptions import UserError
import requests
import base64

try:
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('shipstation', 'ShipStation')],
        ondelete={'shipstation': 'set '
                                 'default'})

    @api.onchange('shipstation_carrier')
    def _onchange_shipstaion_carrier(self):
        service_object = self.env['shipstation.service'].search(
            [('carrier_code', '=', self.
              shipstation_carrier.code)])
        service_list = []
        for data in service_object:
            service_list.append(data.id)
        package_object = self.env['shipstation.packages'].search(
            [('carrier_code', '=', self.
              shipstation_carrier.code)])
        package_list = []
        for data in package_object:
            package_list.append(data.id)
        res = {}
        res['domain'] = {'shipstation_service': [('id', 'in', service_list)],
                         'shipstation_package': [('id', 'in', package_list)]}
        return res

    store = fields.Many2one('shipstation.store', string='Store',)
    shipstation_carrier = fields.Many2one('shipstation.delivery',
                                          string='Shipstation Carrier')
    shipstation_service = fields.Many2one('shipstation.service',
                                          string='Shipstation Delivery '
                                                 'Carrier Service')
    shipstation_package = fields.Many2one('shipstation.packages',
                                          string='Shipstation Package')


class ShipStationApi(models.Model):
    _name = 'shipstation.api'
    _description = "Shipstation Api"
    _rec_name = 'host'

    host = fields.Char(string="Host", help="Provide the api url",required=True)
    username = fields.Char(string="Username", help="Provide the Shipstation API Key",required=True)
    password = fields.Char(string="Password", help="Provide the Shipstation API Secret",required=True)
    activate = fields.Boolean(string="Activate", default=False,
                              help="Make this credential active.Please activate only one credential ata time")

    def get_carriers_service(self):
        """This function will create shipstation store,packages and other
        information form shipstation"""

        base64string = base64.encodebytes(('%s:%s' % (
            self.username, self.password)).encode()).decode().replace('\n', '')
        url = self.host + '/carriers'
        headers = {
            'Authorization': "Basic " + base64string
        }
        carriers = requests.get(url, headers=headers)
        for rec in carriers.json():
            # print (rec)
            product = self.env['product.product'].search(
                [('name', '=', 'ShipstationShipping')])
            if not product:
                product = self.env['product.product'].create({
                    'name': 'ShipstationShipping',
                    'type': 'service',
                    'lst_price': 0.0,
                })
            add_carriers = self.env['shipstation.delivery'].search([
                ('shipping_providerid', '=', rec.get('shippingProviderId'))])
            if not add_carriers:
                add_carriers = self.env['shipstation.delivery'].create({
                    'name': rec.get('name'),
                    'code': rec.get('code'),
                    'account_number': rec.get('accountNumber') or False,
                    'requires_funded_account': rec.get(
                        'requiresFundedAccount') or False,
                    'balance': rec.get('balance'),
                    'nick_name': rec.get('nickname'),
                    'shipping_providerid': rec.get('shippingProviderId'),
                    'primary': rec.get('primary')
                })

            url = self.host + '/carriers/listservices?carrierCode=' \
                  + add_carriers.code
            headers = {
                'Authorization': "Basic " + base64string
            }
            services = requests.get(url, headers=headers)
            for i in services.json():
                services = self.env['shipstation.service'].search \
                    ([('carrier_code', '=', i.get('carrier_code'))
                      and ('code', '=', i.get('code'))])
                if not services:
                    services = self.env['shipstation.service'].create({
                        'carrier_code': i.get('carrierCode'),
                        'code': i.get('code'),
                        'name': i.get('name'),
                        'domestic': i.get('domestic'),
                        'international': i.get('international')
                    })
            url = self.host + '/carriers/listpackages?carrierCode=' \
                  + add_carriers.code
            headers = {
                'Authorization': "Basic " + base64string
            }
            packages = requests.get(url, headers=headers)
            for p in packages.json():
                package = self.env['shipstation.packages'].search \
                    ([('carrier_code', '=', p.get('carrierCode'))
                      and ('code', '=', p.get('code')
                           and ('name', '=', p.get('name')))])
                if not package:
                    package = self.env['shipstation.packages'].create({
                        'carrier_code': p.get('carrierCode'),
                        'code': p.get('code'),
                        'name': p.get('name'),
                        'domestic': p.get('domestic'),
                        'international': p.get('international')
                    })

        url = self.host + '/stores'
        headers = {
            'Authorization': "Basic " + base64string
        }
        stores = requests.get(url, headers=headers)
        for rec in stores.json():
            store = self.env['shipstation.store'].search \
                ([('store_id', '=', rec.get('storeId')) and
                  ('store_name', '=', rec.get('storeName'))])
            if not store:
                store = self.env['shipstation.store'].create({
                    'store_id': rec.get('storeId'),
                    'store_name': rec.get('storeName'),
                    'marketplace_name': rec.get('marketplaceName'),
                    'account_number': rec.get('accountName'),
                    'email': rec.get('email'),
                    'company_name': rec.get('companyName'),
                    'phone': rec.get('phone'),
                    'website': rec.get('website'),
                    'create_date': rec.get('createDate'),
                    'modified_date': rec.get('modifyDate')
                })


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def _get_shipment_rate(self):
        """Calculating the shipping rate"""
        vals = self.carrier_id.rate_shipment(self.order_id)
        if vals.get('success'):
            self.delivery_message = vals.get('warning_message', False)
            self.delivery_price = vals['price']
            self.display_price = vals['price']
            return {}
        return {'error_message': vals['error_message']}


class DeliveryCarrier(models.Model):
    _inherit = ['delivery.carrier']
    _primary_email = ['email_from']

    code = fields.Char(string="Code")

    def send_shipping(self, pickings):
        self.ensure_one()
        if hasattr(self, '%s_send_shipping' % self.delivery_type):
            return getattr(self, '%s_send_shipping' % self.delivery_type)(
                pickings)

    @api.model
    def create_oredr(self, pickings):
        """Creating order to shipstation"""
        credential = self.env['shipstation.api'].search(
            [('activate', '=', True)])
        for rec in credential:

            base64string = base64.encodebytes(('%s:%s' % (
                rec.username, rec.password)).encode()).decode().replace('\n',
                                                                        '')
            if not pickings.shipstation_order_id or pickings.shipstation_shipping_cancel:

                url = rec.host + '/orders/createorder'
            else:
                url = rec.host + '/orders/' + str(pickings.shipstation_order_id)
            headers = {
                'Host': 'ssapi.shipstation.com',
                'Authorization': "Basic " + base64string,
                'Content-Type': 'application/json'
            }
            oredrNumber = pickings.origin
            sale_oredr = self.env['sale.order'].search(
                [('name', '=', pickings.origin)])
            oredrDate = sale_oredr.date_order
            paymentDate = sale_oredr.date_order
            shipByDate = pickings.scheduled_date
            if pickings.shipstation_shipping_cancel:
                oredrStatus = 'cancelled'

            else:
                oredrStatus = 'awaiting_shipment'
            customer_id = sale_oredr.partner_id.id
            customerUsername = sale_oredr.partner_id.name
            billname = sale_oredr.partner_id.name
            bill_street1 = sale_oredr.partner_invoice_id.street
            bill_street2 = sale_oredr.partner_invoice_id.street2 or ""
            bill_city = sale_oredr.partner_invoice_id.city
            bill_state = sale_oredr.partner_invoice_id.state_id.name
            bill_postal = sale_oredr.partner_invoice_id.zip
            bil_contry = sale_oredr.partner_invoice_id.country_id.code
            bill_phone = sale_oredr.partner_invoice_id.phone
            shipTo_name = sale_oredr.partner_id.name
            shipTo_street1 = sale_oredr.partner_invoice_id.street
            shipTo_street2 = sale_oredr.partner_invoice_id.street2 or " "
            shipTo_city = sale_oredr.partner_invoice_id.city
            shipTo_state = sale_oredr.partner_invoice_id.state_id.name
            shipTo_postal = sale_oredr.partner_invoice_id.zip
            shipTo_contry = sale_oredr.partner_invoice_id.country_id.code

            shipTo_phone = sale_oredr.partner_invoice_id.phone
            items = []
            for rec in sale_oredr.order_line:
                each = {"sku": rec.product_id.default_code or "null",
                        "name": rec.product_id.name,
                        "imageUrl": f'{request.httprequest.host_url}'
                                    f'web/image?model=product.template&id='
                                    f'{rec.product_id.id}&field=image_128',
                        "weight": {
                            "value": (rec.product_id.weight * 2.2046),
                            "units": "pounds"
                        },
                        "quantity": int(rec.product_uom_qty),
                        "unitPrice": rec.price_unit,
                        "taxAmount": rec.tax_id.amount,
                        "shippingAmount": (rec.price_unit * int(
                            rec.product_uom_qty)) + rec.tax_id.amount,
                        "productId": rec.product_id.id
                        }
                items.append(each)
            items = str(items)

            amountPaid = sale_oredr.amount_untaxed
            taxAmount = sale_oredr.amount_tax
            shippingAmount = 0.0
            customerNotes = sale_oredr.note
            internalNotes = " "
            paymentMethod = "Credit Card"
            dc = self.env['delivery.carrier'].search([('name', '=',
                                                       pickings.carrier_id.name)])
            requestedShippingService = dc.shipstation_service.name
            carrierCode = dc.shipstation_carrier.code
            serviceCode = dc.shipstation_service.code
            packageCode = dc.shipstation_package.code
            confirmation = "delivery"
            shipDate = pickings.date_done
            weight = "{\n\"value\": %s,\n\"units\":\"%s\"\n }" % (
                (pickings.shipping_weight * 2.2046), "pounds")
            tag_ids = sale_oredr.tag_ids
            if pickings.shipstation_shipping_cancel and pickings.shipstation_shipping_orderKey:

                payload = "{\n  \"orderNumber\": \"%s\",\n  \"orderKey\":\"%s\",\n  \"orderDate\": \"%s\",\n  \"paymentDate\": \"%s\",\n  \"shipByDate\": \"%s\",\n  \"orderStatus\": \"%s\",\n  \"customerId\": \"%s\",\n  \"customerUsername\": \"%s\",\n  \"billTo\": {\n    \"name\": \"%s\",\n    \"street1\": \"%s\",\n    \"street2\": \"%s\",\n    \"city\": \"%s\",\n    \"state\": \"%s\",\n    \"postalCode\": \"%s\",\n    \"country\": \"%s\",\n    \"phone\": \"%s\" },\n    \"shipTo\": {\n    \"name\": \"%s\",\n    \"street1\": \"%s\",\n    \"street2\": \"%s\",\n    \"city\": \"%s\",\n    \"state\": \"%s\",\n    \"postalCode\": \"%s\",\n   \"country\":\"%s\",\n    \"phone\": \"%s\"  },\n    \"items\":%s,\n    \"amountPaid\": \"%s\",\n    \"taxAmount\": \"%s\",\n    \"shippingAmount\": \"%s\",\n    \"customerNotes\": \"%s\",\n    \"internalNotes\": \"%s\",\n    \"paymentMethod\": \"%s\",\n    \"requestedShippingService\": \"%s\",\n    \"carrierCode\": \"%s\",\n \"serviceCode\":\"%s\",\n    \"packageCode\": \"%s\",\n    \"confirmation\": \"%s\",\n    \"shipDate\": \"%s\",\n    \"weight\":%s }" % (
                    oredrNumber, pickings.shipstation_shipping_orderKey,
                    oredrDate, paymentDate, shipByDate,
                    oredrStatus,
                    customer_id, customerUsername, billname, bill_street1,
                    bill_street2,
                    bill_city, bill_state, bill_postal, bil_contry, bill_phone,
                    shipTo_name,
                    shipTo_street1, shipTo_street2, shipTo_city, shipTo_state,
                    shipTo_postal, shipTo_contry, shipTo_phone, items,
                    amountPaid,
                    taxAmount,
                    shippingAmount, customerNotes, internalNotes, paymentMethod,
                    requestedShippingService, carrierCode, serviceCode,
                    packageCode,
                    confirmation, shipDate, weight)
            else:
                payload = "{\n  \"orderNumber\": \"%s\",\n  \"orderDate\": \"%s\",\n  \"paymentDate\": \"%s\",\n  \"shipByDate\": \"%s\",\n  \"orderStatus\": \"%s\",\n  \"customerId\": \"%s\",\n  \"customerUsername\": \"%s\",\n  \"billTo\": {\n    \"name\": \"%s\",\n    \"street1\": \"%s\",\n    \"street2\": \"%s\",\n    \"city\": \"%s\",\n    \"state\": \"%s\",\n    \"postalCode\": \"%s\",\n    \"country\": \"%s\",\n    \"phone\": \"%s\" },\n    \"shipTo\": {\n    \"name\": \"%s\",\n    \"street1\": \"%s\",\n    \"street2\": \"%s\",\n    \"city\": \"%s\",\n    \"state\": \"%s\",\n    \"postalCode\": \"%s\",\n   \"country\":\"%s\",\n    \"phone\": \"%s\"  },\n    \"items\":%s,\n    \"amountPaid\": \"%s\",\n    \"taxAmount\": \"%s\",\n    \"shippingAmount\": \"%s\",\n    \"customerNotes\": \"%s\",\n    \"internalNotes\": \"%s\",\n    \"paymentMethod\": \"%s\",\n    \"requestedShippingService\": \"%s\",\n    \"carrierCode\": \"%s\",\n \"serviceCode\":\"%s\",\n    \"packageCode\": \"%s\",\n    \"confirmation\": \"%s\",\n    \"shipDate\": \"%s\",\n    \"weight\":%s }" % (
                    oredrNumber, oredrDate, paymentDate, shipByDate,
                    oredrStatus,
                    customer_id, customerUsername, billname, bill_street1,
                    bill_street2,
                    bill_city, bill_state, bill_postal, bil_contry, bill_phone,
                    shipTo_name,
                    shipTo_street1, shipTo_street2, shipTo_city, shipTo_state,
                    shipTo_postal, shipTo_contry, shipTo_phone, items,
                    amountPaid,
                    taxAmount,
                    shippingAmount, customerNotes, internalNotes, paymentMethod,
                    requestedShippingService, carrierCode, serviceCode,
                    packageCode,
                    confirmation, shipDate, weight)

            create_order = requests.request("POST", url, headers=headers,
                                            data=payload)
            result = create_order.json()

            if not pickings.shipstation_order_id and result.get('orderId'):
                pickings.shipstation_order_id = result.get('orderId')
                pickings.carrier_tracking_ref = result.get('orderId')
                pickings.shipstation_shipping_orderKey = result.get('orderKey')
            attachment_64 = pickings.get_label()

            so_attachment = self.env['ir.attachment'].sudo().create({
                'name': 'Shipstation Shipping Label - %s.pdf' % attachment_64.get('trackingNumber'),
                'type': 'binary',
                'mimetype': 'application/pdf',
                'datas': attachment_64.get('data')
            })
            pickings.message_post(
                body=(_("Order created into Shipstation for %s<br/>" % self.name)),
                attachment_ids=[so_attachment.id]
            )

    def shipstation_cancel_shipment(self, pickings):
        """Function to cancel shipstaion order"""
        pickings.shipstation_shipping_cancel = True
        pickings.send_to_shipper()

    def shipstation_send_shipping(self, pickings):
        res = []
        self.create_oredr(pickings)
        for p in pickings:
            res = res + [{'exact_price': p.carrier_id.fixed_price,
                          'tracking_number': False}]
        return res

    def shipstation_rate_shipment(self, order):
        """Calculating shipping rate"""

        shipstation = self.env['shipstation.api'].search(
            [('activate', '=', True)], limit=1)

        base64string = base64.encodebytes(('%s:%s' % (
            shipstation.username,
            shipstation.password)).encode()).decode().replace('\n', '')

        url = shipstation.host + "/shipments/getrates"
        company_postal = order.company_id.zip
        to_state = order.partner_shipping_id.state_id.name
        to_country = order.partner_shipping_id.country_id.code
        to_postal = order.partner_shipping_id.zip
        to_city = order.partner_shipping_id.city
        weight_value = 0
        for rec in order.order_line:
            weight_value = weight_value + (
                    rec.product_id.weight * rec.product_uom_qty)
        payload = "{\n  \"carrierCode\": \"%s\",\n  \"serviceCode\": \"%s\",\n  \"packageCode\": \"%s\",\n  \"fromPostalCode\": \"%s\",\n  \"toState\": \"%s\",\n  \"toCountry\": \"%s\",\n  \"toPostalCode\": \"%s\",\n  \"toCity\": \"%s\",\n  \"weight\": {\n    \"value\": %s,\n    \"units\": \"pounds\"\n  }\n}" % (
            self.shipstation_carrier.code, self.shipstation_service.code,
            self.shipstation_package.code, company_postal, to_state, to_country,
            to_postal, to_city, (weight_value * 2.2046))
        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        result = response.json()
        # print("result", result)
        if not result:

            final = {'success': True,
                     'price': 0.0,
                     'error_message': True,
                     'warning_message': "Something went wrong"}
        else:
            if 'shipmentCost' in result[0]:
                price = result[0].get('shipmentCost')
                final = {'success': True,
                         'price': price,
                         'error_message': False,
                         'warning_message': False}
            else:
                final = {'success': True,
                         'price': 0,
                         'error_message': True,
                         'warning_message': result.get('ExceptionMessage')}
        return final

    def rate_shipment(self, order):
        self.ensure_one()
        if hasattr(self, '%s_rate_shipment' % self.delivery_type):
            res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
            # apply margin on computed price
            res['price'] = float(res['price']) * (
                    1.0 + (float(self.margin) / 100.0))
            # free when order is large enough
            if res['success'] and self.free_over and \
                    order._compute_amount_total_without_delivery() >= self.amount:
                res['warning_message'] = _(
                    'Info:\nThe shipping is free because the order amount '
                    'exceeds %.2f.\n(The actual shipping cost is: %.2f)') % (
                                             self.amount, res['price'])
                res['price'] = 0.0
            return res

    def cancel_shipment(self, pickings):

        self.ensure_one()
        if hasattr(self, '%s_cancel_shipment' % self.delivery_type):
            return getattr(self, '%s_cancel_shipment' % self.delivery_type)(
                pickings)
