{
    'name': 'Export Product Stock in Excel',
    'version': '0.2',
    'category': 'Warehouse',
    'license': "AGPL-3",
    'summary': "Current Stock Report for all Products in each Warehouse",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'depends': [
                'base',
                'stock',
                'sale',
                'purchase',
                'report_xlsx'
                ],
    'data': [
            'views/wizard_view.xml',
            ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
