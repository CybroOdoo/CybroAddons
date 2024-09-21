# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
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
###############################################################################
{
    'name': 'Docusign Odoo Connector',
    'version': '16.0.1.0.0',
    'summary': 'Integrating Docusign application with odoo',
    'description': """This module allows the odoo users Integration with DocuSign.
    We email the sales order to the customer for signature.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'depends': ['base', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/docusign_credentials_views.xml',
        'views/sale_order_views.xml',
        'wizard/send_document_views.xml',
    ],
    'assets': {
            'web.assets_backend': [
                'docusign_odoo_connector/static/src/js/edit_document.js',
                'docusign_odoo_connector/static/src/xml/pdf_viewer_field.xml',
            ],
        },
    'images': ['static/description/banner.png'],
    'external_dependencies': {
        'python': ['docusign_esign']
    },
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False
}
