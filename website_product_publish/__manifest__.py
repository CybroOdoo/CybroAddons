# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Quick Product Publish/Unpublish',
    'version': '14.0.1.0.0',
    'summary': """Quick Product Publish& Unpublish on Website, Multiple Product Publish, Category wise publish""",
    'description': """quick product published & unpublished on website, multi product publish, category vise publish, 
                      multi product publish/unpublish, products published & unpublished on website,
                      quick product publishe, publish all products in a category, website publish, all publish,
                      publish, unpublish, odoo13, website, ecommerce,
                    """,
    'category': 'Website',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/assets.xml',
        'views/product_template.xml',
        'views/product_category.xml',
        'security/ir.model.access.csv',
        'wizard/product_publish_view.xml',

    ],
    'qweb': ["static/src/xml/website_backend_quick_publish.xml"],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
