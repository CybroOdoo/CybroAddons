# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'POS Product Category Filter',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Show only specified categories of product in point of sale ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'description': """

=======================



""",
    'depends': ['point_of_sale'],
    'images': ['static/description/banner.jpg'],
    'data': ['views/custom_view.xml',
             'views/template.xml'],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
