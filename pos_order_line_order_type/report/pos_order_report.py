# -*- coding: utf-8 -*-
from odoo import models, fields


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    order_type_id = fields.Many2one('por.order.type', string='Tipo de Pedido')

    def _select(self):
        return super(PosOrderReport, self)._select() + ',l.order_type_id AS order_type_id'

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ',l.order_type_id'
