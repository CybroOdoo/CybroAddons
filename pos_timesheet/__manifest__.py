# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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
    'name': 'POS Timesheet',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Efficiently track employees work hours in POS.""",
    'description': """This module enhances the Point of Sale (POS) 
     functionality by automatically calculating timesheet for employees based 
     on their activities in the POS.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'hr_timesheet', 'project'],
    'data': [
        'views/pos_config_views.xml',
        'views/pos_session_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_timesheet/static/src/css/worked_hour_popup.css',
            'pos_timesheet/static/src/js/HeaderLockButton.js',
            'pos_timesheet/static/src/js/model.js',
            'pos_timesheet/static/src/js/Chrome.js',
            'pos_timesheet/static/src/js/Popups/ClosePosPopup.js',
            'pos_timesheet/static/src/js/Popups/WorkedHourPopup.js',
        ],
        'web.assets_qweb': [
            'pos_timesheet/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
