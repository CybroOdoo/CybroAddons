# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
#
################################################################################
{
    'name': 'Multiple DatePicker Widget',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Widget for picking multiple dates in odoo 17',
    'description': 'Multiple dates can be assigned to a field where you want '
                   'to add those',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'assets': {
        'web.assets_backend': {
            '/multiple_datepicker_widget/static/src/css/datepicker_widget.css',
            '/multiple_datepicker_widget/static/src/js/lib/bootstrap-datepicker.min.js',
            '/multiple_datepicker_widget/static/src/js/multiple_date_picker_widget.js',
            '/multiple_datepicker_widget/static/src/xml/datepicker_widget_templates.xml',
        },
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
