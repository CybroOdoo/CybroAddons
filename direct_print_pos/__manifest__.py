# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
    'name': 'Direct Pos Print',
    'version': "19.0.1.0.0",
    'category': 'Extra Tools',
    'summary': 'Direct POS Print is a utility that enables direct printing '
               'from Odoo POS using the cloud-based PrintNode API. This '
               'connector allows users to send print jobs from their Odoo '
               'system to any printer linked to their PrintNode account.',
    'description': 'PrintNode is a cloud-based printing service that allows '
                   'businesses to print documents remotely from any device or '
                   'location. Direct POS Print for Odoo is a software module '
                   'that enables POS receipt printing through printers '
                   'already configured via the Direct Print module, '
                   'integrating Odoo '
                   'with PrintNode printing capabilities.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ["point_of_sale", "direct_print_odoo"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "report/pos_receipt_template.xml",
        "report/pos_template_data.xml",
        "views/res_config_settings_view.xml",
        "views/pos_template_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "direct_print_pos/static/src/js/pos_print.js",
            "direct_print_pos/static/src/xml/pos_receipt_template.xml",
        ]
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}