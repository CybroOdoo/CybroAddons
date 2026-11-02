/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosOrder.prototype, {
    getLoyaltyPoints() {
        const loyaltyPoints = {};
        const partnerId = this.partner_id?.id;

        if (!partnerId) {
            return [];
        }

        const loyaltyCards = this.models["loyalty.card"].filter(
            (card) => card.partner_id?.id === partnerId
        );

        for (const program of this.models["loyalty.program"].filter(
            (program) => program.program_type === "loyalty"
        )) {
            const card = loyaltyCards.find(
                (card) => card.program_id?.id === program.id
            );

            const won = program.getEarnedPoints(this);
            const spent = program.getSpentPoints(this);
            const total = program.getNewBalance(this);

            if (!card && !total) {
                continue;
            }

            const name = program.portal_visible
                ? program.portal_point_name
                : _t("Points");

            loyaltyPoints[program.id] = {
                card_id: card ? card.id : -(program.id),
                won: parseFloat(won.toFixed(2)),
                spent: parseFloat(spent.toFixed(2)),
                total: parseFloat(total.toFixed(2)),
                balance: parseFloat(total.toFixed(2)),
                name,
                program,
            };
        }

        const result = Object.entries(loyaltyPoints).map(
            ([programIdStr, points]) => ({
                couponId: points.card_id,
                points,
                program: points.program,
            })
        );
        return result;
    },
});
