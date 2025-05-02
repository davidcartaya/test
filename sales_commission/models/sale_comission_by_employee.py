from odoo import api, fields, models

class SaleCommissionByEmployee(models.Model):
    _name = 'sale.commission.by.employee'
    _description = 'Comisión por Empleado'

    commission_id = fields.Many2one('sale.commission', string='Comisión', ondelete='cascade', readonly=True, invisible=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    amount = fields.Float('Monto de Comisión', required=True)