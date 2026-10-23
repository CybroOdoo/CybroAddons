import { Component, proxy, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";

export class PollMessage extends Component {
    static template = "odoo_poll.PollMessage";
    static props = {
        pollId: Number,
    };

    setup() {
        this.notification = useService("notification");

        this.state = proxy({
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
            this.state.loading = false;
            if (!this.state.error) {
                this.state.error = _t("Connection Error or Access Failure");
            }
        }
    }

    //Handles clicking an option (immediately records vote on click)
    async toggleOption(optionId) {
        if (this.state.pollData && this.state.pollData.is_closed) {
            return;
        }

        let optionsToSubmit = [];
        const index = (this.state.selectedOptions || []).indexOf(optionId);

        if (!this.state.pollData.is_multiple_choice) {
            optionsToSubmit = [optionId];
            this.state.selectedOptions = [optionId];
        } else {
            const currentSelected = [...(this.state.selectedOptions || [])];
            if (index > -1) {
                currentSelected.splice(index, 1);
            } else {
                currentSelected.push(optionId);
            }
            this.state.selectedOptions = currentSelected;
            optionsToSubmit = currentSelected;
        }

        if (optionsToSubmit.length === 0) {
            await this.removeVotes();
        } else {
            await this.vote(optionsToSubmit);
        }
    }

    //Submit selected votes to backend
    async vote(optionIds = null) {
        const idsToVote = optionIds || this.state.selectedOptions;
        if (!idsToVote || idsToVote.length === 0) {
            this.notification.add(_t("Please select an option first"), { type: "warning" });
            return;
        }

        try {
            const result = await rpc("/discuss/poll/vote", {
                poll_id: this.props.pollId,
                option_ids: idsToVote,
                context: user.context,
            });

            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                this.state.pollData = result;
                this.state.selectedOptions = result.user_votes || idsToVote;
                this.notification.add(_t("Vote recorded!"), { type: "success" });
            }
        } catch (error) {
            this.notification.add(_t("Failed to submit vote"), { type: "danger" });
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
            this.notification.add(_t("Vote removed"), { type: "info" });
        } catch (error) {
            this.notification.add(_t("Failed to remove vote"), { type: "danger" });
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
                this.notification.add(_t("Poll closed"), { type: "info" });
            }
        } catch (error) {
            this.notification.add(_t("Failed to close poll"), { type: "danger" });
        }
    }

    //Get width percentage for progress bar
    getBarWidth(option) {
        return (option.percentage || 0) + "%";
    }

    //Check if option is selected by current user
    isOptionSelected(optionId) {
        return (this.state.selectedOptions || []).includes(optionId);
    }
}

registry.category("discuss.poll_components").add("PollMessage", PollMessage);