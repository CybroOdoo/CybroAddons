# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Sale Report Format Editor',
    'version': '15.0.1.0.0',
    'category': 'Sale',
    'summary': 'Sale Report Format Editor',
    'description': """Sale Report Format Editor For Configuring the Sale Templates""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': ['security/ir.model.access.csv',
             'data/design_templates.xml',
             'views/custom_layouts.xml',
             'views/document_base_layout.xml',
             'reports/custom_sale_template.xml',
             'reports/custom_sale_template_fantacy.xml',
             'reports/custom_sale_template_old_standard.xml',
             'reports/default_sale_template.xml',
             'template_view/default_template_view.xml',
             'template_view/normal_template_view.xml',
             'template_view/modern_template_view.xml',
             'template_view/old_template_view.xml',
             ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,

}
