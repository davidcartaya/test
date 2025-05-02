# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class SalesCommission(models.Model):
    """
    Comisión de Ventas
    """
    _name = 'sale.commission'
    _description = 'Comisión de Ventas'
    _order = "id desc"


    name = fields.Char('Nombre', default='Nuevo')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Vendedores')
    start_date = fields.Date('Fecha de Inicio')
    end_date = fields.Date('Fecha de Fin', readonly=True)
    commission_product_id = fields.Many2one('product.product', 'Producto de Comisión')
    company_id = fields.Many2one(
        'res.company',
        'Compañía',
        default=lambda self: self.env.user.company_id
    )
    total_commission_amt = fields.Float(
        'Monto Total de Comisión',
        store=True
    )
    commission_paid = fields.Boolean('Comisión Pagada', compute='_check_payment')
    commission_line_ids = fields.One2many('sale.commission.line', 'commission_sheet_id', string='Líneas de Comisión')
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('open', 'Abierto'),
            ('paid', 'Pagado')
        ],
        default='draft',
        string='Estado de la Comisión'
    )
    invoice_ids = fields.Many2many(comodel_name='account.move', string='Factura')
    employee_commission_ids = fields.One2many(
        'sale.commission.by.employee',
        'commission_id',
        string='Comisiones por Empleado'
    )
    invoice_count = fields.Integer(compute="_compute_invoice", copy=False, default=0, store=True)

    @api.depends('invoice_ids')
    def _compute_invoice(self):
        for record in self:
            invoices = record.mapped('invoice_ids')
            record.invoice_count = len(invoices)

    @api.constrains('employee_commission_ids')
    def _check_total_commission(self):
        for record in self:
            if not record.total_commission_amt <= 0.0:
                total_commission = sum(record.employee_commission_ids.mapped('amount'))
                if total_commission > record.total_commission_amt:
                    raise ValidationError("La suma total de las lineas de comisión de los empleados no puede superar el monto total de la comisión.")

    def _check_payment(self):
        """
        Verifica si TODAS las facturas asociadas están pagadas.
        Si todas están pagadas, marca la comisión como pagada y cambia el estado.
        """
        for record in self:
            if record.invoice_ids:
                all_paid = all(inv.payment_state == 'paid' for inv in record.invoice_ids)
                record.commission_paid = all_paid
                if all_paid:
                    record.state = 'paid'
            else:
                record.commission_paid = False

    def create_invoice_commission(self):
        """
        Crea una factura para cada línea de empleado en la comisión,
        y las guarda en el campo invoice_ids.
        """
        account_move = self.env['account.move']
        product = self.env['product.product'].sudo().search(
            [('is_commission_product', '=', True)],
            limit=1
        )

        if not product:
            raise UserError(_("Debe configurar un producto marcado como 'Producto de Comisión'."))

        all_invoice_ids = []

        for record in self:
            invoice_ids = []

            for emp_line in record.employee_commission_ids:
                partner = emp_line.employee_id.related_contact_ids[:1]
                if not emp_line.employee_id or not partner:
                    continue
                account = product.property_account_expense_id or self.env['account.account'].search([], limit=1)
                move = account_move.create({
                    'partner_id': partner.id,
                    'move_type': 'in_invoice',
                    'invoice_comission': True,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'quantity': 1,
                        'price_unit': emp_line.amount,
                        'account_id': account.id,
                    })]
                })

                invoice_ids.append(move.id)

            if invoice_ids:
                record.write({
                    'invoice_ids': [(6, 0, invoice_ids)],
                    'state': 'open',
                })
                all_invoice_ids.extend(invoice_ids)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', all_invoice_ids)],
            'target': 'current',
            'name': _('Facturas de Comisión')
        }
    
    @api.model_create_multi
    def create(self, val):
        """
        Sobrescribe la creación para asignar un nombre secuencial
        según la secuencia 'sale.commission'.
        """
        for vals in val:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission') or _('Nuevo')
            res = super(SalesCommission, self).create(vals)
            return res


    def action_view_invoice_ids(self):
        self.ensure_one()
        return {
            'name': _('Facturas de Comisión'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }