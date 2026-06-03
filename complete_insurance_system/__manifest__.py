# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Complete Insurance Management',
    'version':'17.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """Employee Insurance Management""",
    'description': """Manages insurance amounts for employees to be deducted 
    from salary""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'contacts', 'crm', 'website', 'account'],
    'data': [
        'security/insurance_management_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/res_insurance_views.xml',
        'views/insurance_policy_category_views.xml',
        'views/insurance_policy_sub_category_views.xml',
        'views/insurance_policy_views.xml',
        'views/insurance_for_views.xml',
        'views/insured_document_views.xml',
        'views/claim_document_views.xml',
        'views/claim_reason_views.xml',
        'views/nominee_relation_views.xml',
        'views/customer_views.xml',
        'views/res_partner_views.xml',
        'views/website_quotation_views.xml',
        'views/insurance_quote_request_template.xml',
        'views/thanks_form.xml',
        'views/insurance_claim_views.xml',
        'report/res_insurance_templates.xml',
        'report/res_insurance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'complete_insurance_system/static/src/js/insurance_dashboard.js',
            'complete_insurance_system/static/src/xml/dashboard.xml',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'
        ],
        'web.assets_frontend': [
            'complete_insurance_system/static/src/js/insurance_request.js',
        ],
    },

    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
