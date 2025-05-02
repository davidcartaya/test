odoo.define('pos_product_stock.Custom', function(require) {
    'use strict';
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const order = (ProductScreen) => class extends ProductScreen {
        //we extends ProductScreen to super _clickproduct function.
        async _clickProduct(event) {
            if (event.detail.detailed_type == 'product') {
                if (this.env.pos.config['location_from'] == 'all_warehouse') {
                    if (this.env.pos.config['stock_product'] == 'on_hand') {
                        if (event.detail.qty_available <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            }); //shows error pop up as condition satisfies.
                        } else {
                            
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'outgoing_qty') {
                        if (event.detail.outgoing_qty <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'incoming_qty') {
                        if (event.detail.incoming_qty <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'available_qty') {
                        if (event.detail.available_product <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    }
                } else if (this.env.pos.config['location_from'] == 'current_warehouse') {
                    if (this.env.pos.config['stock_product'] == 'on_hand') {
                        if (event.detail.on_hand <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'outgoing_qty') {
                        if (event.detail.outgoing <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'incoming_qty') {
                        if (event.detail.incoming <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.config['stock_product'] == 'available_qty') {
                        if (event.detail.available <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            event.detail.virtual_stock -= 1
                            super._clickProduct(event);
                        }
                    }
                }
            } else {
                super._clickProduct(event);
            }
        }

        _setValue(val) {
            
            const selectedOrderline = this.currentOrder.get_selected_orderline();
            if (selectedOrderline) {
                let product = selectedOrderline.product;
                let currentQuantity = selectedOrderline.get_quantity();
        
                if (this.env.pos.numpadMode === 'quantity') {
                    const result = selectedOrderline.set_quantity(val);
                    if (!result) NumberBuffer.reset();
        
                    // Restaurar la cantidad en stock si se elimina la línea o se reduce la cantidad
                    const parsedVal = parseFloat(val) || 0;
                    if (parsedVal < currentQuantity) {
                        let quantityRestored = currentQuantity - parsedVal;

                        if (this.env.pos.config['stock_product'] == 'on_hand') {
                            product.virtual_stock += quantityRestored;

                        }  else if (this.env.pos.config['stock_product'] == 'outgoing_qty') {
                            product.virtual_stock += quantityRestored;

                        } else if (this.env.pos.config['stock_product'] == 'incoming_qty') {
                            product.virtual_stock += quantityRestored;
                            
                        } else if (this.env.pos.config['stock_product'] == 'available_qty') {
                            product.virtual_stock += quantityRestored;
                        }
                        
                        this.render();
                    }
                } else if (this.env.pos.numpadMode === 'discount') {
                    selectedOrderline.set_discount(val);
                } else if (this.env.pos.numpadMode === 'price') {
                    selectedOrderline.price_manually_set = true;
                    selectedOrderline.set_unit_price(val);
                }
            }
        }
    }
    Registries.Component.extend(ProductScreen, order);
});
