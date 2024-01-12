# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Athira PS (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Website Quotation Template Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': "Adding Quotation Template inside website",
    'description': "Using this new website quotation template snippet,we can"
                   "directly add the products inside the selected quotation  "
                   "template into the shopping cart.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'website_sale'],
    'data':
        [
            'views/sale_order_template_views.xml',
            'views/website_quotation_snippet_templates.xml',
        ],
    'assets': {
        'web.assets_frontend': [
            'website_quotation_template/static/src/js/snippet.js',
            'website_quotation_template/static/src/xml/snippet_template.xml',
            'website_quotation_template/static/src/css/snippet.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
