{
    'name': 'Salon Booking',
    'summary': """   """,
    'description': """  """,
    'author': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Test',
    'version': '0.1',

    'depends': ['base',
                'sale',
                'hr',
                ],

    'data': [
             'templates/template.xml',
             'security/ir.model.access.csv',
             'views/chair_view.xml',
             'views/period_view.xml',
             'views/day_view.xml',
             'views/month_view.xml',
             'views/autofill_month.xml',
             'views/salon_book_view.xml',
             'sweep/sweep_sale_order.xml',
             'sweep/sweep_menu_act.xml',
             'sweep/sweep_product.xml',
             'sweep/sweep_invoice.xml',
             ],

    'demo': ['demo/demo_chair.xml',
             'demo/demo_time.xml',
             'demo/demo_day.xml',
             'demo/demo_month.xml',

             ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}

