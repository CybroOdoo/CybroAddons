{
    'name' : 'POS Change Table',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': "Change Table of Order in POS ",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'description': """


=======================


""",
    'depends': ['point_of_sale', 'pos_restaurant','base'],
    'data': [
        'template.xml'
    ],

    'qweb': [
        "static/src/xml/table_change.xml",
    ],
    'license': 'AGPL-3',
    'installable': True,
}
