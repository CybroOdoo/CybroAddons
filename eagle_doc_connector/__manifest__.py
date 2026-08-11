# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
{
    'name': 'Eagle Doc Connector',
    'version': '19.0.1.0.0',
    'sequence': 2,
    'summary': """Eagle Doc Connector enables users to connect Odoo with
     Eagle Doc for AI-powered invoice scanning and bookkeeping automation""",
    'description': """Integrate Eagle Doc with Odoo for AI-powered document
     processing. It also helps synchronize vendor/customer master data,
     track sub-business profiles per company, and submit vendor and
     bookkeeping-account correction feedback to Eagle Doc.""",
    'category': 'Accounting',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': [
        'base',
        'accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/eagle_doc_cron.xml',
        'data/eagle_doc_actions.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'wizard/eagle_doc_feedback_wizard_views.xml',
        'wizard/eagle_doc_usage_wizard_views.xml',
        'views/account_move_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'eagle_doc_connector/static/src/js/account_move_list_controller.js',
            'eagle_doc_connector/static/src/xml/account_move_list_buttons.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
}
