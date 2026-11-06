
import { describe, expect, test } from "@odoo/hoot";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { MembershipPopup } from "@membership_in_pos/js/abstract_awaitable_popup";

describe("membership_in_pos membership popup", () => {
    function makePopup({ partner = { id: 42 }, cardCode = "CARD-123", cardResult = false } = {}) {
        const alerts = [];
        const calls = [];
        const popup = {
            cardCodeRef: () => ({ value: cardCode }),
            pos: { getOrder: () => ({ getPartner: () => partner }) },
            orm: {
                call: async (...args) => {
                    calls.push(args);
                    return cardResult;
                },
            },
            dialog: { add: (...args) => alerts.push(args) },
            state: { card: false },
        };
        return { popup, alerts, calls };
    }

    test("asks for a customer before checking a membership", async () => {
        const { popup, alerts, calls } = makePopup({ partner: false });

        await MembershipPopup.prototype.Membership_check.call(popup);

        expect(alerts).toHaveLength(1);
        expect(alerts[0][0]).toBe(AlertDialog);
        expect(Boolean(alerts[0][1].title)).toBe(true);
        expect(Boolean(alerts[0][1].body)).toBe(true);
        expect(calls).toHaveLength(0);
    });

    test("checks the entered card code for the selected customer", async () => {
        const card = { id: 7, discount: 15 };
        const { popup, calls } = makePopup({ cardResult: card });

        await MembershipPopup.prototype.Membership_check.call(popup);

        expect(calls).toHaveLength(1);
        expect(calls[0][0]).toBe("membership.card");
        expect(calls[0][1]).toBe("membership_card_check");
        expect(calls[0][2]).toEqual([[]]);
        expect(calls[0][3]).toEqual({
            customer_input: [{ customerInput: "CARD-123", customer: 42 }],
        });
        expect(popup.state.card).toBe(card);
    });

    test("alerts when the membership lookup finds no valid card", async () => {
        const { popup, alerts } = makePopup({ cardResult: 0 });

        await MembershipPopup.prototype.Membership_check.call(popup);

        expect(popup.state.card).toBe(0);
        expect(alerts).toHaveLength(1);
        expect(alerts[0][0]).toBe(AlertDialog);
        expect(Boolean(alerts[0][1].title)).toBe(true);
        expect(Boolean(alerts[0][1].body)).toBe(true);
    });
});
