/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { OrderTypePopup } from "@pos_order_line_order_type/input_popups/deliveryTypePopup";


patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },
    async changeOrderType(orderline) {
        debugger
        console.log('Cambiar tipo de entrega')
        const selectionList = this.pos.pos_custom_order_type.map(orderType => ({
            id: orderType.id,
            label: orderType.name,
            item: orderType,
        }));
        const { confirmed, payload: selectedOrderType } = await this.popup.add(
            OrderTypePopup,
            {
                title: _t("Selecciona el tipo de entrega"),
                list: selectionList,
            }
        );
        if (confirmed) {
            orderline.set_line_order_type(selectedOrderType);
        }
    },
    removeOrderType(orderline) {
        console.log('Borrar tipo de entrega')
        orderline.remove_order_type()
    }
});
