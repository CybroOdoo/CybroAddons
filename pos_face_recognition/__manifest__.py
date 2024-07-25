# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
{
    'name': 'Pos Face Recognition',
    'version': '17.0.1.0.0',
    'category': 'Point of Sales',
    'summary': 'User can login pos session by face recognition method',
    'description': 'User can login pos session by face recognition '
                   'method.If any unauthorized login is detected a warning '
                   'message is arise.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'pos_hr'],
    'assets': {
        'point_of_sale._assets_pos': [
            'https://unpkg.com/webcam-easy/dist/webcam-easy.min.js',
            'pos_face_recognition/static/src/js/face-api.min.js',
            'pos_face_recognition/static/src/js/LoginScreen.js',
            'https://code.jquery.com/jquery-3.3.1.min.js',
            'pos_face_recognition/static/src/xml/LoginScreen.xml'
        ]
    },
    'data': [
        'views/hr_employee_view.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
