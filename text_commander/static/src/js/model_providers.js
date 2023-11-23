/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
//Creates a class for rendering the template when the commander is entered
class ModelItemCommand extends Component {}
ModelItemCommand.template = "text_commander.ModelItemsCommand";
//Creating a new namespace
const ModelItemCommandRegistry = registry.category("command_setup");
ModelItemCommandRegistry.add("!", {
    debounceDelay: 200,
    emptyMessage: _lt("Commands: "),
    name: _lt("Record"),
    placeholder: _lt("Search for a record..."),
});
const ModelItemCommandProvider = registry.category("command_provider");
ModelItemCommandProvider.add("model",{
    namespace: "!",
    async provide(env, options){
        const suggestion = []
        suggestion.push({
            Component: ModelItemCommand,
        });
        return suggestion
    },
});
