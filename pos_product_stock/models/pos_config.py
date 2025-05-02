from odoo import fields, models


class PosConfig(models.Model):
    """inherit pos.config to add fields."""
    _inherit = 'pos.config'

    pos_stock_location_id = fields.Many2one('stock.location', string='Ubicación de stock',
                                         help="This field helps to hold the location")
    location_from = fields.Selection([('all_warehouse', 'Todas las ubicaciones'),
                                      ('current_warehouse', 'Ubicación actual')],
                                     string="Mostrar stock de",
                                     help="Puede elegir la ubicación donde desea mostrar el stock.")
    display_stock_setting = fields.Boolean(string="Mostrar Stock",
                                           help="Al habilitarlo, podrá ver la cantidad de Stock en el punto de venta.",
                                           store=True)
    stock_product = fields.Selection([('on_hand', 'Cantidad a Mano'),
                                      ('incoming_qty', 'Cantidad entrante'),
                                      ('outgoing_qty', 'Cantidad saliente'),
                                      ('available_qty', 'Cantidad disponible')],
                                     string="Tipo de stock",
                                     help="Te ayuda a elegir la cantidad que quieres que sea visible en pos")
