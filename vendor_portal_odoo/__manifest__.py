# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Noorjahan N A (<https://www.cybrosys.com>)
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
    'name': 'Odoo Vendor Portal',
    'version': '15.0.1.0.0',
    'category': 'Purchase',
    'summary': """Vendor Portal Management in Odoo""",
    'description': """Vendor Portal Management in Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['website', 'purchase', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard.xml',
        'wizard/mark_done.xml',
        'data/rfq_sequence.xml',
        'data/rfq_mail_template.xml',
        'data/rfq_cron.xml',
        'views/vendor.xml',
        'views/vendor_rfq.xml',
        'views/res_config_settings.xml',
        'views/portal_rfq.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
