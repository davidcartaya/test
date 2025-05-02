from odoo import http
from odoo.http import request, Response
import json

class InvoiceController(http.Controller):

    @http.route('/api/get_invoice', type='http', auth='public', methods=['POST'], csrf=False)
    def get_invoice(self, **post):
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return Response(json.dumps({'error': 'Formato de JSON no válido'}), status=400, mimetype='application/json')

        invoice_number = data.get('invoice_number')
        invoice_id = data.get('invoice_id')
        customer_id = data.get('customer_id')
        number_quote = data.get('number_quote')

        if not invoice_number or not customer_id or number_quote < 0 or not invoice_id:
            return Response(json.dumps({'error': 'Datos incompletos'}), status=400, mimetype='application/json')

        invoice = request.env['account.move'].sudo().search([
            ('name', '=', invoice_number),
            ('id', '=', invoice_id),
            ('partner_id', '=', customer_id),
            ('move_type', '=', 'out_invoice'),
            '|',  # Esto se usa para combinar condiciones OR
            ('number_quote', '=', number_quote),  # Esta condición sigue funcionando para los casos donde number_quote no es 0
            ('number_quote', '=', False)  # Esta condición asegura que se consideren las facturas donde number_quote es igual a 0
        ], limit=1)

        if not invoice:
            return Response(json.dumps({'error': 'Factura no encontrada'}), status=404, mimetype='application/json')

        payment_state_translation = {
            'not_paid': 'No pagado',
            'in_payment': 'En proceso de pago',
            'paid': 'Pagado',
            'partial': 'Pagado parcialmente',
            'reversed': 'Revertido',
            'invoicing_legacy': 'Sistema anterior de facturación'
        }

        invoice_data = {
            'invoice_number': invoice.name,
            'invoice_id': invoice.id,
            'customer_id': invoice.partner_id.id,
            'number_quote': invoice.number_quote,
            'payment_state': payment_state_translation.get(invoice.payment_state, 'Desconocido'),
            'amount': invoice.amount_residual,
        }

        return Response(json.dumps(invoice_data), status=200, mimetype='application/json')
