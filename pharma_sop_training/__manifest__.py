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
    'name': 'Pharmaceutical ERP — SOP & Training',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Standard Operating Procedure lifecycle and employee training '
               'compliance for the Pharmaceutical ERP suite.',
    'description': """SOP lifecycle and employee training compliance for the Pharmaceutical ERP.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pharmaceutical_base',
        'mrp',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pharma_sop_sequence.xml',
        'data/pharma_cron_data.xml',
        'views/pharma_sop_views.xml',
        'views/pharma_training_views.xml',
        'views/mrp_routing_views.xml',
        'views/pharma_bmr_step_views.xml',
        'views/pharma_bmr_views.xml',
        'views/menus.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    # Not a standalone application: this module only grafts its "SOPs & Training"
    # section onto the core Pharmaceutical ERP "Quality" app.
    'application': False,
}
