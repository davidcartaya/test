# -*- coding: utf-8 -*-
{
    "name": "Reportes de Cobranzas",
    "version": "16.0",
    'author': 'David Cartaya',
    "depends": ['base', 'sale', 'account', 'type_contract'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/collection_wizard.xml',
        'report/report_morosidad.xml',
        'report/report_vencidos.xml',

    ],
    'installable': True,
}
