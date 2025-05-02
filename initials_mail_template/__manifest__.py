# -*- coding: utf-8 -*-
{
    "name": "Enviar correo electronico al crear iniciales de clientes",
    'author': 'David Cartaya',
    "version": "16.0",
    "depends": ['base', '3mit_account_advance_payment'],
    "data": [
        'data/initials_mail_template.xml',
        'views/account_advanced_payment.xml',
    ],
    'installable': True,
}
