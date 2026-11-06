/** @odoo-module **/

import { Component, useState, useRef, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * CodeViewer — line-numbered source viewer with optional edit mode.
 *
 * Two modes:
 *  - View mode (default): renders content as a numbered table with
 *    the existing styling, read-only.
 *  - Edit mode: replaces the table with a plain monospace textarea,
 *    shows Save/Cancel buttons. Saving calls vibe.generated.file.save_content
 *    server-side, which re-validates the parent module.
 *
 * Switching files (selecting a different one in the tree) automatically
 * cancels an in-progress edit. We protect against silent data loss with
 * a confirm() prompt if the draft has unsaved changes.
 */
export class CodeViewer extends Component {
    static template = "vibe_coding_assistant.CodeViewer";

    setup() {
        this.vibeStore = useService("vibeStore");
        this.notification = useService("notification");
        this.storeState = useState(this.vibeStore.state);
        this.textareaRef = useRef("textarea");
        this.codeScrollRef = useRef("codeScroll");

        // Local UI state for the editor
        this.state = useState({
            editing: false,
            draft:   "",   // textarea content while editing
            saving:  false,
            // Briefly true after a jump-to-line; controls the highlight
            // pulse animation. Cleared by a setTimeout.
            flashLine: null,
        });

        // If the active file changes while we're editing, cancel the edit
        // (with a confirm if there are unsaved changes). This prevents the
        // textarea from showing one file's content while the rest of the
        // viewer thinks it's showing another.
        useEffect(
            (path) => {
                if (this.state.editing) {
                    const hasChanges = this.state.draft !== (this.storeState.activeFileContent || "");
                    if (hasChanges) {
                        this.notification.add(
                            "Edits to the previous file were discarded.",
                            { type: "warning" }
                        );
                    }
                    this.state.editing = false;
                    this.state.draft = "";
                }
            },
            () => [this.storeState.activeFilePath]
        );

        // ── Scroll-to-error effect ─────────────────────────────────────
        // When file_tree.onErrorClick sets pendingScrollLine, scroll the
        // code viewer to that line and pulse-highlight it briefly.
        // Then clear the signal so a repeat click on the same error re-fires.
        useEffect(
            (line, content) => {
                if (line == null || !content) return;
                // Defer to next tick so the rendered DOM contains the
                // target row (in case this fires right after selectFile).
                Promise.resolve().then(() => {
                    this._scrollToLine(line);
                    this.state.flashLine = line;
                    // Clear the signal so re-clicking the same error works
                    this.vibeStore.state.pendingScrollLine = null;
                    // Fade the flash highlight after 2 seconds
                    setTimeout(() => {
                        if (this.state.flashLine === line) {
                            this.state.flashLine = null;
                        }
                    }, 2000);
                });
            },
            () => [
                this.storeState.pendingScrollLine,
                // Re-trigger when content arrives, since the user might
                // have clicked an error before the file finished loading
                this.storeState.activeFileContent,
            ]
        );
    }

    /** Scroll the line-numbered table so the target line is roughly centred. */
    _scrollToLine(lineNum) {
        const scrollEl = this.codeScrollRef.el;
        if (!scrollEl) return;
        const lineEl = scrollEl.querySelector(
            '[data-line-num="' + lineNum + '"]'
        );
        if (lineEl) {
            // scrollIntoView centers the element nicely
            lineEl.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
            // Fallback: scroll to top if we can't find the line (file may
            // be shorter than the error line, e.g. file-level error with line=1)
            scrollEl.scrollTop = 0;
        }
    }

    // ── Getters ──────────────────────────────────────────────────────────

    get activePath() {
        return this.storeState.activeFilePath;
    }

    get content() {
        return this.storeState.activeFileContent;
    }

    get isLoading() {
        // Only consider it "loading" when we have a path but no content
        // AND we haven't determined the file is missing. The missing-file
        // case has its own branch in the template.
        return !!this.activePath && this.content === null && !this.isMissing;
    }

    get isMissing() {
        return !!this.storeState.activeFileMissing;
    }

    get isModified() {
        return this.storeState.activeFileIsModified;
    }

    /** Validation errors that apply specifically to the currently open file.
     *  Used to render the file-level warning banner at the top of the viewer.
     */
    get fileErrors() {
        const all = this.storeState.validationErrors || [];
        const path = this.activePath;
        if (!path) return [];
        return all.filter((e) => e.file === path);
    }

    /** Set of line numbers in the current file that have errors. */
    get errorLineSet() {
        const set = new Set();
        for (const e of this.fileErrors) {
            if (e.line) set.add(e.line);
        }
        return set;
    }

    /** Map of line number → error message (first error wins if multiple). */
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
        const errSet = this.errorLineSet;
        const errMsgs = this.errorMessagesByLine;
        const flash = this.state.flashLine;
        return c.split("\n").map((text, i) => {
            const num = i + 1;
            return {
                num,
                text,
                hasError: errSet.has(num),
                errorMsg: errMsgs[num] || null,
                isFlashing: flash === num,
            };
        });
    }

    get fileName() {
        const p = this.activePath;
        if (!p) return "";
        return p.split("/").pop();
    }

    /** Editable: only files that actually exist in the module. */
    get canEdit() {
        return !!this.activePath && !this.isLoading && !this.isMissing;
    }

    get hasUnsavedChanges() {
        return this.state.editing &&
               this.state.draft !== (this.content || "");
    }

    // ── Actions ──────────────────────────────────────────────────────────

    onEdit() {
        this.state.draft = this.content || "";
        this.state.editing = true;
        // Focus the textarea on next tick so the DOM has rendered
        Promise.resolve().then(() => {
            const el = this.textareaRef.el;
            if (el) {
                el.focus();
                // Place caret at start so users see the beginning of the file
                el.setSelectionRange(0, 0);
            }
        });
    }

    onCancel() {
        if (this.hasUnsavedChanges) {
            // window.confirm IS fine here — only fires on the user's explicit
            // cancel click, doesn't run during render
            if (!window.confirm("Discard unsaved changes?")) {
                return;
            }
        }
        this.state.editing = false;
        this.state.draft = "";
    }

    async onSave() {
        if (this.state.saving) return;
        this.state.saving = true;
        try {
            await this.vibeStore.saveFile(this.state.draft);
            this.state.editing = false;
            this.state.draft = "";
            this.notification.add("File saved.", { type: "success" });
        } catch (e) {
            console.error("[CodeViewer] save failed:", e);
            const msg = e.data?.message || e.message || "Save failed.";
            this.notification.add(msg, { type: "danger", sticky: true });
        } finally {
            this.state.saving = false;
        }
    }

    onKeydown(ev) {
        // Ctrl+S / Cmd+S → Save (only in edit mode)
        if (this.state.editing && (ev.ctrlKey || ev.metaKey) && ev.key === "s") {
            ev.preventDefault();
            this.onSave();
        }
        // Esc → Cancel (only in edit mode)
        if (this.state.editing && ev.key === "Escape") {
            ev.preventDefault();
            this.onCancel();
        }
    }
}
