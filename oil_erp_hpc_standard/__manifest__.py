# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
# ############################################################################

{
    'name': 'Oil ERP - HPM & ASTM Volume Correction Standards',
    'version': '19.0.1.0.0',
    'category': 'Industries',
    'summary': 'Hydrocarbon Product Measurement (HPM) — ASTM D1250 Groups A-F, AGA-8, GPA TP-27, OIML R117, SAES-Y-100, AGES-SP-11-01 with full product-group K0 table, LPG coefficient table, range validation, and per-standard rounding.',
    'description': """

Provides API MPMS, GPA TP-27, and AGA-8 volume correction calculations with support for liquid hydrocarbons, LPG, and natural gas.
Includes standard-specific validations and a unified correction engine for custody transfer, production, and SCADA workflows.

""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_project',
        'stock',
        'product',
    ],
    'data': [
        'security/oil_hpc_security.xml',
        'security/ir.model.access.csv',
        'views/product_category_views.xml',
        'views/product_template_views.xml',
        'wizard/production_views.xml',
        'views/stock_move_views.xml',
        'views/stock_location_views.xml',
        'views/pivot_graph_views.xml',
    ],
    'images': [
            'static/description/banner.jpg',
        ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
