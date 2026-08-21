/** @odoo-module **/

import { mountComponent } from "@web/env";
import { Component, xml, markup } from "@odoo/owl";
import { Wysiwyg } from "@html_editor/wysiwyg";
import { MainComponentsContainer } from "@web/core/main_components_container";
import { MAIN_PLUGINS, EMBEDDED_COMPONENT_PLUGINS } from "@html_editor/plugin_sets";
import { MAIN_EMBEDDINGS } from "@html_editor/others/embedded_components/embedding_sets";
import { FoldableSectionPlugin } from "./foldable_section_plugin";
import { ClipboardPluginCommunity } from "./clipboard_plugin";
import { registry } from "@web/core/registry";


// Odoo 19 frontend excludes core/commands service from web.assets_frontend.
// We register a mock command service if missing to prevent crashes.
if (!registry.category("services").contains("command")) {
    registry.category("services").add("command", {
        start() {
            return {
                openMainPalette() {},
                openPalette() {},
                getCommands() { return []; },
                add(name, action, options = {}) {
                    return () => {}; // return cleanup function
                },
            };
        }
    });
}

export class PortalEditor extends Component {
    static template = xml`
        <div class="o_info_portal_wysiwyg_container position-relative w-100">
            <Wysiwyg config="editorConfig" onLoad.bind="onEditorLoad" contentClass="'o_info_hub_body'" />
            <MainComponentsContainer />
        </div>
    `;
    static components = { Wysiwyg, MainComponentsContainer };

    setup() {
        this.editorConfig = {
            content: this.props.initialContent ? markup(this.props.initialContent) : "",
            Plugins: [
                ...MAIN_PLUGINS,
                ...EMBEDDED_COMPONENT_PLUGINS,
                FoldableSectionPlugin,
                ClipboardPluginCommunity,
            ],
            embeddedComponentInfo: {
                app: this.__owl__.app,
                env: this.env,
            },
            resources: {
                embedded_components: MAIN_EMBEDDINGS,
            },
            getRecordInfo: () => {
                return {
                    resModel: "info.hub.article",
                    resId: this.props.articleId,
                    field: "body",
                    type: "html",
                };
            },
            onChange: () => {
                if (this.editor) {
                    const el = this.editor.editable || this.editor.getElContent?.();
                    if (el) {
                        const newContent = el.innerHTML;
                        if (this.props.onChange) {
                            this.props.onChange(newContent);
                        }
                    }
                }
            }
        };
    }

    onEditorLoad(editor) {
        this.editor = editor;
        window.o_info_portal_editor_instance = editor;

        setTimeout(() => {
            const el = editor.editable;
            if (el) {
                const doc = el.ownerDocument;
                const enforceTitleBlock = () => {
                    const firstBlock = el.firstElementChild;
                    if (!firstBlock || firstBlock.tagName !== "H1") {
                        if (firstBlock && ["P", "DIV", "H2", "H3", "H4", "H5", "H6"].includes(firstBlock.tagName)) {
                            const h1 = doc.createElement("h1");
                            h1.innerHTML = firstBlock.innerHTML;
                            firstBlock.replaceWith(h1);
                        } else {
                            const h1 = doc.createElement("h1");
                            h1.innerHTML = "<br>";
                            el.insertBefore(h1, el.firstChild);
                        }
                    }
                };

                enforceTitleBlock();

                // Store original title to compare
                const firstH1 = el.querySelector("h1");
                let currentTitle = firstH1 ? firstH1.textContent.trim() : "Untitled";

                // Sync the initial header title text immediately on load
                const headerTitleEl = document.getElementById("o_info_portal_header_title");
                if (headerTitleEl && currentTitle) {
                    headerTitleEl.textContent = currentTitle;
                }

                el.addEventListener("input", () => {
                    enforceTitleBlock();
                    const newH1 = el.querySelector("h1");
                    if (newH1) {
                        const newTitle = newH1.textContent.trim() || "Untitled";
                        if (currentTitle !== newTitle) {
                            currentTitle = newTitle;
                            // Update the portal header title element
                            if (headerTitleEl) {
                                headerTitleEl.textContent = newTitle;
                            }
                            // Update the sidebar list item text
                            const sidebarItem = document.querySelector(`.o_info_portal_list [data-article-id="${this.props.articleId}"]`);
                            if (sidebarItem) {
                                const nameSpan = sidebarItem.querySelector(".text-truncate");
                                if (nameSpan) {
                                    nameSpan.textContent = newTitle;
                                }
                            }
                        }
                    }

                    // Show Save/Discard wrapper and hide Cloud saved indicator
                    const saveDiscardWrapper = document.getElementById("o_info_portal_save_discard_wrapper");
                    const cloudSaved = document.getElementById("o_info_portal_cloud_saved");
                    const saveStatus = document.getElementById("o_info_save_status");
                    if (saveDiscardWrapper) saveDiscardWrapper.classList.remove("d-none");
                    if (cloudSaved) cloudSaved.classList.add("d-none");
                    if (saveStatus) saveStatus.classList.add("d-none");
                });
            }
        }, 50);

        if (this.props.onLoad) {
            this.props.onLoad(editor);
        }
    }
}

function runWhenReady(fn) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
        fn();
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

runWhenReady(() => {
    const mountEl = document.getElementById("o_info_portal_wysiwyg_mount");
    if (mountEl) {
        const valNode = document.getElementById("o_info_portal_editor_value");
        const initialContent = valNode ? valNode.innerHTML : "";
        const bodyPanel = document.querySelector(".o_info_portal_body_panel");
        const articleId = bodyPanel ? parseInt(bodyPanel.getAttribute("data-article-id")) : null;
        mountComponent(PortalEditor, mountEl, {
            props: {
                initialContent: initialContent,
                articleId: articleId,
                onChange: (content) => {
                    if (window.o_info_portal_trigger_save) {
                        window.o_info_portal_trigger_save(content);
                    }
                }
            }
        }).catch((err) => {
            console.error("Failed to mount Portal Odoo Editor:", err);
        });
    }
});
