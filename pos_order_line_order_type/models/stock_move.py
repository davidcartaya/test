from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

class StockMove(models.Model):
    _inherit = 'stock.move'

    order_type_id = fields.Many2one(comodel_name='pos.order.type', string='Tipo de Pedido')
