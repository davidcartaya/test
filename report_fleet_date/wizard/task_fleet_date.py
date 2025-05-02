from odoo import models, fields, api
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
from io import BytesIO

class TaskFleetDateWizard(models.TransientModel):
    _name = 'task.fleet.date.wizard'
    _description = 'Wizard to filter tasks by vehicles and date range'

    # Campo Many2many para seleccionar vehículos
    fleet_ids = fields.Many2many('fleet.vehicle', string='Vehículos')

    # Campos para el rango de fechas
    date_start = fields.Date(string='Fecha de inicio', required=True)
    date_end = fields.Date(string='Fecha de fin', required=True)
    format_type = fields.Selection([('xlsx', 'Excel'), ('pdf', 'PDF')], string='Tipo de formato', default="xlsx")
    xlsx_file = fields.Binary(string='Archivo en Base64')
    xlsx_file_name = fields.Char(string='Nombre del archivo')

    def _generate_excel_file(self, sheet_name, fleet_data, date_range):
        """
        Genera un archivo Excel con los datos proporcionados.
        :param sheet_name: Nombre de la hoja del Excel.
        :param fleet_data: Lista de datos organizados por flota.
        :param date_range: Rango de fechas para las columnas.
        :return: (file_data_encoded, file_name)
        """
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(sheet_name)

        # Encabezados dinámicos
        headers = ['Equipos/Materiales', 'Matricula', 'Categoría', 'Clasificación'] + date_range
        worksheet.write_row(0, 0, headers)

        # Agregar los datos
        row = 1
        for fleet in fleet_data:
            worksheet.write(row, 0, fleet['model_id'])  # Nombre de la flota
            worksheet.write(row, 1, fleet['license_plate']) # Matricula
            worksheet.write(row, 2, fleet['category_id'])  # Categoría
            worksheet.write(row, 3, fleet['vehicle_classification'])  # Clasificación
            for col, date in enumerate(date_range, start=1):
                worksheet.write(row, col, fleet['dates'].get(date, ''))  # Datos por fecha
            row += 1

        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 20)  # Columna de nombres
        worksheet.set_column(1, len(date_range), 15)  # Columnas de fechas

        # Cerrar y preparar archivo para descarga
        workbook.close()
        output.seek(0)
        file_data = output.read()
        file_data_encoded = base64.b64encode(file_data)
        file_name = f'{sheet_name}.xlsx'

        return file_data_encoded, file_name

    def action_search_tasks(self):

        tasks = self.env['project.task'].search([
            ('fleet_ids', 'in', self.fleet_ids.ids),
            ('date_deadline', '>=', self.date_start),
            ('date_deadline', '<=', self.date_end),
        ])

        if not tasks:
            raise UserError("No se encontraron datos para las flotas seleccionadas en el rango de fechas especificado.")
        
        date_range = [
            (self.date_start + timedelta(days=i)).strftime('%d-%m-%Y')
            for i in range((self.date_end - self.date_start).days + 1)
        ]

        fleet_data = []
        for vehicle in self.fleet_ids:
            vehicle_data = {'model_id': vehicle.model_id.display_name,
                            'license_plate': vehicle.license_plate,
                            'category_id': vehicle.category_id.name,
                            'vehicle_classification': vehicle.x_studio_clasificacion_vehiculo,
                            'dates': {}}
            for date in date_range:
                vehicle_data['dates'][date] = ''  

            for task in tasks.filtered(lambda t: vehicle in t.fleet_ids):
                date_key = task.date_deadline.strftime('%d-%m-%Y')
                if date_key in vehicle_data['dates']:
                    vehicle_data['dates'][date_key] = task.x_studio_related_field_4bb_1ietij21n 
            fleet_data.append(vehicle_data)

        context = {
            'fleet_data': fleet_data,
            'date_range': date_range,
        }

        if self.format_type == 'xlsx':
            file_data_encoded, file_name = self._generate_excel_file('Reporte de Flotas', fleet_data, date_range)
            self.xlsx_file = file_data_encoded
            self.xlsx_file_name = file_name

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content?model=%s&id=%s&field=xlsx_file&download=true&filename=%s' % (
                    self._name, self.id, self.xlsx_file_name),
                'target': 'self',
            }
        else:
            # Llamar al reporte y pasarle el contexto con las flotas y fechas
            return self.env.ref('report_fleet_date.action_report_task_fleet_date_pdf').report_action(self, data=context)




        
        
