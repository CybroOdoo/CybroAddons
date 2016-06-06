{
    'name': "Awesome Backend Theme",
    'summary': """ You can simply edit font colour and background colour in this Theme.""",
    'description': """ Your own colors on your interface.""",
    'author': "Cybrosys Tachno Solutions",
    'category': 'Theme',
    'version': '1.0',


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
