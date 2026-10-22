import { Component, proxy, signal, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * CodeViewer — line-numbered source viewer with optional edit mode.
 *
 * Two modes:
 *  - View mode (default): renders content as a numbered table, read-only.
 *  - Edit mode: replaces the table with a plain monospace textarea,
 *    shows Save/Cancel buttons. Saving calls vibe.generated.file.save_content
 *    server-side, which re-validates the parent module.
 */
export class CodeViewer extends Component {
    static template = "vibe_coding_assistant.CodeViewer";

    // OWL 3: refs are signal.ref() class fields, accessed as this.ref() not this.ref.el
    textareaRef  = signal.ref();
    codeScrollRef = signal.ref();

    setup() {
        // proxy(useService(...)) is the OWL 3 pattern for reactive shared state
        this.vibeStore    = proxy(useService("vibeStore"));
        this.notification = useService("notification");

        // Local UI state for the editor
        this.state = proxy({
            editing:   false,
            draft:     "",
            saving:    false,
            flashLine: null,
        });

        // If the active file changes while editing, cancel the edit
        let lastPath = null;
        useEffect(() => {
            const path = this.vibeStore.state.activeFilePath;
            if (path !== lastPath) {
                lastPath = path;
                if (this.state.editing) {
                    const hasChanges = this.state.draft !== (this.vibeStore.state.activeFileContent || "");
                    if (hasChanges) {
                        this.notification.add(
                            _t("Edits to the previous file were discarded."),
                            { type: "warning" }
                        );
                    }
                    this.state.editing = false;
                    this.state.draft   = "";
                }
            }
        });

        // Scroll-to-error effect
        useEffect(() => {
            const line = this.vibeStore.state.pendingScrollLine;
            const content = this.vibeStore.state.activeFileContent;
            if (line == null || !content) return;
            Promise.resolve().then(() => {
                this._scrollToLine(line);
                this.state.flashLine = line;
                this.vibeStore.state.pendingScrollLine = null;
                setTimeout(() => {
                    if (this.state.flashLine === line) {
                        this.state.flashLine = null;
                    }
                }, 2000);
            });
        });
    }

    _scrollToLine(lineNum) {
        const scrollEl = this.codeScrollRef();
        if (!scrollEl) return;
        const lineEl = scrollEl.querySelector('[data-line-num="' + lineNum + '"]');
        if (lineEl) {
            lineEl.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
            scrollEl.scrollTop = 0;
        }
    }

    get activePath() {
        return this.vibeStore.state.activeFilePath;
    }

    get content() {
        return this.vibeStore.state.activeFileContent;
    }

    get isLoading() {
        return !!this.activePath && this.content === null && !this.isMissing;
    }

    get isMissing() {
        return !!this.vibeStore.state.activeFileMissing;
    }

    get isModified() {
        return this.vibeStore.state.activeFileIsModified;
    }

    get fileErrors() {
        const all  = this.vibeStore.state.validationErrors || [];
        const path = this.activePath;
        if (!path) return [];
        return all.filter((e) => e.file === path);
    }

    get errorLineSet() {
        const set = new Set();
        for (const e of this.fileErrors) {
            if (e.line) set.add(e.line);
        }
        return set;
    }

    get errorMessagesByLine() {
        const map = {};
        for (const e of this.fileErrors) {
            if (e.line && !map[e.line]) {
                map[e.line] = e.message;
            }
        }
        return map;
    }

    get lines() {
        const c = this.content;
        if (!c) return [];
        const errSet  = this.errorLineSet;
        const errMsgs = this.errorMessagesByLine;
        const flash   = this.state.flashLine;
        return c.split("\n").map((text, i) => {
            const num = i + 1;
            return {
                num,
                text,
                hasError:   errSet.has(num),
                errorMsg:   errMsgs[num] || null,
                isFlashing: flash === num,
            };
        });
    }

    get fileName() {
        const p = this.activePath;
        if (!p) return "";
        return p.split("/").pop();
    }

    get canEdit() {
        return !!this.activePath && !this.isLoading && !this.isMissing;
    }

    get hasUnsavedChanges() {
        return this.state.editing && this.state.draft !== (this.content || "");
    }

    onEdit() {
        this.state.draft   = this.content || "";
        this.state.editing = true;
        Promise.resolve().then(() => {
            const el = this.textareaRef();
            if (el) {
                el.focus();
                el.setSelectionRange(0, 0);
            }
        });
    }

    onCancel() {
        if (this.hasUnsavedChanges) {
            if (!window.confirm(_t("Discard unsaved changes?"))) return;
        }
        this.state.editing = false;
        this.state.draft   = "";
    }

    async onSave() {
        if (this.state.saving) return;
        this.state.saving = true;
        try {
            await this.vibeStore.saveFile(this.state.draft);
            this.state.editing = false;
            this.state.draft   = "";
            this.notification.add(_t("File saved."), { type: "success" });
        } catch (e) {
            const msg = e.data?.message || e.message || _t("Save failed.");
            this.notification.add(msg, { type: "danger", sticky: true });
        } finally {
            this.state.saving = false;
        }
    }

    onKeydown(ev) {
        if (this.state.editing && (ev.ctrlKey || ev.metaKey) && ev.key === "s") {
            ev.preventDefault();
            this.onSave();
        }
        if (this.state.editing && ev.key === "Escape") {
            ev.preventDefault();
            this.onCancel();
        }
    }
}
