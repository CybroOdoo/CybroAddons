# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Pharmaceutical ERP — Traceability, CoA & Audit Trail',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Certificate of Analysis, Batch Genealogy and Audit Trail for '
               'the Pharmaceutical ERP suite.',
    'description': """Certificates of Analysis per batch with a printable PDF, the QA release
     queue, upstream and downstream batch genealogy and an audit trail of
     tracked changes.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'mail',
        'stock',
        'mrp',
        'purchase_stock',
        'pharmaceutical_base',
        # The audit trail view reads mail_tracking_value directly. In Odoo 19
        # that model moved out of `mail` into its own `mail_tracking` module,
        # so it must be depended on explicitly or the SQL view fails to build.
        'mail_tracking',
        # CoA/genealogy surface Deviation & CAPA relations directly, so this tier
        # requires the CAPA & Deviation tier. Installing CoA installs it too;
        # pharma_capa_deviation stays independently installable without CoA.
        'pharma_capa_deviation',
    ],
    'data': [
        'security/ir.access.csv',
        'data/pharma_sequences_data.xml',
        'reports/pharma_coa_report.xml',
        'views/pharma_coa_views.xml',
        'views/audit_trail_views.xml',
        'views/stock_lot_genealogy_views.xml',
        'views/mrp_production_views.xml',
        'views/pharma_qa_release_views.xml',
        'views/menus.xml',
        'views/pharma_reporting_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'pharma_traceability_coa/static/src/css/pharma_coa_report.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
