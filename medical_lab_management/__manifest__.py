###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': "Medical Lab Management",
    'version': '12.0.1.0.1',
    'summary': """Manage Medical Lab Operations.""",
    'description': """Manage Medical Lab General Operations.""",
    'author': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'company': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Industries',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/lab_users.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/lab_patient_view.xml',
        'views/test_unit_view.xml',
        'views/lab_test_type.xml',
        'views/lab_test_content_type.xml',
        'views/physician_specialty.xml',
        'views/physician_details.xml',
        'views/lab_request.xml',
        'views/lab_appointment.xml',
        'views/account_invoice.xml',
        'report/report.xml',
        'report/lab_test_report.xml',
        'report/lab_patient_card.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
