# -*- coding: utf-8 -*-

{
    'name': "Ticket de regalo en el pos",
    'author': 'David Cartaya',
    'license': 'AGPL-3',
    'depends': ['point_of_sale'],
    'data': [
    ],  
    'assets': {
        'point_of_sale._assets_pos': [
            'gift_ticket_pos/static/src/js/orderline.js',
            'gift_ticket_pos/static/src/xml/**/*',
        ],
    },
    "installable": True,
}