# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (<https://www.cybrosys.com>)
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
    'version': '19.0.1.0.1',
    'category': 'Point of Sales',
    'summary': 'User can login pos session by face recognition method',
    'description': 'User can login pos session by face recognition '
                   'method.If any unauthorized login is detected a warning '
                   'message is arise.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_hr'],
    'data': [
            'views/hr_employee_views.xml'
        ],
    'assets': {
        'point_of_sale._assets_pos': [
            'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1/dist/face-api.js',
            'https://code.jquery.com/jquery-3.3.1.min.js',
            'https://unpkg.com/webcam-easy/dist/webcam-easy.min.js',
            'pos_face_recognition/static/src/js/SelectionPopup.js',
            'pos_face_recognition/static/src/xml/SelectionPopup.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
