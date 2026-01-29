odoo.define("document.search_panel_extension", function (require) {
    "use strict";

    const ActionModel = require("web.ActionModel");
    const SearchPanelModelExtension = require("web.searchPanelModelExtension");

    const isFolderCategory = (s) => s.fieldName === "workspace_id";

    /**
         * SearchPanelModelExtension inherited to updated custom searchPanel
    */
    class CustomDocumentSearchPanelModelExtension extends SearchPanelModelExtension {
        constructor() {
            super(...arguments);
        }
        get(property) {
            /**
                * Get function that return selected workspace id
            */
            switch (property) {

                case "selectedWorkspaceId": return this.getSections(isFolderCategory)[0]['activeValueId'];

            }
            return super.get(...arguments);
        }

        getFolders() {
            /**
                * Get function to return sub-folders (workspace)
            */
            const { values } = this.getSections(isFolderCategory)[0];
            return [...values.values()];
        }

    }
    ActionModel.registry.add("CustomDocumentsSearchPanel", CustomDocumentSearchPanelModelExtension, 30);
    return CustomDocumentSearchPanelModelExtension;
});
