# -*- coding: utf-8 -*-

from odoo import api, fields, models    

class CommissionSetting(models.Model): 
    _name = 'commission.settings'
    _description = "Configuración de Comisión"
    
    employee_id = fields.Many2one('hr.employee', 'Vendedor')
    commission_type = fields.Selection(
        [("fixed", "Fijo"), ("per", "Porcentaje")],
        string="Tipo de Comisión"
    )
    amount = fields.Float('Monto o porcentaje')
    product_id = fields.Many2one(
        'product.template',
        string='Producto'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente'
    )
    categ_id = fields.Many2one(
        'product.category',
        string='Categoria de producto'
    )
