{
    'name': "Custom Backend Appearance",
    'summary': """ You can simply change font colour and background colour using this Module.""",
    'description': """ Your own colors on your interface.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Theme',
    'version': '2.0',
    'depends': [
        'base',
        'web_widget_color', ],
    'data': ['template/template.xml',
             'views/theme_view.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
