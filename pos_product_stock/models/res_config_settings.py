from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add field. """
    _inherit = 'res.config.settings'

    display_stock = fields.Boolean(string="Mostrar Stock",
                                   readonly=False, help="Al habilitarlo puedes "
                                                        "Ver cantidad en Punto de Venta",
                                   default=False, related='pos_config_id.display_stock_setting')
    stock_type = fields.Selection(related='pos_config_id.stock_product',
                                  string="Tipo de stock", readonly=False,
                                  required=True, help="Help you to choose "
                                                      "the quantity you want to visible in pos")
    stock_from = fields.Selection(related='pos_config_id.location_from',
                                  string="Show Stock Of", readonly=False,
                                  required=True, help="can choose the location "
                                                      "where you want to display the stock ")
    stock_location_id = fields.Many2one(related='pos_config_id.pos_stock_location_id',
                                        string="Stock Location", readonly=False,
                                        help="This field helps to hold the location")

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env['pos.config'].search([], limit=1)
        res.update({
            'display_stock': config.display_stock_setting,
            'stock_type': config.stock_product,
            'stock_from': config.location_from,
            'stock_location_id': config.pos_stock_location_id.id,
        })
        return res

    def set_values(self):
        super().set_values()
        config = self.env['pos.config'].search([], limit=1)
        config.write({
            'display_stock_setting': self.display_stock,
            'stock_product': self.stock_type,
            'location_from': self.stock_from,
            'pos_stock_location_id': self.stock_location_id.id,
        })