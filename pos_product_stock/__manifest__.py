# -*- coding: utf-8 -*-
{
    'name': 'POS Product Stock',
    'version': "16.0.1.0.0",
    'category': 'Point Of Sale',
    'author': 'David Cartaya',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'point_of_sale', 
        'stock',
    ],
    'data': [
        'views/res_cofig_settings_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_product_stock/static/src/xml/product_item.xml',
            'pos_product_stock/static/src/css/product_quantity.scss',
            'pos_product_stock/static/src/js/pos_location.js',
            'pos_product_stock/static/src/js/pos_payment_screen.js',
            'pos_product_stock/static/src/js/pos_session.js',
            'pos_product_stock/static/src/js/deny_order.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
