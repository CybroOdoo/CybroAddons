# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

{
    'name': 'ShipStation Odoo Connector',
    'version': '15.0.1.0.0',
    'summary': 'Integrate and Manage ShipStation Operations with Odoo',
    'description': 'Integrate and Manage ShipStation Operations with Odoo',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'account', 'stock', 'delivery'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/api_credential.xml',
        'views/store.xml',
        'views/services.xml',
        'views/delivery_shipstation.xml',
        'views/packages_shipstation.xml',
        'views/delivery_carrier_view.xml',
        'views/sale_orders.xml',
        'views/shipstation_actions.xml',
        'views/stock_picking.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'price': 49,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
