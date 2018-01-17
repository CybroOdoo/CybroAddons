# -*- coding: utf-8 -*-
{
    'name': 'Aged partner filter',
    'summary': "Aged partners filtered pdf reports",
    'version': '10.0.1.0',
    'author': 'Cybrosys Technologies',
    'website': "http://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    "category": "Accounts",
    'depends': ['base', 'account', 'sale'],
    'data': ['views/filter_aged_partners.xml',
             ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
}
