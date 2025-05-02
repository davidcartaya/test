# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    order_type_id = fields.Many2one(comodel_name='pos.order.type', string='Tipo de Pedido')

    def _export_for_ui(self, orderline):
        result = super(PosOrderLine, self)._export_for_ui(orderline)
        result['order_type_id'] = orderline.order_type_id.id
        print('RE:::::::::::::::::', result)
        return result


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _get_fields_for_order_line(self):
        fields = super(PosOrder, self)._get_fields_for_order_line()
        fields.extend([
            'order_type_id',
        ])
        return fields
