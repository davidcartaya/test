from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    number_quote = fields.Integer('Numero de cuota')
    is_quote = fields.Boolean('Es una cuota?', default=False)

   
