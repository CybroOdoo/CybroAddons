# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Mohammed Ajmal P (odoo@cybrosys.com)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributes in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along this program.
#   If not, see <http://www.gnu.org/license/>.
#
################################################################################
{
    'name': "Sale Purchase mixed Report",
    'summary': """Mixed reports of Sale and Purchase data""",
    'description': """Mixed reports of Sale and Purchase data""",
    'category': 'Technical',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'sale', 'purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'reports/sale_purchase_report_views.xml',
        'reports/sale_purchase_pdf_template.xml',
        'wizards/wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/sale_purchase_mixed_report/static/src/js/action_manager.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
