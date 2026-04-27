/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export class PollMessage extends Component {
    static template = "odoo_poll.PollMessage";
    static props = {
        pollId: Number,
    };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            pollData: null,
            selectedOptions: [],
            loading: true,
            error: false,
            accessDenied: false,
        });

        onWillStart(async () => {
            await this.loadPoll();
        });
    }


    //Fetch poll results from backend
    async loadPoll() {
        try {
            const data = await rpc("/discuss/poll/results", {
                poll_id: this.props.pollId,
                company_id: user.currentCompanyId,
                context: user.context,
            });
            if (data.error) {
                this.state.error = data.error;
                // Hide for any access or missing record error
                this.state.accessDenied = (data.error === "Access Denied");
                this.state.pollData = null;
            } else {
                this.state.pollData = data;
                this.state.selectedOptions = data.user_votes || [];
                this.state.error = false;
                this.state.accessDenied = false;
            }
            this.state.loading = false;
        } catch (error) {
            console.error("Error loading poll:", error);
            this.state.loading = false;
            if (!this.state.error) {
                this.state.error = "Connection Error or Access Failure";
            }
        }
    }

    //Handles single and multiple choice logic
    toggleOption(optionId) {
        const index = this.state.selectedOptions.indexOf(optionId);
        if (index > -1) {
            this.state.selectedOptions.splice(index, 1);
        } else {
            if (!this.state.pollData.is_multiple_choice) {
                this.state.selectedOptions = [optionId];
            } else {
                this.state.selectedOptions.push(optionId);
            }
        }
    }

    //Submit selected votes to backend
    async vote() {
        if (this.state.selectedOptions.length === 0) {
            this.notification.add("Please select an option first", { type: "warning" });
            return;
        }

        try {
            const result = await rpc("/discuss/poll/vote", {
                poll_id: this.props.pollId,
                option_ids: this.state.selectedOptions,
                context: user.context,
            });

            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                this.state.pollData = result;
                this.notification.add("Vote recorded!", { type: "success" });
            }
        } catch (error) {
            console.error("Error voting:", error);
            this.notification.add("Failed to submit vote", { type: "danger" });
        }
    }

    //Remove current user's votes
    async removeVotes() {
        try {
            const result = await rpc("/discuss/poll/remove_votes", {
                poll_id: this.props.pollId,
                context: user.context,
            });
            this.state.pollData = result;
            this.state.selectedOptions = [];
            this.notification.add("Vote removed", { type: "info" });
        } catch (error) {
            console.error("Error removing votes:", error);
        }
    }

    //Close the poll (author only)
    async closePoll() {
        try {
            const result = await rpc("/discuss/poll/close", {
                poll_id: this.props.pollId,
                context: user.context,
            });

            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                await this.loadPoll();
                this.notification.add("Poll closed", { type: "info" });
            }
        } catch (error) {
            console.error("Error closing poll:", error);
        }
    }

    //Get width percentage for progress bar
    getBarWidth(option) {
        return option.percentage + "%";
    }

    //Check if option is selected by current user
    isOptionSelected(optionId) {
        return this.state.selectedOptions.includes(optionId);
    }
}

registry.category("discuss.poll_components").add("PollMessage", PollMessage);
