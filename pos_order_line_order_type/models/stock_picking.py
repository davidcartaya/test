from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

from itertools import groupby
from collections import defaultdict

class StockPicking(models.Model):
    _inherit='stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        vals = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        vals['order_type_id'] = first_line.order_type_id.id
        return vals