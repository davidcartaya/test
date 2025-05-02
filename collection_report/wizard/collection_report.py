from odoo import models, fields, api, _
from datetime import timedelta
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import UserError

class ReportCollectionWizard(models.TransientModel):
    _name = "report.collection.wizard"
    _description = "Wizard de Reportes de Cobranzas"

    report_type = fields.Selection(
        [
            ("vencidos", "Reporte de Vencidos por Cobrar Detallado"),
            ("morosidad", "Reporte de Morosidad por Tipo de Contrato"),
        ],
        string="Tipo de Reporte",
        default='', 
    )
    xlsx_file = fields.Binary(string='Archivo CSV en Base64')
    xlsx_file_name = fields.Char(string='Nombre del archivo CSV')

    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha de Fin")
    partner_id = fields.Many2many("res.partner", string="Cliente")
    contract_type_id = fields.Many2many("type.contract", string="Tipo de Contrato")

    file_format = fields.Selection(
        [("pdf", "PDF"), ("xls", "Excel")], string="Formato",
        default=''
    )
        
    @api.onchange('report_type')
    def _onchange_report_type(self):
        """Actualizar campos basados en el tipo de reporte seleccionado"""
        if self.report_type == "morosidad":
            self.partner_id = False
        elif self.report_type != "morosidad":
            self.contract_type_id = False


    def generate_report(self):
        report_type = self.report_type
        file_format = self.file_format

        if not report_type or not file_format:
            raise UserError('Por favor, seleccione el tipo de reporte y el formato del archivo.')

        if report_type == "vencidos":
            return self._generate_vencidos_report(file_format)
        elif report_type == "morosidad":
            return self._generate_morosidad_report(file_format)
        

    def _generate_vencidos_report(self, file_format):
        # Construcción del dominio para filtrar órdenes de venta
        domain = [("invoice_ids", "!=", False)]

        # Filtro por fechas
        if self.start_date:
            domain.append(("date_order", ">=", self.start_date))
        if self.end_date:
            domain.append(("date_order", "<=", self.end_date))

        # Filtro por clientes (Many2many)
        if self.partner_id:
            domain.append(("partner_id", "in", self.partner_id.ids))

        # Búsqueda de órdenes de venta ordenadas por cliente y fecha
        sale_orders = self.env["sale.order"].search(domain, order="partner_id asc, date_order desc")

        # Agrupación de las órdenes por cliente
        grouped_orders = {}
        for order in sale_orders:
            partner_name = order.partner_id.name
            if partner_name not in grouped_orders:
                grouped_orders[partner_name] = []
            grouped_orders[partner_name].append(order)

        # Procesar los datos agrupados para el reporte
        report_data = []
        for partner_name, orders in grouped_orders.items():
            for sale_order in orders:
                paid_quotes = 0
                overdue_quotes = 0
                upcoming_quotes = 0
                total_collected = 0
                total_due_overdue = 0
                total_due = 0
                payment_dates = []

                total_invoiced = sum(
                    invoice.amount_total for invoice in sale_order.invoice_ids
                )
                total_paid = sum(
                    (invoice.amount_total - invoice.amount_residual) for invoice in sale_order.invoice_ids
                )

                if total_paid == total_invoiced:
                    status_order = "Totalmente Pagada"
                elif total_paid > 0:
                    status_order = "Parcialmente Pagada"
                else:
                    status_order = "No Pagada"

                days_between_payments = (
                    sale_order.payment_term_id.line_ids[0].days
                    if sale_order.payment_term_id.line_ids
                    else 30
                )

                if (
                    len(sale_order.invoice_ids) == 1
                    and not sale_order.invoice_ids[0].is_quote
                ):
                    invoice = sale_order.invoice_ids[0]

                    if (
                        sale_order.payment_term_id
                        and invoice.invoice_date
                        and invoice.invoice_date_due
                    ):
                        invoice_date = fields.Date.from_string(invoice.invoice_date)
                        invoice_due_date = fields.Date.from_string(invoice.invoice_date_due)

                        current_date = invoice_date + timedelta(days=days_between_payments)
                        while current_date <= invoice_due_date:
                            payment_dates.append(current_date.strftime("%Y-%m-%d"))

                            payments = (
                                self.env["account.payment"]
                                .sudo()
                                .search(
                                    [
                                        ("reconciled_invoice_ids", "in", [invoice.id]),
                                        ("date", "=", current_date.strftime("%Y-%m-%d")),
                                        ("amount", "<=", sale_order.amount_total),
                                    ],
                                    limit=1,
                                )
                            )

                            if payments:
                                for pay in payments:
                                    total_collected += pay.amount
                                paid_quotes += 1

                            elif not payments and current_date < fields.Date.today():
                                overdue_quotes += 1

                            elif (
                                current_date >= fields.Date.today()
                                and current_date <= invoice_due_date
                            ):
                                upcoming_quotes += 1

                            next_date = current_date + timedelta(days=days_between_payments)
                            if next_date > invoice_due_date:
                                break
                            current_date = next_date

                        total_due_overdue += invoice.amount_residual
                        total_due += invoice.amount_residual
                        quote_amount = sale_order.x_studio_monto_cuota if sale_order.x_studio_monto_cuota > 0 else 0
                else:
                    quote_amount = sale_order.invoice_ids[0].amount_total if sale_order.invoice_ids else 0
                    for invoice in sale_order.invoice_ids:
                        if invoice.payment_state in ["paid", "in_payment"]:
                            paid_quotes += 1
                            total_collected += invoice.amount_total
                        elif (
                            invoice.invoice_date_due < fields.Date.today()
                            and invoice.payment_state not in ["paid", "in_payment", "cancel"]
                        ):
                            overdue_quotes += 1
                            total_due_overdue += invoice.amount_residual
                        elif invoice.invoice_date_due >= fields.Date.today():
                            upcoming_quotes += 1

                        total_due += invoice.amount_residual

                report_data.append(
                    {
                        "partner_name": partner_name,
                        "order_name": sale_order.name,
                        "identification_id": sale_order.partner_id.identification_id,
                        "state": status_order,
                        "paid_quotes": paid_quotes,
                        "overdue_quotes": overdue_quotes,
                        "upcoming_quotes": upcoming_quotes,
                        "payment_period": days_between_payments,
                        "total_collected": round(total_collected, 2),
                        "total_due_overdue": round(total_due_overdue, 2),
                        "total_due": round(total_due, 2),
                        "quote_amount": quote_amount,
                    }
                )

        # Generar reporte según el formato solicitado
        if file_format == "pdf":
            return self.env.ref("collection_report.report_vencidos_pdf").report_action(
                self, data={"report_data": report_data}
            )
        elif file_format == "xls":
            return self._generate_xls_report_vencidos(report_data)

    def _generate_xls_report_vencidos(self, report_data):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Vencidos por Cobrar')

        headers = [
            'Nombre Cliente', 'Identificación', 'Estado', 'Facturas Pagadas',
            'Facturas Vencidas', 'Facturas Próximas a Vencer', 'Periodo de Pago',
            'Total Cobrado', 'Total Adeudado Vencido', 'Total Adeudado'
        ]
        worksheet.write_row('A1', headers)

        row = 1  # Empezamos en la segunda fila
        for data in report_data:
            worksheet.write(row, 0, data['partner_name'])
            worksheet.write(row, 1, data['identification_id'])
            worksheet.write(row, 2, data['state'])
            worksheet.write(row, 3, data['paid_quotes'])
            worksheet.write(row, 4, data['overdue_quotes'])
            worksheet.write(row, 5, data['upcoming_quotes'])
            worksheet.write(row, 6, data['payment_period'])
            worksheet.write(row, 7, data['total_collected'])
            worksheet.write(row, 8, data['total_due_overdue'])
            worksheet.write(row, 9, data['total_due'])
            row += 1

        # Cerrar el archivo Excel
        workbook.close()

        # Preparar el archivo para la descarga
        output.seek(0)
        file_data = output.read()

        # Codificar en base64
        file_data_encoded = base64.b64encode(file_data)

        # Guardar el archivo en Odoo (esto es opcional si lo deseas)
        self.xlsx_file = file_data_encoded
        self.xlsx_file_name = 'Vencidos por Cobrar.xlsx'

        # Retornar el archivo como una respuesta para descarga
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&id=%s&field=xlsx_file&download=true&filename=%s' % (
                self._name, self.id, self.xlsx_file_name),
            'target': 'self',
        }


    def _generate_morosidad_report(self, file_format):
        type_contract_id = self.contract_type_id.id
        start_date = self.start_date
        end_date = self.end_date
        partner_id = self.partner_id.id

        domain = [("state", "in", ['sale', 'done'])]
        if start_date:
            domain.append(("date_order", ">=", start_date))
        if end_date:
            domain.append(("date_order", "<=", end_date))
        if partner_id:
            domain.append(("partner_id", "=", partner_id))

        if not type_contract_id:
            domain.append(("type_contract_id", "!=", False))

        if type_contract_id:
            domain.append(("type_contract_id", "=", type_contract_id))

        # Buscar las órdenes de venta según el dominio filtrado
        sale_orders = self.env["sale.order"].search(domain)

        # Inicialización de variables para almacenar datos de contratos y morosidad
        global_totals = {}
        report_data = {}
        active_contracts = {}  # Diccionario para contar contratos activos por tipo
        overdue_contracts = {}  # Diccionario para contar contratos morosos por tipo
        overdue_ranges = {  # Diccionario para contar cuotas vencidas por rango de días
            '1_30_days': 0,
            '31_60_days': 0,
            '61_90_days': 0,
            '91_120_days': 0,
        }
        total_due_per_contract_type = {}  # Diccionario para almacenar la cantidad adeudada por tipo de contrato

        # Iterar sobre las órdenes de venta
        for order in sale_orders:
            contract_type = order.type_contract_id.name

            # Verificar si el contrato está activo: Si la venta no está cancelada y tiene facturas no pagadas
            is_active = False
            invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            total_invoiced = sum(invoices.mapped('amount_total'))
            total_residual = sum(invoices.mapped('amount_residual'))

            # Si tiene facturas no pagadas, se considera activo
            if total_residual > 0:
                is_active = True

            # Calcular si el contrato está moroso (total_invoiced - total_residual)
            is_overdue = False
            for invoice in invoices:
                if invoice.invoice_date_due < fields.Date.today() and invoice.amount_residual > 0:  # Verificar que la factura no esté pagada
                    # Calcular los días vencidos de la factura
                    days_overdue = abs((fields.Date.today() - invoice.invoice_date_due).days)
                    
                    if days_overdue > 0:  # Solo considerar las facturas vencidas
                        # Clasificar la factura según su antigüedad
                        if 1 <= days_overdue <= 30:
                            overdue_ranges['1_30_days'] += 1
                        elif 31 <= days_overdue <= 60:
                            overdue_ranges['31_60_days'] += 1
                        elif 61 <= days_overdue <= 90:
                            overdue_ranges['61_90_days'] += 1
                        elif 91 <= days_overdue <= 120:
                            overdue_ranges['91_120_days'] += 1

            # Para determinar si el contrato es moroso, se usa total_invoiced - total_residual
            if total_invoiced - total_residual < total_invoiced:
                is_overdue = True

            # Contar los contratos activos y morosos por tipo de contrato
            if contract_type:
                if contract_type not in active_contracts:
                    active_contracts[contract_type] = 0
                    overdue_contracts[contract_type] = 0
                    total_due_per_contract_type[contract_type] = 0  # Inicializar la cantidad adeudada por tipo

                # Solo contar el contrato como activo si tiene facturas no pagadas
                if is_active:
                    active_contracts[contract_type] += 1

                if is_overdue:
                    overdue_contracts[contract_type] += 1

                # Sumar el monto residual de las facturas al total adeudado por el tipo de contrato
                total_due_per_contract_type[contract_type] += total_residual

        total_global_active_contracts = 0
        total_global_overdue_contracts = 0
        total_global_overdue_1_30_days = 0
        total_global_overdue_31_60_days = 0
        total_global_overdue_61_90_days = 0
        total_global_overdue_91_120_days = 0
        total_global_due = 0

        # Crear el reporte agrupado por tipo de contrato y rangos de días
        for contract_type in active_contracts:
            active_count = active_contracts[contract_type]
            overdue_count = overdue_contracts.get(contract_type, 0)

            if overdue_count > 0:
                overdue_percentage = (active_count / overdue_count) * 100
            else:
                overdue_percentage = 0 

            report_data[contract_type] = {
                'active_contracts': active_contracts[contract_type],
                'morosity_percentage': overdue_percentage,
                'overdue_contracts': overdue_contracts.get(contract_type, 0),
                'overdue_1_30_days': overdue_ranges['1_30_days'],
                'overdue_31_60_days': overdue_ranges['31_60_days'],
                'overdue_61_90_days': overdue_ranges['61_90_days'],
                'overdue_91_120_days': overdue_ranges['91_120_days'],
                'total_due': total_due_per_contract_type[contract_type],
            }

            total_global_active_contracts += active_count
            total_global_overdue_contracts += overdue_count
            total_global_overdue_1_30_days += overdue_ranges['1_30_days']
            total_global_overdue_31_60_days += overdue_ranges['31_60_days']
            total_global_overdue_61_90_days += overdue_ranges['61_90_days']
            total_global_overdue_91_120_days += overdue_ranges['91_120_days']
            total_global_due += total_due_per_contract_type[contract_type]

        global_totals = {
            'active_contracts': total_global_active_contracts,
            'overdue_contracts': total_global_overdue_contracts,
            'overdue_1_30_days': total_global_overdue_1_30_days,
            'overdue_31_60_days': total_global_overdue_31_60_days,
            'overdue_61_90_days': total_global_overdue_61_90_days,
            'overdue_91_120_days': total_global_overdue_91_120_days,
            'total_due': total_global_due,
        }

        if file_format == "pdf":
            return self.env.ref("collection_report.report_morosidad_pdf").report_action(
                self, data={"report_data": report_data, "global_totals": global_totals}
            )

        if file_format == "xls":
            return self._generate_xls_report_morosidad(report_data, global_totals) 
        
    def _generate_xls_report_morosidad(self, report_data, global_totals):
        # Crear un archivo Excel en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Morosidad por Tipo de Contrato')

        # Agregar los encabezados
        headers = [
            'Tipo de Contrato', 'Contratos Activos', 'Clientes Morosos',
            'Cuotas Vencidas 1-30 días', 'Cuotas Vencidas 31-60 días', 
            'Cuotas Vencidas 61-90 días', 'Cuotas Vencidas 91-120 días', 
            'Total Adeudado', 'Porcentaje de Morosidad'
        ]
        worksheet.write_row('A1', headers)

        # Agregar los datos del reporte
        row = 1  # Empezamos en la segunda fila
        for contract_type, data in report_data.items():
            worksheet.write(row, 0, contract_type)
            worksheet.write(row, 1, data['active_contracts'])
            worksheet.write(row, 2, data['overdue_contracts'])
            worksheet.write(row, 3, data['overdue_1_30_days'])
            worksheet.write(row, 4, data['overdue_31_60_days'])
            worksheet.write(row, 5, data['overdue_61_90_days'])
            worksheet.write(row, 6, data['overdue_91_120_days'])
            worksheet.write(row, 7, data['total_due'])
            worksheet.write(row, 8, data['morosity_percentage'])
            row += 1


        worksheet.write(row, 0, 'Totales')  # Primera columna: Total Global
        worksheet.write(row, 1, global_totals.get('active_contracts', 0))  # Contratos Activos
        worksheet.write(row, 2, global_totals.get('overdue_contracts', 0))  # Clientes Morosos
        worksheet.write(row, 3, global_totals.get('overdue_1_30_days', 0))  # Cuotas Vencidas 1-30 días
        worksheet.write(row, 4, global_totals.get('overdue_31_60_days', 0))  # Cuotas Vencidas 31-60 días
        worksheet.write(row, 5, global_totals.get('overdue_61_90_days', 0))  # Cuotas Vencidas 61-90 días
        worksheet.write(row, 6, global_totals.get('overdue_91_120_days', 0))  # Cuotas Vencidas 91-120 días
        worksheet.write(row, 7, global_totals.get('total_due', 0))  # Total Adeudado
        worksheet.write(row, 8, '')  # Dejar vacío o agregar algo si se desea el porcentaje global
        row += 1
        # Cerrar el archivo Excel
        workbook.close()

        # Preparar el archivo para la descarga
        output.seek(0)
        file_data = output.read()
        file_data_encoded = base64.b64encode(file_data)

        # Guardar el archivo en Odoo (esto es opcional si quieres almacenar el archivo en el modelo)
        self.xlsx_file = file_data_encoded
        self.xlsx_file_name = 'Reporte Morosidad.xlsx'
        # Retornar el archivo como una respuesta para descarga
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&id=%s&field=xlsx_file&download=true&filename=%s' % (
                self._name, self.id, self.xlsx_file_name),
            'target': 'self',
        }
                
