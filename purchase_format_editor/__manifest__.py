# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
    'name': 'Purchase Report Format Editor',
    'version': '16.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Configure Purchase Report Templates With Different Styles',
    'description': "To configure purchase report templates with different "
                   "styles, you need to design a layout that includes "
                   "components such as headers, tables, summaries, and "
                   "footers, and customize the template with suitable fonts "
                   "and visual elements to match your desired styles.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/doc_layout_purchase_data.xml',
        'views/doc_layout_purchase_views.xml',
        'views/base_document_layout_views.xml',
        'report/purchase_order_custom_templates.xml',
        'report/purchase_order_fantacy_templates.xml',
        'report/purchase_order_old_standard_templates.xml',
        'report/purchase_order_templates.xml',
        'report/purchase_order_custom_quotation_templates.xml',
        'report/purchase_order_quotation_fantacy_templates.xml',
        'report/purchase_order_quotation_old_standard_templates.xml',
        'report/purchase_quotation_templates.xml',
        'views/purchase_order_default_templates.xml',
        'views/purchase_order_normal_templates.xml',
        'views/purchase_order_modern_templates.xml',
        'views/purchase_order_old_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
