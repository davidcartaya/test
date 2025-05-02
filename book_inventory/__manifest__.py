# -*- coding: utf-8 -*-

{
    'name': "Libro de inventario",
    'author': 'David Cartaya',
    'license': 'AGPL-3',
    'depends': ['account', 'stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'report/account_inventary_book_report.xml',
        'wizard/account_inventory_book.xml',
    ],  
    "installable": True,
}