# coding: utf-8
from odoo import fields, models, api, _
import time
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import io
import base64
import xlsxwriter

class AccountInventoryBookWizard(models.TransientModel):
    _name = "inventory.book.wizard"

    date_start = fields.Date("Fecha de Inicio", required=True, default=time.strftime('%Y-%m-%d'))
    date_end = fields.Date("Fecha Fin", required=True, default=time.strftime('%Y-%m-%d'))
    product_type_filter = fields.Selection([("all", _("Todos los productos")),
            ("category", _("Categoría")),
            ("product", _("Producto")),
        ], "Filtar por", required=True, default='all')

    category_ids = fields.Many2many(comodel_name='product.category', string='Categoría')
    product_ids = fields.Many2many(comodel_name='product.product', string='Producto', domain="[('detailed_type','=','product')]")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Lote')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Almacen')
    
    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        for rec in self:
            if rec.product_type_filter == 'all':
                rec.product_ids = False
                rec.category_ids = False
            elif rec.product_type_filter == 'category':
                rec.product_ids = False
            elif rec.product_type_filter == 'product':
                rec.category_ids = False

    def imprimir_pdf(self):
        for rec in self:
            data = {
                'ids': 0,
                'form': {
                    'date_from': self.date_start,
                    'date_to': self.date_end,
                    'category_ids': self.category_ids.ids if self.category_ids else [],
                    'product_ids': self.product_ids.ids if self.product_ids else [],
                    'company': self.company_id.id,
                    'lot_id': self.lot_id.id or False,  # ← Aquí agregas el filtro de lote
                }
            }
            return self.env.ref('book_inventory.report_inventary_book').report_action(self, data=data)  # , config=False


    def imprimir_xlsx(self):
        self.ensure_one()

        data = {
            'form': {
                'date_from': self.date_start.strftime('%Y-%m-%d'),
                'date_to': self.date_end.strftime('%Y-%m-%d'),
                'category_ids': self.category_ids.ids,
                'product_ids': self.product_ids.ids,
                'company': self.company_id.id,
            }
        }

        # Obtener los datos del mismo método que usa el PDF
        report_data = self.env['report.book_inventory.report_invantary_book_template']._get_report_values(None, data)

        # Crear archivo en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Libro de Inventario")

        # Formatos
        format_title = workbook.add_format({'bold': True, 'font_size': 14})
        format_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        format_cell = workbook.add_format({'border': 1})
        money = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        # Encabezado del reporte en el Excel (basado en el PDF)
        company = self.company_id

        sheet.write('A1', 'Nombre de la Empresa:', format_cell)
        sheet.write('B1', company.name or '')

        sheet.write('A2', 'RIF:', format_cell)
        sheet.write('B2', company.vat or '')  # o usa otro campo si tienes uno personalizado tipo 'rif'

        sheet.write('A3', 'Dirección de la Empresa:', format_cell)
        direccion = f"{company.street or ''} {company.street2 or ''}".strip()
        sheet.write('B3', direccion)

        # Fecha del reporte
        sheet.write('A5', 'LIBRO DE INVENTARIO', format_title)
        sheet.write('A6', f"Desde: {self.date_start.strftime('%d/%m/%Y')}  Hasta: {self.date_end.strftime('%d/%m/%Y')}", format_cell)

        # Encabezados de tabla
        headers = [
            'Código', 'Descripción', 'Exist. Inicial', 'Costo Inicial', 'Total Inicial',
            'Entradas', 'Costo Entradas', 'Total Entradas',
            'Salidas', 'Costo Salidas', 'Total Salidas',
            'Stock Final', 'Costo Final', 'Total Final'
        ]
        for col, header in enumerate(headers):
            sheet.write(7, col, header, format_header)

        # Datos
        for row, producto in enumerate(report_data['datos'], start=8):
            sheet.write(row, 0, producto['default_code'], format_cell)
            sheet.write(row, 1, producto['name'], format_cell)
            sheet.write(row, 2, producto['existencia_inicial'], format_cell)
            sheet.write(row, 3, producto['precio_inicial'], money)
            sheet.write(row, 4, producto['precio_total_inicial'], money)
            sheet.write(row, 5, producto['entradas_mes'], format_cell)
            sheet.write(row, 6, producto['entradas_mes_precio'], money)
            sheet.write(row, 7, producto['entradas_mes_precio_total'], money)
            sheet.write(row, 8, producto['salida_mes'], format_cell)
            sheet.write(row, 9, producto['salida_mes_precio'], money)
            sheet.write(row, 10, producto['salida_mes_precio_total'], money)
            sheet.write(row, 11, producto['final'], format_cell)
            sheet.write(row, 12, producto['final_precio'], money)
            sheet.write(row, 13, producto['final_precio_total'], money)

        workbook.close()
        output.seek(0)

        xlsx_data = output.read()
        output.close()

        # Crear attachment temporal y retornar con acción de descarga
        filename = f"Libro_Inventario_{self.date_start.strftime('%d_%m_%Y')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        download_url = f'/web/content/{attachment.id}?download=true'
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }