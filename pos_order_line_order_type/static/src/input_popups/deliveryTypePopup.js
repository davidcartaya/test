/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class OrderTypePopup extends AbstractAwaitablePopup {
    static template = "pos_order_line_order_type.OrderTypePopup";
    static defaultProps = {
        cancelText: _t("Discard"),
        confirmText: _t("Add"),
        title: _t("Select"),
        body: "",
        list: [],
        confirmKey: false,
    };
    setup() {
        super.setup();
        this.state = useState({ selectedId: this.props.list.find((item) => item.isSelected) });
    }
    async onChangeOrderType(dt_name) {
        const selected_dt = this.props.list.find((item) => item.label === dt_name);
        if (selected_dt) {
            this.selectedDt = selected_dt;
        }
    }
    selectItem(itemId) {
        this.state.selectedId = itemId;
        this.confirm();
    }
    /**
     * We send as payload of the response the selected item.
     *
     * @override
     */
    getPayload() {
        return this.selectedDt && this.selectedDt.item;
    }
}
