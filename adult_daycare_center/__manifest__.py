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
    'name': "Adult Daycare Center",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """ Adult Day Care Center For Senior Citizens """,
    'description': """ Adult Day Care Center For Senior Citizens to manage
     Adult Daycare Center and Daycare activities""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['crm', 'project', 'sale_management', 'website', 'account',
                'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_menu_data.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/product_template_views.xml',
        'views/assessment_request_templates.xml',
        'views/activity_type_views.xml',
        'views/daycare_activities_views.xml',
        'views/sale_order_views.xml',
        'views/adult_daycare_center_menus.xml',
        'report/res_partner_reports.xml',
        'report/crm_lead_reports.xml',
        'report/sale_order_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
