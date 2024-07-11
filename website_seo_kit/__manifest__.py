# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
############################################################################
{
    'name': "Website SEO Kit",
    'version': '17.0.1.0.0',
    'summary': """This module help to generate seo content""",
    'description': """Website seo kit used for automatically generate meta titles,
     descriptions, and keywords for each product and product category""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Website',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.jpg'],
    'depends': ['base', 'website', 'website_sale'],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/product_public_category_form_view.xml',
        'views/generate_seo_views.xml',
        'views/website_seo_attributes_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
