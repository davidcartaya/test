from odoo import http
from odoo.http import request, Response
import json


class PaymentController(http.Controller):

    @http.route('/api/create_payment', type='http', auth='public', methods=['POST'], csrf=False)
    def create_payment(self):
        try:
            # Leer datos del cuerpo de la solicitud
            data = json.loads(request.httprequest.data)

            invoice_number = data.get('invoice_number')  # Número de la factura
            payment_amount = data.get('payment_amount')  # Monto del pago
            payment_date = data.get('payment_date')  # Fecha del pago
            journal_id = data.get('journal_id')  # Diario contable

            # Validaciones iniciales
            if not all([invoice_number, payment_amount, payment_date, journal_id]):
                response_data = {"error": "Faltan datos requeridos para procesar el pago"}
                return Response(json.dumps(response_data), status=400, mimetype='application/json')

            # Buscar la factura correspondiente
            invoice = request.env['account.move'].sudo().search([('name', '=', invoice_number)], limit=1)

            if not invoice:
                response_data = {"error": f"No se encontró la factura con el número {invoice_number}"}
                return Response(json.dumps(response_data), status=404, mimetype='application/json')
            
            if payment_amount > invoice.amount_residual:
                response_data = {
                    "error": f"No puede pagar un monto mayor al monto pendiente de la factura: {invoice.amount_residual}"
                }
                return Response(json.dumps(response_data), status=400, mimetype='application/json')
            
            if invoice.amount_residual <= 0 or invoice.payment_state in ['in_payment', 'paid']:
                response_data = {
                    "error": f"La factura con el número {invoice_number} ya está completamente pagada o en proceso de pago"
                }
                return Response(json.dumps(response_data), status=400, mimetype='application/json')

            # Buscar el método de pago válido para el diario
            payment_method_line = request.env['account.payment.method.line'].sudo().search([
                ('payment_method_id.code', '=', 'manual'),
                ('journal_id', '=', journal_id)
            ], limit=1)

            if not payment_method_line:
                response_data = {"error": f"No se encontró un método de pago válido para el diario con ID {journal_id}"}
                return Response(json.dumps(response_data), status=404, mimetype='application/json')

            # Crear el pago
            payment_register = request.env['account.payment.register'].sudo().with_context(
                active_ids=invoice.ids, active_model='account.move').create({
                    'payment_date': payment_date,
                    'journal_id': journal_id,
                    'amount': payment_amount,
                    'currency_id': invoice.currency_id.id,
                    'payment_method_line_id': payment_method_line.id,
                })

            payment_create = payment_register.action_create_payments()

            payment = request.env['account.payment'].sudo().search([('id', '=', payment_create['res_id'])], limit=1)

            response_data = {
                "success": True,
                "message": "Pago creado y asociado correctamente",
                "payment_name": payment.name,
                "payment_id": payment.id,
                "invoice_id": invoice.id,
                "invoice_name": invoice.name,

            }
            return Response(json.dumps(response_data), status=200, mimetype='application/json')

        except Exception as e:
            response_data = {"error": f"Ocurrió un error al procesar el pago: {str(e)}"}
            return Response(json.dumps(response_data), status=500, mimetype='application/json')
