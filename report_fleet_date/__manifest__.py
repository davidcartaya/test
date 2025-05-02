# -*- coding: utf-8 -*-
{
    "name": "Reporte de flota por fecha",
    "summary": "Reporte de flota por fecha",
    'author': "David Cartaya",
    "description": """Reporte de flota por fecha""",
    "depends": [
        'base',
        'project'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/task_fleet_date.xml',
        'report/report.xml',

    ],
    'license': 'LGPL-3',
    "application": True,
    "installable": True,
    "auto_install": False,
}