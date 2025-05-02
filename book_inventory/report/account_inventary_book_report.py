# coding: utf-8
from odoo import fields, models, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT



class AccountInventoryBookReport(models.AbstractModel):
    _name = 'report.book_inventory.report_invantary_book_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        format_new = "%d/%m/%Y"
        date_start = datetime.strptime(data['form']['date_from'], DATE_FORMAT)
        date_end = datetime.strptime(data['form']['date_to'], DATE_FORMAT)
        lot_id = data['form'].get('lot_id')
        # warehouse_id = data['form'].get('warehouse_id')
        warehouse_id = self.env['inventory.book.wizard'].browse(data['context']['active_id']).warehouse_id
        company_id = self.env['res.company'].browse(data['form']['company'])
        datos = []
        dominio_productos = ['|', ('company_id','=',company_id.id), ('company_id','=',False), ('detailed_type','=','product')]

        if data['form']['category_ids']:
            dominio_productos.append(('categ_id','in', data['form']['category_ids']))
        if data['form']['product_ids']:
            dominio_productos.append(('id','in', data['form']['product_ids']))

        productos_ids = self.env['product.product'].search(dominio_productos)
        for p in productos_ids:
            # Saldos iniciales
            dominio_inicial = [
                ('product_id','=', p.id),
                ('create_date','<', data['form']['date_from'])
            ]
            inciales_ids = self.env['stock.valuation.layer'].search(dominio_inicial)
            if lot_id:
                inciales_ids = inciales_ids.filtered(
                    lambda vl: vl.stock_move_id and any(
                        ml.lot_id.id == lot_id and ml.product_id.id == vl.product_id.id
                        for ml in vl.stock_move_id.move_line_ids
                    )
                )
            if warehouse_id:
                inciales_ids = inciales_ids.filtered(
                    lambda vl: vl.warehouse_id and vl.warehouse_id.id == warehouse_id
                )
            existencia_inicial = sum(inciales_ids.mapped('quantity'))
            precio_total_inicial = sum(inciales_ids.mapped('value'))
            precio_inicial = (precio_total_inicial / existencia_inicial) if existencia_inicial else 0

            # Movimientos del período
            dominio_mes = [
                ('product_id','=', p.id),
                ('create_date','>=', data['form']['date_from']),
                ('create_date','<=', data['form']['date_to']),
            ]
            inventario_mes_ids = self.env['stock.valuation.layer'].search(dominio_mes)
            if lot_id:
                inventario_mes_ids = inventario_mes_ids.filtered(
                    lambda vl: vl.stock_move_id and any(
                        ml.lot_id.id == lot_id and ml.product_id.id == vl.product_id.id
                        for ml in vl.stock_move_id.move_line_ids
                    )
                )
            if warehouse_id:
                inventario_mes_ids = inventario_mes_ids.filtered(
                    lambda vl: vl.warehouse_id and vl.warehouse_id.id == warehouse_id
                )
            entradas = inventario_mes_ids.filtered(lambda x: x.quantity > 0)
            salidas = inventario_mes_ids.filtered(lambda x: x.quantity < 0)
            entradas_mes = sum(entradas.mapped('quantity'))
            entradas_mes_precio_total = sum(entradas.mapped('value'))
            salidas_mes = abs(sum(salidas.mapped('quantity')))
            salida_mes_precio_total = abs(sum(salidas.mapped('value')))

            entradas_mes_precio = (entradas_mes_precio_total / entradas_mes) if entradas_mes else 0
            salida_mes_precio = (salida_mes_precio_total / salidas_mes) if salidas_mes else 0

            final = existencia_inicial + entradas_mes - salidas_mes
            final_precio_total = precio_total_inicial + entradas_mes_precio_total - salida_mes_precio_total
            final_precio = (final_precio_total / final) if final else 0

            datos.append({
                'default_code': p.default_code or '',
                'name': p.name,
                'existencia_inicial': existencia_inicial,
                'precio_inicial': precio_inicial,
                'precio_total_inicial': precio_total_inicial,
                'entradas_mes': entradas_mes,
                'entradas_mes_precio': entradas_mes_precio,
                'entradas_mes_precio_total': entradas_mes_precio_total,
                'salida_mes': salidas_mes,
                'salida_mes_precio': salida_mes_precio,
                'salida_mes_precio_total': salida_mes_precio_total,
                'final': final,
                'final_precio': final_precio,
                'final_precio_total': final_precio_total,
            })

        return {
            'company': company_id,
            'currency': company_id.currency_id,
            'date_start': date_start,
            'date_end': date_end,
            'datos': datos,
        }