# -*- coding: utf-8 -*-
{
    'name': "Odoo 15 Development Tutorials",

    'summary': """
        Odoo 15 Development Tutorials""",

    'description': """
        Odoo 15 Development Tutorials,
        Odoo 14 Development Tutorials,
        Odoo 13 Development Tutorials,
        Development Tutorials,
        Odoo Tutorials,
        Odoo13, Odoo14, odoo15, odoo Tutorials, odoo learning, odoo13 Tutorials, odoo14 Tutorials, Tutorials,
        Open acadaemy module for managing trainings:
        -Manage student enroll
        -Attendance registration
        -Trainer
        -Training sessions
        -Courses
        -More..
    """,

    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'live_test_url': 'https://bit.ly/3knPv8t',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tutorials',
    'version': '15.0.1.0.0',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'board', 'website_slides'],
    'images': ['static/description/banner.gif'],

    # always loaded
    'data': [
        'data/slide_channel_data.xml',
        'data/slide_channel_data_v13.xml',
        'data/slide_channel_data_v15.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/openacademy.xml',
        'views/partner.xml',
        'views/session_board.xml',
        'reports.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
