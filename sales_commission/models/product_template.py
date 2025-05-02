from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    commission_ids = fields.One2many(
        'commission.settings',  # modelo relacionado
        'product_id',           # campo inverso en commission.settings
        string="Configuración de Comisiones"
    )
    is_commission_product = fields.Boolean('Producto de Comisión')
    commission_assignment = fields.Selection(
        [
            ('invoice', 'Por Factura'),
            ('sale_order', 'Por Venta')
        ],
        string="Asignación de Comisión",
        default='invoice'
    )
    amount_comission = fields.Float('Monto o Porcentaje de Comisión')
    commission_type = fields.Selection([
            ('per', 'Porcentaje'),
            ('fix', 'Fijo')
        ],
        string="Tipo de Comisión",
        default='fix'
    )

    @api.constrains('commission_ids')
    def _check_total_percentage(self):
        for record in self:
            percentage_lines = record.commission_ids.filtered(lambda l: l.commission_type == 'per')
            total_percentage = sum(percentage_lines.mapped('amount'))
            if total_percentage > 100:
                raise ValidationError("La suma total de los porcentajes de comisión no puede superar el 100%.")
