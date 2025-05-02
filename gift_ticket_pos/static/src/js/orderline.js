/** @odoo-module */
debugger
import { _t } from "@web/core/l10n/translation";
import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

debugger


patch(Orderline.prototype, {
    setup() {
        debugger
        super.setup(...arguments);
    },

    willStart() {
        return this.super(...arguments).then(() => {
            if (this.props.hidePrice === undefined) {
                this.props.hidePrice = false;
            }
        });
    }
})