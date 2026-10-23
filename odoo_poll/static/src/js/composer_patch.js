import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { IS_ACTION_DEFINITION_SYM } from "@mail/core/common/action";
import { PollDialog } from "./poll_dialog";

const composerActionsRegistry = registry.category("mail.composer/actions");

// Register as a standard composer quick action for Discuss composer
composerActionsRegistry.add("create-poll", {
    [IS_ACTION_DEFINITION_SYM]: true,
    name: _t("Create Poll"),
    icon: "oi_view-cohort",
    iconClass: "fa fa-bar-chart",
    sequenceQuick: 25,
    condition: ({ composer }) => !composer?.message,
    setup() {
        this.dialogService = useService("dialog");
    },
    onSelected({ composer, owner }) {
        const PollComponent = PollDialog || registry.category("discuss.poll_components").get("PollDialog");
        const thread = (composer && composer.targetThread) || (owner && (owner.thread || (owner.props && owner.props.composer && (owner.props.composer.targetThread || owner.props.composer.thread))));

        if (!thread) {
            return;
        }

        this.dialogService.add(PollComponent, {
            threadId: thread.id,
            threadModel: thread.model,
        });
    },
}, { force: true });