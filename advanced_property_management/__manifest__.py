# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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
    'name': "Advanced Property Management",
    'version': '17.0.1.0.0',
    'category': 'Industries',
    'summary': """Manage your properties by selling, renting and bidding""",
    'description': """The module makes it simple for you to manage
     your properties""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['mail', 'sale_management', 'website',
                'base_geolocalize'],
    'data': [
        'security/user_groups.xml',
        'security/property_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/advanced_property_management_data.xml',
        'data/ir_cron_data.xml',
        'views/property_property_views.xml',
        'views/property_facility_views.xml',
        'views/property_tag_views.xml',
        'views/property_search_pannel_views.xml',
        'views/property_templates.xml',
        'views/property_commision_views.xml',
        'views/property_sale_views.xml',
        'views/property_rental_views.xml',
        'views/res_partner_views.xml',
        'views/rental_bill_views.xml',
        'views/property_auction_views.xml',
        'reports/property_sale_report.xml',
        'reports/property_report.xml',
        'wizards/property_sale_report_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'advanced_property_management/static/src/js/property_website.js',
            'advanced_property_management/static/src/js/property_item.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
