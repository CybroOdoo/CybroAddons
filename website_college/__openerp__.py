# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Hilar AK(<hilar@cybrosys.in>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Website_college",

    'summary': """
        Odoo demo theme for an educational Institution which includes their front page, backend theme ..""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Cybrosys",
    'website': "http://cybrosys.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'website',
    'version': '9.0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'web',
                'website',
                'website_livechat',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/template.xml',
        'views/alumni.xml',
        'views/course.xml',
        'views/facility.xml',
        'views/gallery.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'images': ['/website_college/static/description/banner.jpg'],
    'installable': True,
    'application': True
}
