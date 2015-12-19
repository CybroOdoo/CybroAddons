{
    'name': 'Sale Discount for Total Amount',
    'version': '1.0',
    'category': 'sale',
    'sequence': 6,
    'summary': "extension of default Sale Management module meant to provide discount for total amount",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',

    'description': """

Sale Discount for Total Amount
=======================
Module to manage discount for total amount in Sale.
        Two Type of Discount,
        Discount by a fixed value,
        Discount by a percentage...
""",
    'depends': ['sale', 'base', 'stock'],
    'data': [
        'views/sale_view.xml',
        'views/account_invoice_view.xml'

    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
