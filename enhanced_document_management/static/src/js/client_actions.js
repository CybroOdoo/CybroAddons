/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FileViewer } from "@web/core/file_viewer/file_viewer";

function normalizeViewerFile(file) {
    if (!file) {
        return file;
    }
    return {
        ...file,
        name: file.name || file.displayName || file.filename || "",
    };
}

/**
 * Handle opening the document viewer from a client action.
 * This is used after password verification for locked documents.
 */
function openDocumentViewer(env, action) {
    const notification = env.services.notification;
    const { attachment, attachment_list } = action.params;
    const currentAttachment = normalizeViewerFile(attachment);
    const files = (attachment_list || [attachment]).map(normalizeViewerFile);
    const viewableFiles = files.filter((file) => file?.isViewable);
    const actionService = env.services.action;
    if (actionService) {
        actionService.doAction({ type: "ir.actions.act_window_close" });
    }

    if (!currentAttachment?.isViewable || !viewableFiles.length) {
        const downloadUrl = currentAttachment?.downloadUrl || currentAttachment?.defaultSource || `/web/content/${currentAttachment?.id}?download=true`;
        window.open(downloadUrl, '_blank');
        return;
    }

    const startIndex = viewableFiles.findIndex((file) => file.id === currentAttachment.id);
    registry.category("main_components").remove("web.file_viewer_locked");
    registry.category("main_components").add("web.file_viewer_locked", {
        Component: FileViewer,
        props: {
            files: viewableFiles,
            startIndex,
            close: () => registry.category("main_components").remove("web.file_viewer_locked"),
        },
    });
}

/**
 * Handle soft reload of the current view.
 * This avoids full page refreshes (location.reload()) and uses Odoo's internal routing.
 */
function softReload(env, action) {
    env.bus.trigger("reload");
    // Fallback to standard reload action if available
    const actionService = env.services.action;
    if (actionService) {
        actionService.doAction("reload");
    }
}

registry.category("actions").add("open_document_viewer", openDocumentViewer);
registry.category("actions").add("edm_soft_reload", softReload);
