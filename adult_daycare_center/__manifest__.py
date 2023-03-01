# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
{
    'name': "Adult Day Care Center",
    'version': '16.0.1.0.0',
    'category': 'Tools',
    'summary': """ Adult Day Care Center For Senior Citizens """,
    'description': """ Adult Day Care Center For Senior Citizens""",
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'depends': ['crm', 'project', 'sale_management', 'website', 'account', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/res_partners_views.xml',
        'views/crm_lead_views.xml',
        'views/product_template_views.xml',
        'views/assessment_request_template.xml',
        'views/activity_type_views.xml',
        'views/daycare_activities_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
        'reports/res_partner_report.xml',
        'reports/crm_lead_report.xml',
        'reports/sale_template_inherit.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
