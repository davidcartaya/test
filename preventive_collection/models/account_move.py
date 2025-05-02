import csv
import base64
from io import StringIO
from odoo import models, fields
from odoo.exceptions import UserError
import paramiko
import os
from datetime import timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    partial_csv_file = fields.Binary('Partial Payments CSV')
    partial_csv_file_name = fields.Char('CSV File Name')

    def _calculate_payment_schedule(self, invoice):
        """
        Calcula las fechas de pago programadas para una factura y devuelve la próxima fecha de pago junto con days_overdue.
        """
        payment_dates = []
        next_payment_date = None
        days_between_payments = invoice.invoice_payment_term_id.line_ids[0].days if invoice.invoice_payment_term_id.line_ids else 30

        invoice_date = fields.Date.from_string(invoice.invoice_date)
        invoice_due_date = fields.Date.from_string(invoice.invoice_date_due)
        current_date = invoice_date 

        while current_date <= invoice_due_date:
            payment_dates.append(current_date)

            # Si encontramos una fecha mayor a la fecha actual, la consideramos como próxima fecha de pago
            if not next_payment_date and current_date > fields.Date.today():
                next_payment_date = current_date

            current_date += timedelta(days=days_between_payments)

        days_overdue = (next_payment_date - fields.Date.today()).days if next_payment_date else 'Vencida'

        return days_overdue
           

    def _get_last_payment_date(self, invoice_id):
        """ 
        Función para obtener la última fecha de pago de una factura.
        """
        payment = self.env['account.payment'].search(
            [('reconciled_invoice_ids', 'in', [invoice_id])], order='date desc', limit=1
        )
        return payment.date if payment else 'Sin pago'

    def generate_prevention_csv(self):
        invoices = self.search([
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('invoice_origin', '!=', False),
            ('invoice_date', '<=', fields.Date.today()),
            ('type_contract_id.name', '=', 'Cartera Regular')  # Filtra por el nombre del contrato
        ])
        
        if not invoices:
            raise UserError('No se encontraron facturas.')

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        writer.writerow(['customer_id', 'customer_name', 'phone_number', 'email', 'invoice_id', 'invoice_number', 'number_quote', 'debt_amount', 'due_date', 'days_payment_term', 'payment_status', 'last_payment_date', 'days_overdue'])

        for invoice in invoices:
            today = fields.Date.today()
            days_overdue = ''
            days_term = 7
            if invoice.payment_state == 'partial':
                last_payment_date = self._get_last_payment_date(invoice.id)
            else:
                last_payment_date = 'Sin pago'
                        
            if invoice.invoice_payment_term_id and invoice.invoice_payment_term_id.line_ids:
                if invoice.invoice_payment_term_id.name == 'Pago inmediato' or invoice.invoice_payment_term_id.name == 'Immediate Payment':
                    days_term = 7
                else:
                    days_term = invoice.invoice_payment_term_id.line_ids[0].days
            else:
                sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
                if sale_order and sale_order.payment_term_id and sale_order.payment_term_id.line_ids:
                    if sale_order.payment_term_id.name == 'Pago inmediato' or sale_order.payment_term_id.name == 'Immediate Payment':
                        days_term = 7
                    else:
                        days_term = sale_order.payment_term_id.line_ids[0].days

            if not invoice.is_quote:
                days_overdue = self._calculate_payment_schedule(invoice)
            else:
                if invoice.invoice_date_due:
                    if invoice.invoice_date_due < today:
                        days_overdue = "Vencida"
                    elif invoice.invoice_date_due == today:
                        days_overdue = "Vence hoy"
                    else:
                        days_overdue = (invoice.invoice_date_due - today).days
                else:
                    days_overdue = "Sin fecha de vencimiento"
            
            # Si se obtiene una fecha de pago, formatearla
            if last_payment_date != 'Sin pago':
                last_payment_date = last_payment_date.strftime('%d-%m-%Y')
            
            
                    
            PAYMENT_STATE_SELECTION = {
                'not_paid': 'No pagado',
                'in_payment': 'En proceso de pago',
                'paid': 'Pagada',
                'partial': 'Pagado parcialmente',
                'reversed': 'Revertido',
                'invoicing_legacy': 'Sistema anterior de facturacion',
            }
            writer.writerow([
                invoice.partner_id.id,
                invoice.partner_id.name,
                invoice.partner_id.phone_number or '',
                invoice.partner_id.email or '',
                invoice.id,
                invoice.name,
                invoice.number_quote,
                invoice.amount_total,
                invoice.invoice_date_due.strftime('%d-%m-%Y') if invoice.invoice_date_due else '',
                days_term,
                PAYMENT_STATE_SELECTION.get(invoice.payment_state, ''),
                last_payment_date,
                days_overdue
            ])

        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        # Guardar el archivo en Odoo y configurarlo para la descarga
        self.partial_csv_file = base64.b64encode(csv_content.encode('utf-8'))
        self.partial_csv_file_name = 'Cobranza preventiva.csv'

        # # Enviar el archivo a un servidor SFTP
        sftp_host = "digitaldoc.danaconnect.com"
        sftp_port = 22
        sftp_username = "glik-dana"
        # remote_path = "/glik-dana/Report/Cobranza_preventiva.csv"
        remote_path = "/glik-dana/contactsfile/11126/Cobranza_preventiva.csv"
        private_key_path = os.path.join(os.path.dirname(__file__), 'id_rsa')
      
       
        try:
            key = paramiko.RSAKey.from_private_key_file(private_key_path)
            transport = paramiko.Transport((sftp_host, sftp_port))
            transport.connect(username=sftp_username, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Escribir el archivo CSV en el servidor
            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(csv_content) 

            sftp.close()
            transport.close()
        except Exception as e:
            raise UserError(f"Error al enviar el archivo al servidor SFTP: {str(e)}")

    def action_generate_csv(self):
        self.generate_prevention_csv()

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&id=%s&field=partial_csv_file&download=true&filename=%s' % (
                self._name, self.id, self.partial_csv_file_name),
            'target': 'self',
        }