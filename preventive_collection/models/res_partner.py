from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    phone_number = fields.Char(string='Numero de telefono')