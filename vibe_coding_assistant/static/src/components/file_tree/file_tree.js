/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ── Module-level helpers (not re-created on every render) ─────────────────

/**
 * Build a nested dict from a flat [{path, language}] list.
 * @param {Array} files
 * @returns {Object} Nested tree dict
 */
function buildTree(files) {
    const tree = {};
    for (const f of files) {
        const parts = f.path.split("/");
        let node = tree;
        for (let i = 0; i < parts.length - 1; i++) {
            const dir = parts[i];
            if (!node[dir]) node[dir] = { _type: "dir", _children: {} };
            node = node[dir]._children;
        }
        const fname = parts[parts.length - 1];
        node[fname] = {
            _type: "file",
            _path: f.path,
            _language: f.language || "plaintext",
            _modified: !!f.user_modified,
        };
    }
    return tree;
}

/**
 * Flatten the nested tree into a depth-annotated array for rendering.
 * Directories before files at each level, both sorted alphabetically.
 * @param {Object} node
 * @param {number} depth
 * @param {Array} result  Accumulated output array (mutated in place)
 */
function flattenTree(node, depth, result) {
    const entries = Object.entries(node);
    const dirs  = entries.filter(([, v]) => v._type === "dir") .sort(([a], [b]) => a.localeCompare(b));
    const files = entries.filter(([, v]) => v._type === "file").sort(([a], [b]) => a.localeCompare(b));
    for (const [name, val] of dirs) {
        result.push({ type: "dir",  name, depth, key: "d:" + depth + ":" + name });
        flattenTree(val._children, depth + 1, result);
    }
    for (const [name, val] of files) {
        result.push({
            type: "file", name, depth, key: "f:" + val._path,
            path: val._path, language: val._language,
            modified: val._modified,
        });
    }
}

const FILE_ICONS = {
    python:     "fa-file-code-o",
    xml:        "fa-code",
    csv:        "fa-table",
    markdown:   "fa-file-text-o",
    json:       "fa-file-code-o",
    javascript: "fa-file-code-o",
};

// ── Component ──────────────────────────────────────────────────────────────

/**
 * FileTree — displays the generated module's file structure.
 *
 * Renders a depth-annotated flat list built from the flat path list in the
 * store. Clicking a file calls vibeStore.selectFile().
 *
 * Header row: module name + validation badge + Download button.
 * Below header: validation errors banner when validation_state === "invalid".
 */
export class FileTree extends Component {
    static template = "vibe_coding_assistant.FileTree";

    setup() {
        this.vibeStore = useService("vibeStore");
        this.storeState = useState(this.vibeStore.state);
    }

    // ── Computed getters ─────────────────────────────────────────────────

    get moduleData() {
        return this.storeState.activeModuleData || {};
    }

    get moduleName() {
        return this.moduleData.name || "Module";
    }

    get validationState() {
        return this.moduleData.validation_state || "pending";
    }

    /** Validation errors as a structured list — parsed once by the store. */
    get validationErrors() {
        return this.storeState.validationErrors || [];
    }

    get hasErrors() {
        return this.validationErrors.length > 0;
    }

    /** Map of file path → number of errors against that file.
     *
     * Used to render the red error badge next to each file in the tree.
     * Files with zero errors are absent from the map.
     */
    get errorsByFile() {
        const counts = {};
        for (const err of this.validationErrors) {
            const f = err.file || "(unknown)";
            counts[f] = (counts[f] || 0) + 1;
        }
        return counts;
    }

    /** How many errors apply to the given file path. */
    errorsForFile(path) {
        return this.errorsByFile[path] || 0;
    }

    get downloadUrl() {
        const id = this.storeState.activeModuleId;
        return id ? "/vibe/module/" + id + "/download" : null;
    }

    get treeItems() {
        const files = this.storeState.moduleFiles;
        if (!files || !files.length) return [];
        const result = [];
        flattenTree(buildTree(files), 0, result);
        // Decorate each file row with its error count so the template can
        // render the badge without recomputing on every iteration.
        const errs = this.errorsByFile;
        for (const item of result) {
            if (item.type === "file") {
                item.errorCount = errs[item.path] || 0;
            }
        }
        return result;
    }

    // ── Event handlers ───────────────────────────────────────────────────

    isActive(path) {
        return this.storeState.activeFilePath === path;
    }

    async onSelectFile(path) {
        await this.vibeStore.selectFile(path);
    }

    /** Click an error in the banner — open the file and scroll to the line.
     *
     * Line scrolling itself happens in CodeViewer (via a useEffect on
     * activeFilePath / pendingScrollLine). Here we just open the file and
     * publish the target line.
     */
    async onErrorClick(err) {
        if (!err.file) return;
        await this.vibeStore.selectFile(err.file);
        // Publish the line for CodeViewer to pick up. Null line (file-level
        // error) still scrolls to the top.
        this.vibeStore.state.pendingScrollLine = err.line || 1;
    }

    fileIcon(language) {
        return "fa " + (FILE_ICONS[language] || "fa-file-o");
    }
}
