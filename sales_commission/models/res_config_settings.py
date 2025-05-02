from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CommissionConfigAccountLine(models.Model):
    _name = 'commission.config.account.line'
    _description = 'Línea de Configuración de Comisión (Cuenta y Porcentaje)'

    company_id = fields.Many2one('res.company', string="Compañía", ondelete="cascade", required=True)
    account_id = fields.Many2one('account.account', string="Cuenta", required=True)
    percentage = fields.Float(string="Porcentaje", required=True)

    @api.constrains('company_id', 'percentage')
    def _check_total_percentage(self):
        for line in self:
            total_percentage = sum(line.company_id.commission_account_line_ids.mapped('percentage'))
            if total_percentage > 100:
                raise ValidationError("La suma total de los porcentajes de comisión no puede superar el 100%.")


class CommissionConfigSale(models.TransientModel):
    _inherit = "res.config.settings"

    commission_configuration = fields.Selection(
        [
            ('sale_order', 'Basado en Pedido de Venta'),
            ('invoice', 'Basado en Factura'),
        ],
        string='Pagar Comisión Basado en',
        default='invoice'
    )
    
    commission_calc_on = fields.Selection(
        [
            ('product_category', 'Categoría de Producto'),
            ('product', 'Producto'),
            ('partner', 'Cliente')
        ],
        string='Cálculo de Comisión Basado en',
        default='product'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(CommissionConfigSale, self).default_get(fields_list)
        last_config = self.search([], limit=1, order="id desc")
        if last_config:
            if last_config.commission_configuration:
                res.update({
                    'commission_configuration': last_config.commission_configuration,
                })
            if last_config.commission_calc_on:
                res.update({
                    'commission_calc_on': last_config.commission_calc_on,
                })
            # Si se requieren líneas previas, se podrían obtener y asignar a commission_account_line_ids aquí
        return res
