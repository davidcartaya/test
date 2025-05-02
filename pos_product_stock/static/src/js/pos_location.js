odoo.define('Pos_product_stock.update', function(require) {
    'use strict';

    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');

    const Update = (ProductItem) => class extends ProductItem {
        setup() {
            super.setup(...arguments);
        }

        get value() {
            if (this.env.pos.config.display_stock_setting === true) {
                const current_product = this.props.product.id;
                const product = this.props.product;
        
                const stock_product = this.env.pos.stock_quant;
                const move_line = this.env.pos.move_line;
        
                let on_hand = 0;
                let outgoing = 0;
                let incoming = 0;
                let selected_qty = 0;
        
                // Sumar stock de quant
                stock_product.forEach((sp) => {
                    if (sp.product_id[0] === current_product) {
                        on_hand += sp.quantity;
                    }
                });
        
                // Sumar movimientos
                move_line.forEach((line) => {
                    if (line.product_id[0] === current_product) {
                        if (
                            this.env.pos.config.stock_location_id &&
                            this.env.pos.config.stock_location_id[1] === line.location_dest_id[1]
                        ) {
                            incoming += line.qty_done;
                        } else if (
                            this.env.pos.config.stock_location_id &&
                            this.env.pos.config.stock_location_id[1] === line.location_id[1]
                        ) {
                            outgoing += line.qty_done;
                        }
                    }
                });
        
                // 🟡 Nuevo: calcular cuántas unidades ya están seleccionadas en el pedido actual
                const current_order = this.env.pos.get_order();
                if (current_order) {
                    const lines = current_order.get_orderlines();
                    for (let line of lines) {
                        if (line.product && line.product.id === current_product) {
                            selected_qty += line.quantity;
                        }
                    }
                }
        
                // Calcular el stock virtual según la config y RESTAR lo ya seleccionado
                if (!product._virtual_stock_initialized || this.env.pos.reset_virtual_stock) {
                    if (this.env.pos.config.stock_product === 'available_qty') {
                        product.virtual_stock = product.qty_available - selected_qty;
                    } else if (this.env.pos.config.stock_product === 'on_hand') {
                        product.virtual_stock = product.qty_available - outgoing - selected_qty;
                    } else if (this.env.pos.config.stock_product === 'incoming_qty') {
                        product.virtual_stock = incoming - selected_qty;
                    } else if (this.env.pos.config.stock_product === 'outgoing_qty') {
                        product.virtual_stock = outgoing - selected_qty;
                    }
        
                    product._virtual_stock_initialized = true;
                    this.env.pos.reset_virtual_stock = false;
                }
        
                return {
                    display_stock_setting: true,
                };
            } else {
                return {
                    display_stock_setting: false,
                };
            }
        }
    };

    Registries.Component.extend(ProductItem, Update);

    return ProductItem;
});
