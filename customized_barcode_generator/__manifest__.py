# -*- coding: utf-8 -*-
{
    'name': 'Cost Price as Code in Barcode',
    'version': '16.0.1.0.0',
    'summary': """Print user defined product labels.""",
    'description': """The module enables user to print customized product labels, Barcode, Barcode Generator, Barcode Label, Product Label, Product Barcode Generator, Product Barcode, Label Print, Product Label Print
                    """,
    'category': 'Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'web', 'product', 'account'],
    'website': 'https://www.cybrosys.com',
    'data': [
        'report/product_label_template.xml',
        'views/barcode_generator_view.xml',
        'security/ir.model.access.csv'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
