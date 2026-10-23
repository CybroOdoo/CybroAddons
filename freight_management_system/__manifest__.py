#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Freight Management',
    'version': '20.0.1.0.0',
    'category': 'Industries',
    'summary': 'Manage freight orders, custom clearance and shipment '
               'tracking.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['product', 'account', 'mail', 'uom'],
    'data': [
        'security/freight_security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/freight_routes_data.xml',
        'data/mail_template_data.xml',
        'views/freight_order_views.xml',
        'views/freight_port_views.xml',
        'views/freight_container_views.xml',
        'views/custom_clearance_views.xml',
        'views/freight_service_views.xml',
        'views/clearance_revision_views.xml',
        'report/freight_report_templates.xml',
        'report/tracking_report_templates.xml',
        'wizard/custom_clearance_revision_views.xml',
        'wizard/freight_order_track_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
