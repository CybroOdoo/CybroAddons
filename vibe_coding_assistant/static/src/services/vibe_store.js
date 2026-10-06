/** @odoo-module **/

import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

/**
 * Parse the validation_errors field from a vibe.generated.module record.
 *
 * Server stores it as a JSON-string of {file, line, message} dicts, or
 * `false` when the module is valid. Returns an empty array in all the
 * "no errors" cases (no module loaded, parse failure, field empty) so
 * callers can safely iterate without null-checks.
 */
function parseValidationErrors(moduleRecord) {
    if (!moduleRecord || !moduleRecord.validation_errors) return [];
    try {
        const errors = JSON.parse(moduleRecord.validation_errors);
        return Array.isArray(errors) ? errors : [];
    } catch (e) {
        console.warn("[vibeStore] could not parse validation_errors:", e);
        return [];
    }
}

/**
 * vibeStore — central reactive state for the Vibe Coding Assistant.
 *
 * Phase 3: conversations + messaging.
 * Phase 4: module generation pipeline.
 * Phase 5: file tree + code viewer.
 * Phase 6: provider info, archive, loading states.
 */
const vibeStoreService = {
    dependencies: ["orm", "notification"],

    start(env, { orm, notification }) {
        const state = reactive({
            // Conversation list
            conversations: [],
            isLoadingConversations: false,
            activeConversationId: null,
            messages: [],
            // Token totals for the active conversation
            conversationTotals: null,  // {tokens_input_total, tokens_output_total, tokens_total}
            // Module preview
            activeModuleId: null,
            activeModuleData: null,
            moduleFiles: [],
            // Validation errors for the active module, parsed from
            // activeModuleData.validation_errors JSON. Array of:
            //   { file: string, line: number | null, message: string }
            validationErrors: [],
            // File viewer
            activeFilePath: null,
            activeFileContent: null,
            activeFileId: null,           // for save calls
            activeFileIsModified: false,  // shows "Modified" badge in viewer
            activeFileMissing: false,     // true if the path doesn't exist in the module
            // Signal: when set to a line number, code_viewer scrolls to
            // that line and highlights it briefly. Cleared after consumption.
            pendingScrollLine: null,
            // Provider info (null = not loaded yet, false = no active provider)
            providerInfo: null,
            // Prompt templates (loaded once on mount)
            promptTemplates: [],
            // Signal: when the user clicks a template chip, this is set to
            // the prompt text. The composer watches it, inserts the text,
            // and clears the signal back to null.
            pendingPromptInsert: null,
            // UI flags
            isSending: false,
            error: null,
        });

        // ── Provider info ────────────────────────────────────────────────

        async function loadProviderInfo() {
            // Use searchRead instead of orm.call("get_active_provider_info") —
            // searchRead has a stable, well-defined signature across Odoo
            // versions and avoids the @api.model recordset-argument confusion
            // that can cause RPC_ERROR on some Odoo 19 builds.
            try {
                const configs = await orm.searchRead(
                    "ai.provider.user.config",
                    [["is_active", "=", true]],
                    ["provider_id", "selected_model"],
                    { limit: 1 }
                );
                if (configs.length) {
                    const c = configs[0];
                    state.providerInfo = {
                        // provider_id from searchRead is [id, display_name]
                        provider_name: c.provider_id ? c.provider_id[1] : "",
                        provider_code: false,   // not needed by the UI badge
                        model: c.selected_model,
                    };
                } else {
                    state.providerInfo = false;
                }
            } catch (e) {
                console.error("[vibeStore] loadProviderInfo:", e);
                state.providerInfo = false;
            }
        }

        // ── Conversations ────────────────────────────────────────────────

        async function loadConversations() {
            state.isLoadingConversations = true;
            try {
                state.conversations = await orm.searchRead(
                    "vibe.conversation",
                    [["state", "!=", "archived"]],
                    ["name", "last_activity", "state"],
                    { order: "last_activity desc, id desc" }
                );
            } catch (e) {
                console.error("[vibeStore] loadConversations:", e);
            } finally {
                state.isLoadingConversations = false;
            }
        }

        async function newConversation() {
            state.activeConversationId = null;
            state.messages = [];
            state.conversationTotals = null;
            state.activeModuleId = null;
            state.activeModuleData = null;
            state.moduleFiles = [];
            state.validationErrors = [];
            state.activeFilePath = null;
            state.activeFileContent = null;
            state.activeFileId = null;
            state.activeFileIsModified = false;
            state.activeFileMissing = false;
        }

        async function selectConversation(id) {
            if (state.activeConversationId === id) return;
            state.activeConversationId = id;
            state.messages = [];
            state.conversationTotals = null;
            state.activeModuleId = null;
            state.activeModuleData = null;
            state.moduleFiles = [];
            state.validationErrors = [];
            state.activeFilePath = null;
            state.activeFileContent = null;
            state.activeFileId = null;
            state.activeFileIsModified = false;
            state.activeFileMissing = false;

            try {
                const result = await orm.call(
                    "vibe.conversation",
                    "load_messages",
                    [[id]]
                );
                state.messages = result.messages || [];
                state.conversationTotals = result.conversation || null;
            } catch (e) {
                console.error("[vibeStore] selectConversation:", e);
                notification.add("Failed to load conversation.", { type: "danger" });
            }
        }

        async function archiveConversation(id) {
            try {
                await orm.call("vibe.conversation", "action_archive", [[id]]);
                if (state.activeConversationId === id) {
                    await newConversation();
                }
                await loadConversations();
            } catch (e) {
                console.error("[vibeStore] archiveConversation:", e);
                notification.add("Could not archive conversation.", { type: "danger" });
            }
        }

        // ── Messaging ────────────────────────────────────────────────────

        async function sendMessage(content) {
            if (!content.trim() || state.isSending) return;
            state.isSending = true;
            state.error = null;

            try {
                if (!state.activeConversationId) {
                    // orm.create expects an array of records and returns an array of IDs,
                    // even when creating a single record.
                    const ids = await orm.create("vibe.conversation", [{ name: "New Chat" }]);
                    state.activeConversationId = Array.isArray(ids) ? ids[0] : ids;
                    // Refresh the sidebar NOW so the new conversation appears even
                    // if the AI call below takes 30+ seconds or fails.
                    await loadConversations();
                }

                // Optimistic user bubble — appears instantly so the user sees
                // their message while Gemini is generating (can take 30–90s).
                state.messages = [
                    ...state.messages,
                    {
                        id: "__optimistic__",
                        role: "user",
                        content,
                        generated_module_id: false,
                        generated_module_name: false,
                        validation_state: false,
                    },
                ];

                const result = await orm.call(
                    "vibe.conversation",
                    "action_send_message",
                    [[state.activeConversationId], content]
                );

                // Defensively handle both wrapped and unwrapped responses.
                // Odoo's orm.call sometimes returns the dict directly, sometimes
                // wraps it; never returns null on a successful call.
                const payload = result || {};
                const newMessages = Array.isArray(payload.messages)
                    ? payload.messages
                    : [];

                if (newMessages.length === 0) {
                    console.warn(
                        "[vibeStore] action_send_message returned no messages — " +
                        "this should not happen. Result was:", result
                    );
                    // Pull messages directly from the DB as a fallback
                    const dbMessages = await orm.searchRead(
                        "vibe.message",
                        [["conversation_id", "=", state.activeConversationId]],
                        ["role", "content", "generated_module_id"],
                        { order: "create_date asc, id asc" }
                    );
                    state.messages = dbMessages.map((m) => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        generated_module_id: m.generated_module_id ? m.generated_module_id[0] : false,
                        generated_module_name: m.generated_module_id ? m.generated_module_id[1] : false,
                        validation_state: false,
                    }));
                } else {
                    state.messages = newMessages;
                }
                // Update running totals if the payload included them
                if (payload.conversation) {
                    state.conversationTotals = payload.conversation;
                }

                await loadConversations();

            } catch (e) {
                console.error("[vibeStore] sendMessage:", e);
                // Pull as much detail as possible from the Odoo error envelope
                const msg =
                    e.data?.message ||
                    e.data?.name ||
                    e.message ||
                    "An unknown error occurred while contacting the AI.";
                state.error = msg;
                // sticky so the user actually reads it
                notification.add(msg, { type: "danger", sticky: true });
                state.messages = state.messages.filter((m) => m.id !== "__optimistic__");
            } finally {
                state.isSending = false;
            }
        }

        /**
         * Send a refinement message — extends the most recent generated
         * module in the conversation rather than creating a new one from
         * scratch. Server enforces the precondition (must have a previous
         * module); we trust state.conversationTotals.can_refine for the
         * UI gate.
         */
        async function refineMessage(content) {
            if (!content.trim() || state.isSending) return;
            if (!state.activeConversationId) return;
            state.isSending = true;
            state.error = null;

            try {
                // Optimistic user bubble showing the refinement intent.
                state.messages = [
                    ...state.messages,
                    {
                        id: "__optimistic__",
                        role: "user",
                        content: "🔄 Refine: " + content,
                        generated_module_id: false,
                        generated_module_name: false,
                        validation_state: false,
                    },
                ];

                const result = await orm.call(
                    "vibe.conversation",
                    "action_refine_module",
                    [[state.activeConversationId], content]
                );

                const payload = result || {};
                const newMessages = Array.isArray(payload.messages)
                    ? payload.messages : [];
                if (newMessages.length) {
                    state.messages = newMessages;
                }
                if (payload.conversation) {
                    state.conversationTotals = payload.conversation;
                }
                await loadConversations();
            } catch (e) {
                console.error("[vibeStore] refineMessage:", e);
                const msg = e.data?.message || e.data?.name || e.message
                    || "Refinement failed.";
                state.error = msg;
                notification.add(msg, { type: "danger", sticky: true });
                state.messages = state.messages.filter((m) => m.id !== "__optimistic__");
            } finally {
                state.isSending = false;
            }
        }

        // ── Module preview ───────────────────────────────────────────────

        async function selectModule(moduleId) {
            state.activeModuleId = moduleId;
            state.activeModuleData = null;
            state.moduleFiles = [];
            state.activeFilePath = null;
            state.activeFileContent = null;
            state.activeFileId = null;
            state.activeFileIsModified = false;
            state.activeFileMissing = false;

            try {
                const [mods, files] = await Promise.all([
                    orm.searchRead(
                        "vibe.generated.module",
                        [["id", "=", moduleId]],
                        ["name", "technical_name", "validation_state", "validation_errors"],
                        { limit: 1 }
                    ),
                    orm.searchRead(
                        "vibe.generated.file",
                        [["module_id", "=", moduleId]],
                        ["id", "path", "language", "user_modified"],
                        { order: "path asc" }
                    ),
                ]);
                if (mods.length) state.activeModuleData = mods[0];
                state.moduleFiles = files;
                state.validationErrors = parseValidationErrors(mods[0]);
            } catch (e) {
                console.error("[vibeStore] selectModule:", e);
                notification.add("Failed to load module preview.", { type: "danger" });
            }
        }

        async function selectFile(path) {
            if (state.activeFilePath === path) return;
            state.activeFilePath = path;
            state.activeFileContent = null;
            state.activeFileId = null;
            state.activeFileIsModified = false;
            state.activeFileMissing = false;
            if (!state.activeModuleId || !path) return;

            try {
                const results = await orm.searchRead(
                    "vibe.generated.file",
                    [["module_id", "=", state.activeModuleId], ["path", "=", path]],
                    ["id", "content", "user_modified"],
                    { limit: 1 }
                );
                if (results[0]) {
                    state.activeFileId = results[0].id;
                    state.activeFileContent = results[0].content || "";
                    state.activeFileIsModified = !!results[0].user_modified;
                } else {
                    // File doesn't exist in this module. Common case: a
                    // validation error referring to a file that the AI
                    // *didn't* generate (e.g. missing ir.model.access.csv).
                    // Set the missing flag so the viewer can show a helpful
                    // explanation instead of an infinite loading spinner.
                    state.activeFileMissing = true;
                    state.activeFileContent = "";
                }
            } catch (e) {
                console.error("[vibeStore] selectFile:", e);
                state.activeFileMissing = true;
                state.activeFileContent = "";
            }
        }

        /** Save edited content for the currently-active file.
         *
         * Calls vibe.generated.file.save_content, which writes the new content,
         * marks the file user_modified, and re-validates the parent module.
         * Refreshes the affected store state (file content, module validation,
         * file-tree user_modified flags).
         */
        async function saveFile(newContent) {
            if (!state.activeFileId) {
                throw new Error("No active file to save.");
            }
            const result = await orm.call(
                "vibe.generated.file",
                "save_content",
                [[state.activeFileId], newContent]
            );

            // Apply server-returned state locally so the UI updates without
            // a full reload.
            state.activeFileContent = result.content;
            state.activeFileIsModified = !!result.user_modified;

            // Update the file in the moduleFiles array so the tree shows the
            // "modified" dot.
            state.moduleFiles = state.moduleFiles.map((f) =>
                f.id === state.activeFileId
                    ? { ...f, user_modified: true }
                    : f
            );

            // Update module-level validation state for the preview header.
            if (state.activeModuleData) {
                const errors = result.validation_errors || [];
                state.activeModuleData = {
                    ...state.activeModuleData,
                    validation_state: result.validation_state,
                    validation_errors: errors.length ? JSON.stringify(errors) : false,
                };
                // Refresh the parsed-errors store field too so the file tree
                // and code viewer pick up the change immediately.
                state.validationErrors = Array.isArray(errors) ? errors : [];
            }
            return result;
        }

        // ── Prompt templates ─────────────────────────────────────────────

        async function loadPromptTemplates() {
            // Loaded once on mount. Templates rarely change during a session,
            // so no need to refetch unless the admin edits one.
            try {
                const rows = await orm.searchRead(
                    "vibe.prompt.template",
                    [["active", "=", true]],
                    ["name", "category", "prompt", "description", "sequence"],
                    { order: "sequence, category, name" }
                );
                state.promptTemplates = rows;
            } catch (e) {
                console.error("[vibeStore] loadPromptTemplates:", e);
                state.promptTemplates = [];
            }
        }

        return {
            state,
            loadProviderInfo,
            loadConversations,
            loadPromptTemplates,
            newConversation,
            selectConversation,
            archiveConversation,
            sendMessage,
            refineMessage,
            selectModule,
            selectFile,
            saveFile,
        };
    },
};

registry.category("services").add("vibeStore", vibeStoreService);
