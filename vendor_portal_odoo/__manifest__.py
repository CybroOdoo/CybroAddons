# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Odoo Vendor Portal',
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': """Vendor Portal Management in Odoo""",
    'description': """This module helps to sent quotations for a product 
    to multiple vendors and vendors can add their
    price in their portal, and can choose best quotation for product""",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['website', 'purchase', 'portal', 'contacts', 'stock'],
    'data': [
        'security/vendor_rfq_security.xml',
        'security/ir.model.access.csv',
        'data/rfq_sequence.xml',
        'data/rfq_mail_templates.xml',
        'data/rfq_cron.xml',
        'wizard/register_vendor_views.xml',
        'views/res_partner_views.xml',
        'views/vendor_rfq_views.xml',
        'views/res_config_settings_views.xml',
        'views/portal_rfq_templates.xml',
        'views/vendor_portal_menus.xml',
        'wizard/rfq_done_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
