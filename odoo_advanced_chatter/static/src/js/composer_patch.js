/** @odoo-module **/
import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";

// Import nothing for now, we define the map here

// Shared state for follower checkboxes
const followerCheckStates = new Map();

patch(Composer.prototype, {
    setup() {
        super.setup();

        // Reactively populate recipients when followers change OR checkbox state changes
        useEffect(
            () => {
                // Clean up non-follower recipients from additionalRecipients
                this.cleanupNonFollowerRecipients();

                // Populate recipients from checked followers
                this.populateRecipientsFromFollowers();
            },
            () => [this.props.composer.thread?.followers?.length, this.props.composer.thread]
        );
    },

    /**
     * Remove non-follower recipients from additionalRecipients
     * This ensures the recipients input only shows actual followers
     */
    cleanupNonFollowerRecipients() {
        const thread = this.props.composer?.thread;

        if (!thread || !thread.additionalRecipients || !thread.followers) {
            return;
        }

        // Get all follower partner IDs
        const followerPartnerIds = new Set(
            thread.followers.map(f => f.partner?.id || f.partner_id?.id).filter(Boolean)
        );

        // Filter additionalRecipients to only include actual followers
        const originalLength = thread.additionalRecipients.length;
        thread.additionalRecipients = thread.additionalRecipients.filter(recipient => {
            const partnerId = recipient.persona?.id;
            const isFollower = followerPartnerIds.has(partnerId);
            return isFollower;
        });

        const removedCount = originalLength - thread.additionalRecipients.length;
    },

    /**
     * Populate additionalRecipients from checked followers
     * This ensures all checked followers appear in the recipients input
     */
    populateRecipientsFromFollowers() {
        const thread = this.props.composer?.thread;

        if (!thread || !thread.followers) {
            console.warn("Cannot populate recipients - no thread or followers");
            return;
        }
        // Initialize additionalRecipients if needed
        if (!thread.additionalRecipients) {
            thread.additionalRecipients = [];
        }

        // Iterate through all followers
        for (const follower of thread.followers) {
            const followerId = follower.id;
            const partner = follower.partner || follower.partner_id;
            const partnerId = partner?.id;

            if (!partnerId || !partner) {
                console.warn("Skipping follower - no partner:", follower);
                continue;
            }

            // Check if this follower's checkbox is checked (default to true)
            const isChecked = followerCheckStates.has(followerId)
                ? followerCheckStates.get(followerId)
                : true;
            if (isChecked) {
                // Check if already in additionalRecipients
                const exists = thread.additionalRecipients.some(
                    r => r.persona?.id === partnerId
                );

                if (!exists) {
                    const recipientObj = {
                        persona: {
                            id: partnerId,
                            name: partner.name || partner.display_name,
                            email: partner.email,
                            type: "partner"
                        },
                        email: partner.email,
                        lang: partner.lang,
                        reason: "Follower"
                    };

                    thread.additionalRecipients = [...thread.additionalRecipients, recipientObj];
                }
            } else {
                // Remove from additionalRecipients if present
                const index = thread.additionalRecipients.findIndex(
                    r => r.persona?.id === partnerId
                );

                if (index !== -1) {
                    const newRecipients = [...thread.additionalRecipients];
                    newRecipients.splice(index, 1);
                    thread.additionalRecipients = newRecipients;
                }
            }
        }



    },

    /**
     * Get all visible recipient IDs (checked followers + manual additions)
     * effectively syncing the backend whitelist with the onscreen input.
     * @returns {Array} Array of partner IDs
     */
    getVisibleRecipientIds() {
        const thread = this.props.composer?.thread;
        if (!thread) return null;

        // Combine suggested (followers) and additional (manual/checked)
        const allRecipients = [
            ...(thread.suggestedRecipients || []),
            ...(thread.additionalRecipients || [])
        ];

        const selectedPartnerIds = [];
        const seenIds = new Set();

        for (const recipient of allRecipients) {
            // Robust ID extraction handling standard Odoo objects and custom wrappers
            let partnerId = recipient.partner_id || recipient.persona?.id || recipient.partner?.id || recipient.id;

            // Handle Many2One tuple [id, name]
            if (Array.isArray(partnerId)) {
                partnerId = partnerId[0];
            }

            if (partnerId && typeof partnerId === 'number') {
                if (!seenIds.has(partnerId)) {
                    seenIds.add(partnerId);
                    selectedPartnerIds.push(partnerId);
                }
            }
        }

        // Also check if we should verify checkbox state for suggestedRecipients?
        // Usually suggestedRecipients in RecipientInput ARE the selected ones.
        // Unchecked followers in my patch are REMOVED from additionalRecipients.
        // Are they removed from suggestedRecipients? 
        // My patch doesn't touch suggestedRecipients directly but RecipientInput might.
        // However, if strict whitelist is applied, we must ensure we don't accidentally include unchecked ones if they persist in suggestedRecipients.
        // Users reported "input list IS correct". Input list renders checks.
        // If suggestedRecipients contains unchecked items, they would appear in input.
        // Standard Odoo Chatter: If I uncheck a follower, they are removed from the input list?
        // Actually, "Followers" dropdown is separate.
        // "RecipientsInput" shows "To: ...".
        // If I uncheck, they disappear from "To:".
        // So `suggestedRecipients` / `additionalRecipients` MUST be reflecting the removal.
        // So just taking the list is safe.
        return selectedPartnerIds.length > 0 ? selectedPartnerIds : null;
    },

    /**
     * Override _sendMessage to include selected followers/recipients whitelist
     * We override the internal method because sendMessage() does not take arguments
     * and we need to inject into postData.
     */
    async _sendMessage(value, postData, extraData) {
        // Calculate the whitelist based on VISIBLE recipients
        const visibleRecipientIds = this.getVisibleRecipientIds();
        // If we have a list, enforce it as a whitelist
        if (visibleRecipientIds) {
            if (!postData) {
                postData = {};
            }
            postData.selected_follower_partner_ids = visibleRecipientIds;
        }

        return super._sendMessage(value, postData, extraData);
    },
});

// Export the Map for recipient_list.js
export { followerCheckStates };
