# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': 'Customer Route Management',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': """This module will set routes and generates report
     based on the routes""",
    'description': """This module will set routes, 
     shows customers in each route and generates report with customer details
     and due amount.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'live_test_url': 'https://www.youtube.com/watch?v=tdu6iBP2N6Y',
    'depends': ['base', 'sale_management', 'account_accountant'],
    'license': 'OPL-1',
    'price': 19.99,
    'currency': 'EUR',
    'data': [
        'security/delivery_route_groups.xml',
        'security/delivery_route_security.xml',
        'security/route_line_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/delivery_route_views.xml',
        'views/route_line_views.xml',
        'report/delivery_route_reports.xml',
        'report/delivery_route_templates.xml',
        'wizard/route_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'customer_route_management/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
