from odoo import http
from odoo.http import request, Response
import json


class InvoiceController(http.Controller):

    @http.route('/api/partner_invoices_balance', type='http', auth='public', methods=['POST'], csrf=False)
    def get_partner_invoices_balance(self):
        """
        Endpoint para obtener las facturas asociadas a un cliente que están no pagadas o parcialmente pagadas,
        incluyendo el monto total, monto pendiente, si es una cuota y el total global pendiente.
        """
        try:
            data = json.loads(request.httprequest.data)

            partner_id = data.get('partner_id')

            if not partner_id:
                return Response(json.dumps({'error': 'El campo partner_id es obligatorio'}), status=400, mimetype='application/json')

            partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))], limit=1)

            if not partner:
                return Response(json.dumps({'error': 'El cliente no existe'}), status=404, mimetype='application/json')

            invoices = request.env['account.move'].sudo().search([
                ('partner_id', '=', int(partner_id)),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice']),
            ])

            if not invoices:
                return Response(json.dumps({'error': 'No se encontraron facturas para este cliente'}), status=404, mimetype='application/json')

            invoices_balance = []
            total_pending_balance = 0.0

            for invoice in invoices:
                total_amount = invoice.amount_total
                pending_amount = invoice.amount_residual
                is_quote = getattr(invoice, 'is_quote', False) or (invoice.number_quote > 0 if invoice.number_quote else False)


                total_pending_balance += pending_amount

                invoices_balance.append({
                    'invoice_id': invoice.id,
                    'invoice_name': invoice.name,
                    'payment_state': 'Parcialmente pagada' if invoice.payment_state == 'partial' else 'Sin pagar',
                    'total_amount': round(total_amount, 2),
                    'pending_amount': round(pending_amount, 2),
                    'is_quote': is_quote,
                })

            response_data = {
                'partner_id': partner_id,
                'partner_name': partner.name,
                'invoices_balance': invoices_balance,
                'total_pending_balance': round(total_pending_balance, 2),
                'status': 200
            }
            return Response(json.dumps(response_data), status=200, mimetype='application/json')

        except Exception as e:
            return Response(json.dumps({'error': str(e)}), status=500, mimetype='application/json')
