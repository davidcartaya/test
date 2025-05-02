# -*- coding: utf-8 -*-
{
    'name': 'POS Order Type in Order Line',
    'version': '1.0',
    'author': 'David Cartaya',
    'category': 'Point of Sale',
    'depends': ['point_of_sale', 'hr', 'bi_pos_order_types', 'stock'],
    'data': [
        'views/pos_config_view.xml',
        'views/stock_picking_views.xml',

    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_order_line_order_type/static/src/js/models.js',
            'pos_order_line_order_type/static/src/js/product_screen.js',
            'pos_order_line_order_type/static/src/input_popups/deliveryTypePopup.js',
            'pos_order_line_order_type/static/src/xml/pos.xml',
        ],
    },
    'application': True,
    'installable': True,
}
