{
'name': 'Validar que las lineas de pedidos tengan un usuario/vendedor asignado',
    'summary': 'Validar que las lineas de pedidos tengan un usuario/vendedor asignado',
    'author': 'David Cartaya',
    'depends': ['web', 'pos_sale', 'point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'validation_user_lines_pos/static/src/js/models.js',
        ],
    },
    'installable': True,
}
