# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
###############################################################################
import base64
from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import json
import requests


class DeliveryCarrier(models.Model):
    """Creating a new delivery carrier and add new fields for
     enter client credentials"""
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('fedex_api', 'Fedex API')], ondelete={'fedex_api': 'set default'})
    fedex_developer_key = fields.Char(string="Fedex Client ID",
                                      help="Provide fedex developer key")
    fedex_developer_pwd = fields.Char(string="Fedex Client Secret",
                                      help="Secret key of fedex")
    fedex_account_number = fields.Char(string="FedEx Account Number",
                                       help="Fedex account number")
    fedex_access_token = fields.Char(string="Fedex Access Token",
                                     help="Access token for payload")
    fedex_default_package_type_id = fields.Many2one('stock.package.type',
                                                    string="Fedex Package Type",
                                                    help="Package type")
    fedex_service_type = fields.Selection(
        [
         ('International_priority', 'International priority'),
         ('Fedex_International_priority', 'Fedex International priority'),
         ], default='Fedex_International_priority', string="Fedex Service type")
    fedex_duty_payment = fields.Selection(
        [('SENDER', 'Sender'), ('RECIPIENT', 'Recipient')], required=True,
        default="SENDER", string="Fedex duty payment", help="Here we can set sender or receiver "
                                                            "who is responsible for duty of payment")
    fedex_weight_unit = fields.Selection([('LB', 'LB'),
                                          ('KG', 'KG')],
                                         default='LB', string="Select weight type")
    fedex_label_stock_type = fields.Selection([('PAPER_LETTER', 'PAPER LETTER'),
                                               ('STOCK_4X6', 'STOCK 4X6')],
                                              string='Label Type',
                                              default='PAPER_LETTER')
    fedex_label_file_type = fields.Selection([('PDF', 'PDF'),
                                              ('PNG', 'PNG'),
                                              ('ZPL', 'ZPL')],
                                             default='PDF',
                                             string="Fedex Label File Type")
    price = fields.Float(string="Picking Id")

    def fedex_api_rate_shipment(self, order):
        """Calculating fedex rate and add to order line"""
        current_date = datetime.now().date()
        if order:
            if self.fedex_developer_key and self.fedex_developer_pwd and self.fedex_account_number:
                user_details = order[0]['create_uid']
                partner_details = order[0]['partner_id']
                url = "https://apis-sandbox.fedex.com/oauth/token"
                payload = {
                    "grant_type": "client_credentials",
                    "client_id": self.fedex_developer_key,
                    "client_secret": self.fedex_developer_pwd
                }
                headers = {
                    'Content-Type': "application/x-www-form-urlencoded",
                }

                response = requests.post(url, data=payload, headers=headers)
                if response.status_code == 200:
                    json_response = response.json()
                    access_token = json_response.get('access_token')
                    self.fedex_access_token = access_token
                    if access_token:
                        url = "https://apis-sandbox.fedex.com/rate/v1/rates/quotes"
                        payload = {
                            "accountNumber": {
                                "value": self.fedex_account_number
                            },
                            "requestedShipment": {
                                "shipper": {
                                  "address": {
                                     "postalCode": str(user_details.zip),
                                     "countryCode": str(user_details.country_id.code)
                                  }
                                },
                                "recipient": {
                                  "address": {
                                    "postalCode": str(partner_details.zip),
                                    "countryCode": str(partner_details.country_id.code)
                                  }
                                },
                                "shipDateStamp": str(current_date),
                                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
                                "serviceType": self.fedex_service_type,
                                "packagingType": self.fedex_default_package_type_id.id,
                                "rateRequestType": [
                                  "LIST",
                                  "ACCOUNT"
                                ],
                                "customsClearanceDetail": {
                                  "dutiesPayment": {
                                    "paymentType": "SENDER",
                                    "payor": {
                                      "responsibleParty": None
                                    }
                                  },
                                  "commodities": [
                                    {
                                      "description": "",
                                      "quantity": 500,
                                      "quantityUnits": str(self.fedex_weight_unit),
                                      "weight": {
                                        "units": str(self.fedex_weight_unit),
                                        "value": 10
                                      },
                                      "customsValue": {
                                       "amount": 400,
                                       "currency": str(self.env.company.currency_id.name)
                                      }
                                    }
                                  ]
                                },
                                "requestedPackageLineItems": [
                                 {
                                    "weight": {
                                      "units": str(self.fedex_weight_unit),
                                      "value": 10
                                    }
                                  }
                                ]
                              }
                            }
                        data = json.dumps(payload)
                        headers = {
                            'Content-Type': "application/json",
                            'X-locale': "en_US",
                            'Authorization': f"Bearer {access_token}"
                        }
                        response = requests.post(url, data=data, headers=headers)
                        res = {}
                        if response.status_code == 200:
                            response_data = json.loads(response.text)
                            res['price'] = \
                            response_data['output']['rateReplyDetails'][0][
                                'ratedShipmentDetails'][0]['totalNetFedExCharge']
                            res['carrier_price'] = res['price']
                            res['success'] = True
                            res['warning_message'] = "Successfully added"
                            self.price = res['price']
                            return res
                else:
                    raise UserError(("Please Enter valid credentials"))
            else:
                raise UserError(("Invalid credentials"))

    def fedex_api_send_shipping(self, pickings):
        """The tracking number and exact price are passed to the main function
        of send shipping"""
        fedex_api_shipping = self.fedex_api_shipping(pickings)
        stock_picking_data = self.env['stock.picking'].browse(pickings.id)
        stock_picking_data.carrier_tracking_ref = fedex_api_shipping['tracking_number']
        res = []
        res = res + [{'exact_price': fedex_api_shipping['exact_price'],
                      'tracking_number': False}]
        return res

    def fedex_api_shipping(self, pickings):
        """Creating new request for ship api and get tracking number"""
        current_date = datetime.now().date()
        stock_picking_data = self.env['stock.picking'].browse(pickings.id)
        sale_id = stock_picking_data[0]['sale_id']
        partner_id_data = sale_id[0]['partner_id'][0]
        user_id_data = sale_id[0]['create_uid'][0]
        carrier_id_details = stock_picking_data[0]['carrier_id']
        carrier_id = carrier_id_details.name
        url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
        payload = {
            "labelResponseOptions": "URL_ONLY",
            "requestedShipment": {
                "shipper": {
                    "contact": {
                        "personName": carrier_id,
                        "phoneNumber": 1234567890,
                        "companyName": carrier_id
                    },
                    "address": {
                        "streetLines": [
                            "demo"
                        ],
                        "city": str(user_id_data),
                        "stateOrProvinceCode": "AR",
                        "postalCode": str(user_id_data.zip),
                        "countryCode": str(user_id_data.country_id.code),
                    }
                },
                "recipients": [
                    {
                        "contact": {
                            "personName": str(partner_id_data.name),
                            "phoneNumber": str(partner_id_data.mobile),
                            "companyName": str(partner_id_data.company_id.name)
                        },
                        "address": {
                            "streetLines": [
                                "RECIPIENT STREET LINE 1",
                                "RECIPIENT STREET LINE 2"
                            ],
                            "city": str(partner_id_data.city),
                            "stateOrProvinceCode": "TN",
                            "postalCode": str(partner_id_data.zip),
                            "countryCode": str(partner_id_data.country_id.code)
                        }
                    }
                ],
                "shipDatestamp": str(current_date),
                "serviceType": str(self.fedex_service_type),
                "packagingType": "fedex_box",
                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
                "blockInsightVisibility": "False",
                "shippingChargesPayment": {
                    "paymentType": "SENDER"
                },
                "shipmentSpecialServices": {
                    "specialServiceTypes": [
                        "FEDEX_ONE_RATE"
                    ]
                },
                "labelSpecification": {
                    "imageType": str(self.fedex_label_file_type),
                    "labelStockType": str(self.fedex_label_stock_type)
                },
                "requestedPackageLineItems": [
                    {}
                ]
            },
            "accountNumber": {
                "value": self.fedex_account_number
            }
        }
        headers = {
            'Content-Type': "application/json",
            'X-locale': "en_US",
            'Authorization': f"Bearer {self.fedex_access_token}"
        }
        data = json.dumps(payload)
        response = requests.post(url, data=data, headers=headers)
        res = {}
        if response.status_code == 200:
            response_data = json.loads(response.text)
            res['tracking_number'] = response_data["output"]["transactionShipments"][0][
                "completedShipmentDetail"]["masterTrackingId"]["trackingNumber"]
            res['exact_price'] = self.price
            encoded_label = response_data['output']['transactionShipments'][0]['pieceResponses'][0][
                'packageDocuments'][0]['encodedLabel']
            if self.fedex_label_file_type == 'PDF':
                mime_type = 'application/pdf'
                name = "label.pdf"
            elif self.fedex_label_file_type == 'PNG':
                mime_type = 'image/png'
                name = "label.png"
            elif self.fedex_label_file_type == 'ZPLII':
                mime_type = 'application/text'
                name = "label.zpl"
            else:
                raise ValueError(
                    f"Unsupported fedex_label_file_type: {self.fedex_label_file_type}")
            if isinstance(encoded_label, str):
                encoded_label = encoded_label.encode('utf-8')
            decoded_bytes = base64.b64decode(encoded_label)
            decoded_txt = decoded_bytes.decode('utf-8')
            decoded_text = decoded_txt.replace('^POI', '^PO')
            url = "http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/"
            headers = {
                "Accept": mime_type
            }
            response = requests.post(url, headers=headers, data=decoded_text)
            pdf_bytes = response.content
            decoded_bytes = base64.b64encode(pdf_bytes)

            if self.fedex_label_file_type == 'ZPLII':
                decoded_byte = decoded_text.encode('utf-8')
                decoded_bytes = base64.b64encode(decoded_byte)
            attachment_values = {
                'name': name,
                'type': 'binary',
                'datas': decoded_bytes,
                'mimetype': mime_type,
                'res_model': 'stock.picking',
                'res_id': pickings.id,
                }
            attachment_id = self.env['ir.attachment'].sudo().create(attachment_values)
            pickings.message_post(body="Delivery details", attachment_ids=[attachment_id.id])
        return res

    def fedex_api_get_tracking_link(self, picking):
        """Tracking button function for tracking the ship details"""
        return "https://www.fedex.com/fedextrack/?action=track&trackingnumber=%s"% picking.carrier_tracking_ref



