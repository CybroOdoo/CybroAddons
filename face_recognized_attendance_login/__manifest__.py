# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Face Recognized Attendance Login',
    'version': '16.0.2.0.0',
    'category': 'Human Resources',
    'summary': """Mark the attendance of employee by recognizing their face""",
    'description': """This module introduces a face recognition system in the 
    attendance module and the employees can Check In  and Check Out only after 
    recognizing their face """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'hr', 'hr_attendance'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'face_recognized_attendance_login/static/src/js/my_attendance.js',
            'face_recognized_attendance_login/static/src/js/face-api.min.js',
            'face_recognized_attendance_login/static/src/xml/attendance.xml',
            'face_recognized_attendance_login/static/src/css/my_attendance.css',
            'face_recognized_attendance_login/static/src/xml/kiosk_confirm.xml',
            'face_recognized_attendance_login/static/src/js/kiosk_confirm.js',
        ]
    },

    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
