odoo.define("document.search_panel", function (require) {
    "use strict";
    const searchPanel = require("web.searchPanel");

    /**
        * Extended searchPanel to add custom
    */
    class DocumentSearchPanel extends searchPanel {}
    DocumentSearchPanel.modelExtension = 'CustomDocumentsSearchPanel';
    return DocumentSearchPanel;
});
