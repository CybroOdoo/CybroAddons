# -*- coding: utf-8 -*-
{
    'name': "Magic Color Note",
    'summary': """Automatically Change the Colour Based on the Date Interval Config of Notes""",
    'description': """
        Set a date interval in integers.
        All notes belonging to the period will be assigned the defined colour.
    """,
    'version': '0.3',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'category': 'Tools',
    'depends': ['base', 'note'],
    'data': ['views/color_note.xml',
             'views/color_config.xml'],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
