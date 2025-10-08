# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Albin PJ (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Certificate And License With Expiry Management',
    'version': '16.0.1.0.0',
    'category': 'Document Management',
    'summary': """Certificate And License With Expiry Management helps you 
                to manage certificates and licenses""",
    'description': """We can manage the certificates and licenses 
                using this module""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['project', 'contacts', 'website', 'product'],
    'data': [
        'security/certificates_license_expiry_groups.xml',
        'security/certificates_security.xml',
        'security/license_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/certificates_mail_template_data.xml',
        'data/license_mail_template_data.xml',
        'views/certificates_license_menus.xml',
        'views/certificates_views.xml',
        'views/license_views.xml',
        'views/certificates_portal.xml',
        'views/res_partner_views.xml',
        'views/license_portal.xml',
        'views/certificates_search.xml',
        'views/license_search.xml',
        'report/certificates_reports.xml',
        'report/license_reports.xml',
        'report/certificates_templates.xml',
        'report/license_templates.xml',
    ],
    'demo': [
        'demo/certificates_license_types_demo.xml',
        'demo/certificates_license_tags_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'certificate_license_expiry/static/src/css/certificate_license.css',
        ],
        'web.assets_frontend': [
            'certificate_license_expiry/static/src/js/certificates_group_by.js',
            'certificate_license_expiry/static/src/js/certificates_search.js',
            'certificate_license_expiry/static/src/js/license_group_by.js',
            'certificate_license_expiry/static/src/js/license_search.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
