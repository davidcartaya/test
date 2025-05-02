from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

       
        commission_model = self.env['sale.commission']
        total_commission_amt = 0.0
        commission_lines = []
        employee_totals = {}

        for line in self.order_line:
            rules = []
            origin_obj = None
            amount = 0.0

            # 1. Producto
            if line.product_id and line.product_id.commission_assignment == 'sale_order':
                rules = line.product_id.commission_ids
                origin_obj = line.product_id
                amount = origin_obj.amount_comission

            # 2. Categoría
            elif line.product_id.categ_id and line.product_id.categ_id.commission_assignment == 'sale_order':
                rules = line.product_id.categ_id.commission_ids
                origin_obj = line.product_id.categ_id
                amount = origin_obj.amount_comission

            # 3. Partner
            elif self.partner_id and self.partner_id.commission_assignment == 'sale_order':
                rules = self.partner_id.commission_ids
                origin_obj = self.partner_id
                amount = origin_obj.amount_comission

            if not origin_obj:
                continue

            amount
            ctype = origin_obj.commission_type


            if ctype == 'per':
                line_commission = line.price_subtotal * (amount / 100.0)
            else:
                line_commission = amount

            total_commission_amt += line_commission

            commission_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'amount': line_commission,
            }))

            for rule in rules:
                if not rule.employee_id:
                    continue
                
                if line_commission <= 0:
                    amount_commission_emp = 0.0
                elif rule.commission_type == 'per':
                    amount_commission_emp = line_commission * (rule.amount / 100.0)
                elif rule.commission_type == 'fixed':
                    amount_commission_emp = rule.amount
                else:
                    amount_commission_emp = 0.0

                employee_id = rule.employee_id.id
                if employee_id in employee_totals:
                    employee_totals[employee_id] += amount_commission_emp
                else:
                    employee_totals[employee_id] = amount_commission_emp

        if commission_lines:
            seq_name = self.env['ir.sequence'].next_by_code('sale.commission') or '/'
            commission_model.create({
                'name': seq_name,
                'employee_ids': [(6, 0, list(employee_totals.keys()))],
                'start_date': fields.Date.today(),
                'commission_line_ids': commission_lines,
                'total_commission_amt': total_commission_amt,
                'employee_commission_ids': [
                    (0, 0, {
                        'employee_id': emp_id,
                        'amount': amount_emp,
                    }) for emp_id, amount_emp in employee_totals.items()
                ]
            })

        return res


