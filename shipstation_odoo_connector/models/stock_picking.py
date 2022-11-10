# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

from odoo import fields, models, api, _
import requests
import base64

try:
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipstation_order_id = fields.Integer(string="Shipstaion Order Id ", readonly=True)
    shipstation_shipping_status = fields.Char(string="Shipping Status",
                                              compute='_compute_shipstation_shipping_status')
    shipstation_shipping_cancel = fields.Boolean(string="Is Cancel", default=False)
    shipstation_shipping_orderKey = fields.Char(string="Order Key")
    shipstation_shipping_hold_date = fields.Date(string="Hold Until")

    @api.depends('shipstation_order_id')
    def _compute_shipstation_shipping_status(self):

        if self.shipstation_order_id:

            shipstation = self.env['shipstation.api'].search(
                [('activate', '=', True)])

            base64string = base64.encodebytes(('%s:%s' % (
                shipstation.username,
                shipstation.password)).encode()).decode().replace('\n', '')

            url = shipstation.host + '/orders/' + str(self.shipstation_order_id)
            payload = {}
            headers = {
                'Host': 'ssapi.shipstation.com',
                'Authorization': "Basic " + base64string
            }
            response = requests.request("GET", url, headers=headers,
                                        data=payload)
            # print("compute", response.json())

            self.shipstation_shipping_status = response.json().get(
                'orderStatus')
        else:
            self.shipstation_shipping_status = "None"

    def get_label(self):
        shipstation = self.env['shipstation.api'].search(
            [('activate', '=', True)])
        dc = self.env['delivery.carrier'].search([('name', '=',
                                                   self.carrier_id.name)])
        sale_oredr = self.env['sale.order'].search(
            [('name', '=', self.origin)])
        total_weight = self.shipping_weight

        self.get_shipping_info()

        base64string = base64.encodebytes(('%s:%s' % (
            shipstation.username,
            shipstation.password)).encode()).decode().replace('\n', '')

        url = shipstation.host + '/orders/createlabelfororder'
        # str(self.shipstation_order_id)
        payload = "{\n  \"orderId\": %s,\n  \"carrierCode\": \"%s\",\n  \"serviceCode\": \"%s\",\n  \"packageCode\": \"%s\",\n  \"shipDate\": \"%s\",\n  \"weight\": {\n    \"value\": %s,\n    \"units\": \"pounds\"\n  },\n  \"internationalOptions\": null,\n  \"advancedOptions\": null,\n  \"testLabel\": false\n}" % (
            self.shipstation_order_id, dc.shipstation_carrier.code,
            dc.shipstation_service.code, dc.shipstation_package.code,
            sale_oredr.date_order, (total_weight * 2.2046))

        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'

        }

        response = requests.request("POST", url, headers=headers,
                                    data=str(payload))

        value = {'trackingNumber': response.json().get('trackingNumber'), 'data': response.json().get('labelData')}
        return value

    def send_to_shipper(self):
        self.ensure_one()

        res = self.carrier_id.send_shipping(self)[0]
        if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
            res['exact_price'] = 0.0
        self.carrier_price = res['exact_price'] * (
                1.0 + (self.carrier_id.margin / 100.0))
        if res['tracking_number']:
            self.carrier_tracking_ref = res['tracking_number']
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        msg = _(
            "Shipment sent to carrier %(carrier_name)s for shipping with "
            "tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
            carrier_name=self.carrier_id.name,
            ref=self.carrier_tracking_ref,
            price=self.carrier_price,
            currency=order_currency.name
        )
        self.message_post(body=msg)
        self._add_delivery_cost_to_so()

    def action_onhold_order(self):
        shipstation = self.env['shipstation.api'].search(
            [('activate', '=', True)])

        base64string = base64.encodebytes(('%s:%s' % (
            shipstation.username,
            shipstation.password)).encode()).decode().replace('\n', '')

        url = shipstation.host + '/orders/holduntil'
        if self.shipstation_shipping_hold_date:
            hold_date = self.shipstation_shipping_hold_date
        else:
            hold_date = fields.date.today()
        payload = "{\n  \"orderId\": %s,\n  \"holdUntilDate\": \"%s\"\n}" % (
            self.shipstation_order_id, hold_date)
        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

    def action_shipped_order(self):
        shipstation = self.env['shipstation.api'].search(
            [('activate', '=', True)])

        base64string = base64.encodebytes(('%s:%s' % (
            shipstation.username,
            shipstation.password)).encode()).decode().replace('\n', '')

        carrier_code = self.env['delivery.carrier'].search(
            [('id', '=', self.carrier_id.id)])

        carier = carrier_code.shipstation_carrier.code
        url = shipstation.host + 'orders/markasshipped'
        payload = "{\n  \"orderId\": %s,\n  \"carrierCode\": \"%s\",\n  \"trackingNumber\": \"%s\",\n  \"notifyCustomer\": true}" % (
            int(self.shipstation_order_id),
            carier, self.shipstation_order_id)
        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

    def action_restore_hold_order(self):
        shipstation = self.env['shipstation.api'].search(
            [('activate', '=', True)])

        base64string = base64.encodebytes(('%s:%s' % (
            shipstation.username,
            shipstation.password)).encode()).decode().replace('\n', '')

        url = shipstation.host + 'orders/restorefromhold'
        if self.shipstation_shipping_hold_date:
            hold_date = self.shipstation_shipping_hold_date
        else:
            hold_date = fields.date.today()
        payload = "{\n  \"orderId\": %s}" % (
            self.shipstation_order_id)
        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

    def open_website_url(self):
        if self.shipstation_order_id:
            if self.shipstation_shipping_status == 'awaiting_shipment':
                url = 'https://ship13.shipstation.com/orders/awaiting-shipment'
            elif self.shipstation_shipping_status == 'shipped':
                url = 'https://ship13.shipstation.com/shipments/shipped?'
                # url ='https://ship13.shipstation.com/orders/shipped'
            elif self.shipstation_shipping_status == 'on_hold':
                url = 'https://ship13.shipstation.com/orders/on-hold'
            elif self.shipstation_shipping_status == 'cancelled':
                url = 'https://ship13.shipstation.com/orders/cancelled'
            return {
                "type": "ir.actions.act_url",
                "url": url + '/%s' % self.origin,
                "target": "new"
            }

    def get_shipping_info(self, ):
        credential = self.env['shipstation.api'].search(
            [('activate', '=', True)])
        base64string = base64.encodebytes(('%s:%s' % (
            credential.username,
            credential.password)).encode()).decode().replace('\n', '')

        url = credential.host + 'shipments?orderNumber=%s&orderId=%s' % (
            self.origin, self.shipstation_order_id)
        headers = {
            'Host': 'ssapi.shipstation.com',
            'Authorization': "Basic " + base64string,
        }
        ship = requests.get(url, headers=headers)
