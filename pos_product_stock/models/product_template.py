from odoo import fields, models


class ProductTemplate(models.Model):
    """inherit product.template to add field."""
    _inherit = "product.template"

    deny = fields.Integer(string="Denegar orden POS", default=0,
                          help="Establezca un límite para poder rechazar pedidos POS")
