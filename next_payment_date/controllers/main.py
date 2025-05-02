from odoo import http, fields
from odoo.http import request, Response
import json
from datetime import timedelta


class PartnerOverdueInvoicesController(http.Controller):

    @http.route('/api/next_payment_date', type='http', auth='public', methods=['POST'], csrf=False)
    def get_next_payment_date(self):
        """
        Endpoint para obtener las facturas vencidas y no pagadas de un cliente,
        organizadas por cada orden de venta y la próxima factura a pagar por cada venta.
        """
        try:
            data = json.loads(request.httprequest.data)

            partner_id = data.get('partner_id')

            if not partner_id:
                return Response(json.dumps({'error': 'El campo partner_id es obligatorio'}), status=400, mimetype='application/json')

            partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))], limit=1)
            if not partner:
                return Response(json.dumps({'error': 'El cliente no existe'}), status=404, mimetype='application/json')

            sale_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner.id)])
            if not sale_orders:
                return Response(json.dumps({'error': 'No se encontraron órdenes de venta para este cliente'}), status=404, mimetype='application/json')

            overdue_invoices_not_quote_data = []
            overdue_invoices_quote_data = []

            for order in sale_orders:
                if len(order.invoice_ids) == 1:
                    for invoice in order.invoice_ids:
                        if not invoice.is_quote and invoice.state == 'posted' and invoice.payment_state == 'not_paid' and invoice.move_type == 'out_invoice':
                            if order.payment_term_id and invoice.invoice_date and invoice.invoice_date_due:
                                payment_dates = []
                                invoice_date = fields.Date.from_string(invoice.invoice_date)
                                invoice_due_date = fields.Date.from_string(invoice.invoice_date_due)
                                days_between_payments = order.payment_term_id.line_ids[0].days if order.payment_term_id.line_ids else 30
                                
                                payment_info = [] 
                                quote = 1

                                current_date = invoice_date
                                while current_date < invoice_due_date:
                                    if current_date <= invoice_due_date:
                                        payment_dates.append(current_date.strftime('%Y-%m-%d'))

                                        payments = request.env['account.payment'].sudo().search([
                                            ('reconciled_invoice_ids', 'in', [invoice.id]),
                                            ('date', '=', current_date)
                                        ])

                                        if not payments and current_date < fields.Date.today():
                                            payment_info.append({
                                                'number_quote': quote,
                                                'payment_date': current_date.strftime('%d-%m-%Y'),
                                                'status': 'No pagada'
                                            })
                                        
                                        quote += 1
                                        current_date += timedelta(days=days_between_payments)

                                next_payment_date = None
                                for date_str in payment_dates:
                                    payment_date = fields.Date.from_string(date_str)
                                    if payment_date > fields.Date.today():
                                        next_payment_date_not_quote = payment_date.strftime('%d-%m-%Y')
                                        break

                                overdue_invoices_not_quote_data.append({
                                    'invoice_id': invoice.id,
                                    'invoice_name': invoice.name,
                                    'amount_total': round(invoice.amount_total, 2),
                                    'amount_residual': round(invoice.amount_residual, 2),
                                    'invoice_date_due': invoice.invoice_date_due.strftime('%d-%m-%Y'),
                                    'overdue_quotes_data': payment_info,
                                })
                else:

                    invoices = order.invoice_ids.filtered(
                        lambda inv: inv.state == 'posted' and inv.payment_state == 'not_paid' and inv.move_type == 'out_invoice'
                    )

                    overdue_invoices = invoices.filtered(lambda inv: inv.invoice_date_due and inv.invoice_date_due < fields.Date.today())
                    upcoming_invoices = invoices.filtered(lambda inv: inv.invoice_date_due and inv.invoice_date_due >= fields.Date.today()).sorted(
                        key=lambda inv: inv.invoice_date_due
                    )

                    next_payment_date_quote = upcoming_invoices[0].invoice_date_due.strftime('%d-%m-%Y') if upcoming_invoices else None

                    for invoice in overdue_invoices:
                        overdue_invoices_quote_data.append({
                            'invoice_id': invoice.id,
                            'invoice_name': invoice.name,
                            'number_quote': invoice.number_quote,
                            'amount_total': round(invoice.amount_total, 2),
                            'amount_residual': round(invoice.amount_residual, 2),
                            'invoice_date_due': invoice.invoice_date_due.strftime('%d-%m-%Y') if invoice.invoice_date_due else None,
                        })

            response_data = {
                'partner_id': partner.id,
                'partner_name': partner.name,
                'status': 200,
            }

            if overdue_invoices_quote_data:
                response_data['overdue_invoices_quote_data'] = overdue_invoices_quote_data

            if overdue_invoices_not_quote_data:
                response_data['overdue_invoices_not_quote_data'] = overdue_invoices_not_quote_data

            if next_payment_date_not_quote:
                response_data['next_payment_date_not_quote'] = next_payment_date_not_quote

            if next_payment_date_quote:
                response_data['next_payment_date_quote'] = next_payment_date_quote

            return Response(json.dumps(response_data), status=200, mimetype='application/json')

        except Exception as e:
            response_data = {'error': f'Ocurrió un error: {str(e)}'}
            return Response(json.dumps(response_data), status=500, mimetype='application/json')
