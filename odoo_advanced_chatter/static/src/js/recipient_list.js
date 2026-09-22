/** @odoo-module **/
import { Follower } from "@mail/core/web/follower";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { followerCheckStates } from "./composer_patch";


patch(Follower.prototype, {
    setup() {
        super.setup();
        const follower = this.props.follower;
        const followerId = follower?.id;
        // Access thread through the follower object, not props
        const thread = follower?.thread;

        // Initialize state from stored value, default to true
        const initialState = followerId && followerCheckStates.has(followerId)
            ? followerCheckStates.get(followerId)
            : true;

        this.state = useState({
            selected: initialState
        });

        // Sync additionalRecipients with checkbox state on initialization
        if (thread && follower) {
            this.syncRecipientWithCheckboxState(thread, follower, initialState);
        } else {
            console.warn("Cannot sync recipient - missing thread or follower:", { thread, follower });
        }
    },

    /**
     * Synchronize additionalRecipients with checkbox state
     * @param {Object} thread - The thread object
     * @param {Object} follower - The follower object
     * @param {Boolean} isChecked - Whether the checkbox is checked
     */
    syncRecipientWithCheckboxState(thread, follower, isChecked) {
        const partnerId = follower.partner?.id || follower.partner_id?.id;
        const partner = follower.partner || follower.partner_id;

        if (!partnerId || !partner) {
            console.warn("No partner found for follower:", follower);
            return;
        }

        // Initialize additionalRecipients if needed
        if (!thread.additionalRecipients) {
            thread.additionalRecipients = [];
        }

        const existingIndex = thread.additionalRecipients.findIndex(
            recipient => recipient.persona?.id === partnerId
        );

        if (isChecked) {
            // Add to additionalRecipients if checked and not already present
            if (existingIndex === -1) {
                // Create a properly structured recipient object
                const recipientObj = {
                    persona: {
                        id: partnerId,
                        name: partner.name || partner.display_name,
                        email: partner.email,
                        type: "partner"
                    },
                    email: partner.email,
                    lang: partner.lang,
                    reason: "Selected follower"
                };

                // Use immutable assignment to trigger reactivity
                thread.additionalRecipients = [...thread.additionalRecipients, recipientObj];
            }
        } else {
            // Remove from additionalRecipients if unchecked
            if (existingIndex !== -1) {
                // Use immutable assignment to trigger reactivity
                const newRecipients = [...thread.additionalRecipients];
                newRecipients.splice(existingIndex, 1);
                thread.additionalRecipients = newRecipients;
            }
        }
    },

    async check(ev, follower) {
        this.state.selected = !this.state.selected;
        // Access thread through the follower object
        const thread = follower?.thread;

        // Store the checkbox state persistently
        if (follower?.id) {
            followerCheckStates.set(follower.id, this.state.selected);
        }

        if (!thread) {
            return;
        }

        // Sync additionalRecipients with the new checkbox state
        this.syncRecipientWithCheckboxState(thread, follower, this.state.selected);
    }
});
