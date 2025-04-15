# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': 'Advanced Fleet Rental Management',
    'version': '17.0.1.0.0',
    'category': "Extra Tools",
    'summary': """This module will helps you to give the vehicles for Rent.""",
    'description': "This module enhances Odoo’s fleet management "
                   "functionality for vehicle rentals, including cars, "
                   "vans, bikes, and jeeps. Key features include:"
                   "Detailed rental contracts and invoicing."
                   "Management of daily, hourly, and kilometer-based rental terms."
                   "Integration with Odoo’s accounting module for automated invoicing and payments."
                   "Tracking of vehicle status, maintenance, and extra service charges."
                   "A user-friendly dashboard for monitoring fleet performance and rental contracts.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['fleet', 'mail', 'sale_management', 'account', ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/product_product_data.xml',
        'data/ir_sequence_data.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_dashboard.xml',
        'views/multi_image_views.xml',
        'views/fleet_rental_contract_views.xml',
        'report/fleet_rental_contract_report.xml',
        'report/fleet_rental_contract_template.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/rental_payment_plan_views.xml',
        'views/cancellation_policy_views.xml',
        'views/fleet_dashboard.xml',
        'wizard/damage_invoice_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'advanced_fleet_rental/static/src/js/fleet_dashboard.js',
            'advanced_fleet_rental/static/src/xml/fleet_dashboard.xml',
            'advanced_fleet_rental/static/src/css/xero_dashboard.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
