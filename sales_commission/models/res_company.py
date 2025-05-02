from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_account_line_ids = fields.One2many(
        'commission.config.account.line', 'company_id', 
        string="Cuentas y Porcentajes de Comisión",
    )
