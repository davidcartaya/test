/** @odoo-module **/


import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.order_type_id = this.order_type_id || "";
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        if (json.order_type_id) {
            var orderType = this.get_order_type_by_id(json.order_type_id);
            if (orderType) {
                this.set_line_order_type(orderType);
            }
        }
    },
    get_order_type_by_id (order_type_id) {
        var self = this;
        var orderType = null;
        for (var i = 0; i < self.pos.pos_custom_order_type.length; i++) {
            if (self.pos.pos_custom_order_type[i].id == order_type_id) {
                orderType = self.pos.pos_custom_order_type[i];
            }
        }
        return orderType;
    },
    set_line_order_type (orderType) {
        this.order_type_id = orderType;
    },
    get_line_order_type() {
        debugger
        return this.order_type_id;
    },
    remove_order_type () {
        this.order_type_id = null;
    },
    getLineOrderType() {
        debugger
        if (this.order_type_id && this.order_type_id.id !== undefined) {
            return this.order_type_id;
        }
        return null;
    },
    export_as_JSON() {
        const result = super.export_as_JSON(...arguments);
        if (this.order_type_id){
            result.order_type_id = this.order_type_id.id;
        }
        return result;
    },
});
