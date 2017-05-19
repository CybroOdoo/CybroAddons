{
    'name': 'Taxless Sale & Purchase',
    'version': '1.0',
    'category': 'Sale Management',
    'sequence': 7,
    'summary': 'hide Tax from Sales and Purchases',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'description': """


=======================


""",
    'depends': ['base', 'sale', 'purchase', 'taxless_accounting'],
    'data': [
        'purchase_view.xml'

    ],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
