from odoo import models, fields, _, api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from itertools import groupby
from datetime import timedelta

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Super de la función _compute_invoice_status para agregar la lógica personalizada:
        - Si number_quote > 1 y is_process_quote es True en la orden,
          establece qty_to_invoice igual a product_uom_qty antes de la validación.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.number_quotes > 1 and line.order_id.is_process_quote and line.order_id.number_quotes == len(line.order_id.invoice_ids):
                line.qty_to_invoice = 0
            super(SaleOrderLine, self)._compute_invoice_status()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    number_quotes = fields.Integer('Número de cuotas a pagar')
    is_process_quote = fields.Boolean(string='Es pedido a cuota?', copy=False)

    def _create_invoices(self, grouped=False, final=False, date=None):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        invoice_vals_list = []
        invoice_item_sequence = 0
        previous_due_date = date or self.date_order.date()

        for order in self:
            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

            number_of_invoices = order.number_quotes if order.number_quotes > 0 else 1
            total_amount = order.amount_untaxed / number_of_invoices
            base_due_date = date or order.date_order.date()
            
            
            for quote in range(1, number_of_invoices + 1):
                invoice_vals = order._prepare_invoice()
                invoiceable_lines = order._get_invoiceable_lines(final)

                if not any(not line.display_type for line in invoiceable_lines):
                    continue

                invoice_vals['number_quote'] = quote
                invoice_vals['is_quote'] = True
                invoice_vals['amount_untaxed'] = total_amount

                invoice_line_vals = []
                down_payment_section_added = False
                for line in invoiceable_lines:
                    if not down_payment_section_added and line.is_downpayment:
                        invoice_line_vals.append(
                            Command.create(
                                order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                            ),
                        )
                        down_payment_section_added = True
                        invoice_item_sequence += 1

                    # Modificar el precio unitario directamente en la línea existente
                    line_vals = line._prepare_invoice_line(sequence=invoice_item_sequence)
                    line_vals['price_unit'] /= number_of_invoices  # Modificación del precio unitario
                    invoice_line_vals.append(Command.create(line_vals))
                    invoice_item_sequence += 1

                invoice_vals['invoice_line_ids'] += invoice_line_vals
                invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
            raise UserError(self._nothing_to_invoice_error_message())
        
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        
        moves.action_post()
        
        for index, move in enumerate(moves):
            due_date = previous_due_date + timedelta(days=7)
            move.write({
                'invoice_date_due': due_date,
                'invoice_date': previous_due_date
            })
            previous_due_date = due_date
        order.is_process_quote = True
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                'mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        
        return moves