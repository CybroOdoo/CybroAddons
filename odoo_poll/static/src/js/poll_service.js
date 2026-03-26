/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export const pollService = {
    dependencies: [],

    start() {
        return {

            //Create a new poll
            async createPoll(threadId, threadModel, question, options, isMultipleChoice) {
                return await rpc("/discuss/poll/create", {
                    thread_id: threadId,
                    thread_model: threadModel,
                    question: question,
                    options: options,
                    is_multiple_choice: isMultipleChoice,
                    context: user.context,
                });
            },

            //Submit vote(s) for a poll
            async vote(pollId, optionIds) {
                return await rpc("/discuss/poll/vote", {
                    poll_id: pollId,
                    option_ids: optionIds,
                    context: user.context,
                });
            },

            //Fetch poll results
            async getResults(pollId) {
                return await rpc("/discuss/poll/results", {
                    poll_id: pollId,
                    context: user.context,
                });
            },

            //Close a poll to prevent further voting
            async closePoll(pollId) {
                return await rpc("/discuss/poll/close", {
                    poll_id: pollId,
                    context: user.context,
                });
            },

            //Remove current user's votes from a poll
            async removeVotes(pollId) {
                return await rpc("/discuss/poll/remove_votes", {
                    poll_id: pollId,
                    context: user.context,
                });
            },
        };
    },
};

registry.category("services").add("poll", pollService);
