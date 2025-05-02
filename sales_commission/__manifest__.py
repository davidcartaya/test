{
    "name" : "Sales Commission",
    "version" : "16.0.4.0",
    "category" : "Sales",
    "author": "David Cartaya <david.cartaya2003@gmail.com>",
    "depends" : ['base','sale_management','account'],
    "data": [
        'security/commission_security.xml',
        'security/ir.model.access.csv',

        'data/data.xml',

        'views/account_move.xml',
        'views/product_category.xml',
        'views/res_company.xml',
        'views/product_template.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/sale_commission_line.xml',
        'views/sale_commission_view.xml',

        'report/commission_report.xml',
        'report/report_commission_template.xml',
    ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
    'license': 'OPL-1',
}
