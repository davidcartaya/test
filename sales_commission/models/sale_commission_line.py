# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SalesCommissionLines(models.Model):
    """
    Líneas de Comisión de Ventas
    """
    _name = 'sale.commission.line'
    _order = "id desc"
    _description = "Líneas de Comisión de Ventas"

    commission_sheet_id = fields.Many2one('sale.commission', string='Hoja de Comisión', ondelete='cascade', readonly=True, invisible=True)
    product_id = fields.Many2one('product.product', string='Producto')
    quantity = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Precio Unitario')
    amount = fields.Float('Monto de comision')