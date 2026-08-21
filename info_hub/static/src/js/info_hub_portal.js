(function () {
    function init() {
        const editor = document.getElementById("o_info_portal_editor");
        const searchInput = document.getElementById("o_info_portal_search");
        const saveStatus = document.getElementById("o_info_save_status");
        const headerIconInput = document.getElementById("o_info_portal_header_icon");

        const inviteSearch = document.getElementById("o_portal_invite_search");
        const inviteSuggestions = document.getElementById("o_portal_invite_suggestions");
        const inviteBtn = document.getElementById("o_portal_invite_btn");
        const invitePerm = document.getElementById("o_portal_invite_perm");

        const shareWebToggle = document.getElementById("o_portal_share_web_toggle");
        const shareLinkContainer = document.getElementById("o_portal_share_link_container");
        const shareLinkInput = document.getElementById("o_portal_share_link_input");
        const shareCopyBtn = document.getElementById("o_portal_share_copy_btn");
        const defaultPermissionSelect = document.getElementById("o_portal_default_permission_select");
        const memberPermSelects = document.querySelectorAll(".o_portal_member_perm_select");

        let activeArticleId = null;
        const bodyPanel = document.querySelector(".o_info_portal_body_panel");
        if (bodyPanel) {
            activeArticleId = parseInt(bodyPanel.getAttribute("data-article-id"));
        }

        let selectedPartnerId = null;

        async function jsonRpc(url, params = {}) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: params,
                    }),
                });
                const data = await response.json();
                return data.result;
            } catch (err) {
                console.error("JSON RPC Error:", err);
                return { error: err.message };
            }
        }

        function debounce(func, wait) {
            let timeout;
            return function (...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        }

        if (searchInput) {
            searchInput.addEventListener("input", function (e) {
                const filter = e.target.value.toLowerCase();
                const listItems = document.querySelectorAll(".o_info_portal_list .list-group-item");
                listItems.forEach(item => {
                    const text = item.querySelector(".text-truncate").textContent.toLowerCase();
                    if (text.includes(filter)) {
                        item.classList.remove("d-none");
                    } else {
                        item.classList.add("d-none");
                    }
                });
            });

            searchInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    const searchVal = e.target.value;
                    const url = new URL(window.location.href);
                    url.searchParams.set("search", searchVal);
                    window.location.href = url.toString();
                }
            });
        }

        // Save Function
        async function performSave(bodyFromEditor) {
            if (!activeArticleId) return;
            const saveDiscardWrapper = document.getElementById("o_info_portal_save_discard_wrapper");
            const cloudSaved = document.getElementById("o_info_portal_cloud_saved");

            if (saveStatus) {
                saveStatus.innerHTML = '<i class="oi oi-clock text-warning me-1"></i>Saving...';
                saveStatus.classList.remove("d-none");
            }

            const icon = headerIconInput ? headerIconInput.value : null;

            let body = bodyFromEditor;
            let name = null;
            
            const wysiwyg = window.o_info_portal_editor_instance;
            if (wysiwyg) {
                const el = wysiwyg.editable || wysiwyg.getElContent?.();
                if (el) {
                    body = el.innerHTML;
                    const firstH1 = el.querySelector("h1");
                    name = firstH1 ? firstH1.textContent.trim() || "Untitled" : "Untitled";
                }
            }

            if (!body) {
                if (editor) body = editor.innerHTML;
            }


            const res = await jsonRpc("/info/portal/save", {
                article_id: activeArticleId,
                name: name,
                icon: icon,
                body: body
            });


            if (res && res.success) {
                if (saveStatus) {
                    saveStatus.innerHTML = '<i class="oi oi-check-circle text-success me-1"></i>Saved';
                }
                if (saveDiscardWrapper) saveDiscardWrapper.classList.add("d-none");
                if (cloudSaved) cloudSaved.classList.remove("d-none");

                const sidebarItem = document.querySelector(`.o_info_portal_list [data-article-id="${activeArticleId}"]`);
                if (sidebarItem) {
                    if (icon) sidebarItem.querySelector(".fs-5").textContent = icon;
                    if (name) sidebarItem.querySelector(".text-truncate").textContent = name;
                }
            } else {
                if (saveStatus) {
                    saveStatus.innerHTML = '<i class="oi oi-alert text-danger me-1"></i>Save Failed';
                }
            }
        }

        // Global save trigger for the OWL editor
        window.o_info_portal_trigger_save = performSave;

        function buildTOC() {
            const tocList = document.getElementById("o_portal_toc_list");
            if (!tocList) return;
            tocList.innerHTML = "";

            const editorEl = document.querySelector(".odoo-editor-editable") || document.querySelector(".o_portal_body_readonly");
            if (!editorEl) return;

            const headings = editorEl.querySelectorAll("h1, h2, h3, h4, h5, h6");
            if (headings.length === 0) {
                const emptyLi = document.createElement("li");
                emptyLi.className = "text-muted small ps-3 py-1";
                emptyLi.textContent = "No headings found";
                tocList.appendChild(emptyLi);
                return;
            }

            headings.forEach((heading, idx) => {
                if (!heading.id) {
                    heading.id = "o_portal_heading_" + idx;
                }

                const li = document.createElement("li");
                const level = parseInt(heading.tagName.substring(1));
                li.className = `py-1 ps-${(level - 1) * 2} border-0`;

                const a = document.createElement("a");
                a.href = "#" + heading.id;
                a.className = "text-decoration-none text-dark small d-block text-truncate p-1 rounded";
                a.textContent = heading.textContent.trim();
                a.addEventListener("click", function (e) {
                    e.preventDefault();
                    heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });

                li.appendChild(a);
                tocList.appendChild(li);
            });
        }

        // Initialize TOC on start
        setTimeout(buildTOC, 500);

        // Manual Save / Discard Button bindings (using robust event delegation)
        document.addEventListener("click", function (e) {
            const saveBtn = e.target.closest("#o_info_portal_save_btn");
            const discardBtn = e.target.closest("#o_info_portal_discard_btn");
            if (saveBtn) {
                e.preventDefault();
                performSave();
            }
            if (discardBtn) {
                e.preventDefault();
                window.location.reload();
            }

            // Table of Contents Toggle
            const tocBtn = e.target.closest("#o_portal_toc_btn");
            if (tocBtn) {
                e.preventDefault();
                const tocPanel = document.getElementById("o_portal_toc_panel");
                if (tocPanel) {
                    tocPanel.classList.toggle("d-none");
                    if (!tocPanel.classList.contains("d-none")) {
                        buildTOC();
                    }
                }
            }

            // Table of Contents Close
            const tocCloseBtn = e.target.closest("#o_portal_toc_close_btn");
            if (tocCloseBtn) {
                e.preventDefault();
                const tocPanel = document.getElementById("o_portal_toc_panel");
                if (tocPanel) {
                    tocPanel.classList.add("d-none");
                }
            }

            // Favorite Button Toggle
            const favoriteBtn = e.target.closest("#o_portal_favorite_btn");
            if (favoriteBtn) {
                e.preventDefault();
                const isFav = favoriteBtn.classList.contains("o_info_hub_active");
                const newFav = !isFav;
                jsonRpc("/info/portal/toggle_favorite", {
                    article_id: activeArticleId,
                    favorite: newFav
                }).then(res => {
                    if (res && res.success) {
                        window.location.reload();
                    }
                });
            }

            // Lock Content Toggle
            const lockBtn = e.target.closest("#o_portal_lock_btn");
            if (lockBtn) {
                e.preventDefault();
                const icon = lockBtn.querySelector("i");
                const isLocked = icon && icon.classList.contains("fa-lock");
                jsonRpc("/info/portal/toggle_locked", {
                    article_id: activeArticleId,
                    locked: isLocked
                }).then(res => {
                    if (res && res.success) {
                        window.location.reload();
                    }
                });
            }

            // Full Width Toggle
            const fullWidthBtn = e.target.closest("#o_portal_full_width_btn");
            if (fullWidthBtn) {
                e.preventDefault();
                e.stopPropagation(); // Keep dropdown open for visual feedback
                const pill = fullWidthBtn.querySelector(".o_info_hub_toggle_pill");
                const isFull = pill && pill.classList.contains("o_info_hub_toggle_on");
                const newFull = !isFull;
                jsonRpc("/info/portal/toggle_full_width", {
                    article_id: activeArticleId,
                    full_width: newFull
                }).then(res => {
                    if (res && res.success) {
                        if (pill) {
                            if (newFull) {
                                pill.classList.remove("o_info_hub_toggle_off");
                                pill.classList.add("o_info_hub_toggle_on");
                            } else {
                                pill.classList.remove("o_info_hub_toggle_on");
                                pill.classList.add("o_info_hub_toggle_off");
                            }
                        }
                        const container = document.querySelector(".o_info_hub_editor_container");
                        if (container) {
                            container.classList.toggle("o_info_hub_full_width", newFull);
                        }
                        const content = document.querySelector(".o_info_hub_editor_content");
                        if (content) {
                            content.classList.toggle("o_info_hub_content_full_width", newFull);
                        }
                        const inner = document.querySelector(".o_info_hub_editor_content_inner");
                        if (inner) {
                            inner.classList.toggle("o_info_hub_content_full_width", newFull);
                        }
                    }
                });
            }

            // Remove Icon
            const removeIconBtn = e.target.closest("#o_portal_remove_icon_btn");
            if (removeIconBtn) {
                e.preventDefault();
                jsonRpc("/info/portal/remove_icon", {
                    article_id: activeArticleId
                }).then(res => {
                    if (res && res.success) {
                        window.location.reload();
                    }
                });
            }

            // Add Random Icon
            const addIconBtn = e.target.closest("#o_portal_add_icon_btn");
            if (addIconBtn) {
                e.preventDefault();
                jsonRpc("/info/portal/add_random_icon", {
                    article_id: activeArticleId
                }).then(res => {
                    if (res && res.success) {
                        window.location.reload();
                    }
                });
            }

            // Create a Copy (Duplicate)
            const duplicateBtn = e.target.closest("#o_portal_duplicate_btn");
            if (duplicateBtn) {
                e.preventDefault();
                jsonRpc("/info/portal/duplicate", {
                    article_id: activeArticleId
                }).then(res => {
                    if (res && res.success && res.new_article_id) {
                        window.location.href = "/info/shared?article_id=" + res.new_article_id;
                    }
                });
            }

            // Download PDF
            const pdfBtn = e.target.closest("#o_portal_pdf_btn");
            if (pdfBtn) {
                e.preventDefault();
                const bodyPanel = document.querySelector(".o_info_portal_body_panel");
                if (bodyPanel) {
                    const printContents = bodyPanel.innerHTML;
                    const originalContents = document.body.innerHTML;
                    document.body.innerHTML = `<div class="container py-5">${printContents}</div>`;
                    window.print();
                    document.body.innerHTML = originalContents;
                    window.location.reload();
                }
            }

            // Collapse Sidebar
            const sidebarCollapseBtn = e.target.closest("#o_portal_sidebar_collapse_btn");
            if (sidebarCollapseBtn) {
                e.preventDefault();
                const sidebar = document.querySelector(".o_info_portal_sidebar_container");
                const contentContainer = document.querySelector(".o_info_portal_content_container");
                const expandBtn = document.getElementById("o_portal_sidebar_expand_btn");
                if (sidebar && contentContainer) {
                    sidebar.classList.add("d-none");
                    contentContainer.classList.remove("col-md-9");
                    contentContainer.classList.add("col-md-12");
                    if (expandBtn) expandBtn.classList.remove("d-none");
                }
            }

            // Expand Sidebar
            const sidebarExpandBtn = e.target.closest("#o_portal_sidebar_expand_btn");
            if (sidebarExpandBtn) {
                e.preventDefault();
                const sidebar = document.querySelector(".o_info_portal_sidebar_container");
                const contentContainer = document.querySelector(".o_info_portal_content_container");
                if (sidebar && contentContainer) {
                    sidebar.classList.remove("d-none");
                    contentContainer.classList.remove("col-md-12");
                    contentContainer.classList.add("col-md-9");
                    sidebarExpandBtn.classList.add("d-none");
                }
            }

            // Search Toggle button
            const searchToggleBtn = e.target.closest("#o_portal_search_toggle_btn");
            if (searchToggleBtn) {
                e.preventDefault();
                const searchBar = document.getElementById("o_info_portal_search_bar");
                if (searchBar) {
                    searchBar.classList.toggle("d-none");
                    if (!searchBar.classList.contains("d-none")) {
                        const searchInput = document.getElementById("o_info_portal_search");
                        if (searchInput) searchInput.focus();
                    }
                }
            }
        });

        if (headerIconInput) {
            headerIconInput.addEventListener("input", function () {
                const saveDiscardWrapper = document.getElementById("o_info_portal_save_discard_wrapper");
                const cloudSaved = document.getElementById("o_info_portal_cloud_saved");
                if (saveDiscardWrapper) saveDiscardWrapper.classList.remove("d-none");
                if (cloudSaved) cloudSaved.classList.add("d-none");
                if (saveStatus) saveStatus.classList.add("d-none");
                
                // Update sidebar icon in real time
                const sidebarItem = document.querySelector(`.o_info_portal_list [data-article-id="${activeArticleId}"]`);
                if (sidebarItem) {
                    const iconSpan = sidebarItem.querySelector(".fs-5");
                    if (iconSpan) iconSpan.textContent = headerIconInput.value;
                }
            });
        }

        if (shareWebToggle) {
            shareWebToggle.addEventListener("change", async function (e) {
                const publish = e.target.checked;
                const res = await jsonRpc("/info/portal/toggle_published", {
                    article_id: activeArticleId,
                    publish: publish
                });
                if (res && res.success) {
                    if (publish) {
                        if (shareLinkInput) shareLinkInput.value = res.share_url;
                        if (shareLinkContainer) shareLinkContainer.classList.remove("d-none");
                    } else {
                        if (shareLinkContainer) shareLinkContainer.classList.add("d-none");
                    }
                }
            });
        }

        if (shareCopyBtn && shareLinkInput) {
            shareCopyBtn.addEventListener("click", function () {
                shareLinkInput.select();
                document.execCommand("copy");
                const oldText = shareCopyBtn.textContent;
                shareCopyBtn.textContent = "Copied!";
                setTimeout(() => shareCopyBtn.textContent = oldText, 2000);
            });
        }

        const visibilitySelect = document.getElementById("o_portal_visibility_select");
        const visibilityContainer = document.getElementById("o_portal_visibility_container");

        if (defaultPermissionSelect) {
            defaultPermissionSelect.addEventListener("change", async function (e) {
                const val = e.target.value;
                if (val === 'none') {
                    if (visibilityContainer) visibilityContainer.classList.add("d-none");
                } else {
                    if (visibilityContainer) visibilityContainer.classList.remove("d-none");
                }
                await jsonRpc("/info/portal/update_settings", {
                    article_id: activeArticleId,
                    default_access: val
                });
            });
        }

        if (visibilitySelect) {
            visibilitySelect.addEventListener("change", async function (e) {
                await jsonRpc("/info/portal/update_settings", {
                    article_id: activeArticleId,
                    visibility: e.target.value
                });
            });
        }

        if (inviteSearch) {
            inviteSearch.addEventListener("input", debounce(async function (e) {
                const query = e.target.value;
                if (!query) {
                    if (inviteSuggestions) inviteSuggestions.style.display = "none";
                    return;
                }

                const suggestions = await jsonRpc("/info/portal/search_partners", { q: query });
                if (suggestions && suggestions.length > 0) {
                    if (inviteSuggestions) {
                        inviteSuggestions.innerHTML = "";
                        suggestions.forEach(item => {
                            const btn = document.createElement("button");
                            btn.className = "list-group-item list-group-item-action text-start border-bottom py-2";
                            btn.innerHTML = `<strong class="text-dark">${item.name}</strong> <span class="text-muted small">(${item.email || 'no email'})</span>`;
                            btn.addEventListener("click", function () {
                                inviteSearch.value = item.name;
                                selectedPartnerId = item.id;
                                inviteSuggestions.style.display = "none";
                            });
                            inviteSuggestions.appendChild(btn);
                        });
                        inviteSuggestions.style.display = "block";
                    }
                } else {
                    if (inviteSuggestions) inviteSuggestions.style.display = "none";
                }
            }, 300));

            document.addEventListener("click", function (e) {
                if (inviteSuggestions && !inviteSearch.contains(e.target) && !inviteSuggestions.contains(e.target)) {
                    inviteSuggestions.style.display = "none";
                }
            });
        }

        if (inviteBtn) {
            inviteBtn.addEventListener("click", async function () {
                if (!selectedPartnerId || !activeArticleId) {
                    alert("Please select a partner from the suggestion list first.");
                    return;
                }
                const res = await jsonRpc("/info/portal/invite", {
                    article_id: activeArticleId,
                    partner_id: selectedPartnerId,
                    permission: invitePerm ? invitePerm.value : "read"
                });

                if (res && res.success) {
                    window.location.reload();
                } else {
                    alert(res && res.error ? res.error : "Invitation failed.");
                }
            });
        }

        memberPermSelects.forEach(select => {
            select.addEventListener("change", async function (e) {
                const partnerId = parseInt(e.target.getAttribute("data-partner-id"));
                const perm = e.target.value;
                const res = await jsonRpc("/info/portal/invite", {
                    article_id: activeArticleId,
                    partner_id: partnerId,
                    permission: perm
                });
                if (res && res.success) {
                    window.location.reload();
                } else {
                    alert(res && res.error ? res.error : "Failed to update permission.");
                }
            });
        });

        // Drag and Drop Sidebar Reordering / Category Moving
        let draggedArticleId = null;
        let draggedEl = null;

        const sidebarLists = document.querySelectorAll(".o_info_portal_list");
        sidebarLists.forEach(list => {
            const listItems = list.querySelectorAll("[draggable='true']");
            
            listItems.forEach(item => {
                item.addEventListener("dragstart", function (e) {
                    draggedArticleId = parseInt(this.getAttribute("data-article-id"));
                    draggedEl = this;
                    e.dataTransfer.effectAllowed = "move";
                    e.dataTransfer.setData("text/plain", draggedArticleId);
                    this.classList.add("o_info_hub_dragging");
                });

                item.addEventListener("dragend", function (e) {
                    this.classList.remove("o_info_hub_dragging");
                    document.querySelectorAll(".o_info_hub_drop_above, .o_info_hub_drop_below").forEach(el => {
                        el.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below");
                    });
                    draggedArticleId = null;
                    draggedEl = null;
                });

                item.addEventListener("dragover", function (e) {
                    e.preventDefault();
                    if (draggedEl === this) return;

                    const rect = this.getBoundingClientRect();
                    const midY = rect.top + rect.height / 2;
                    if (e.clientY < midY) {
                        this.classList.add("o_info_hub_drop_above");
                        this.classList.remove("o_info_hub_drop_below");
                    } else {
                        this.classList.add("o_info_hub_drop_below");
                        this.classList.remove("o_info_hub_drop_above");
                    }
                });

                item.addEventListener("dragleave", function (e) {
                    this.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below");
                });

                item.addEventListener("drop", async function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const targetArticleId = parseInt(this.getAttribute("data-article-id"));
                    if (draggedArticleId === targetArticleId) return;

                    const targetCategory = this.closest(".o_info_portal_list").getAttribute("data-category");
                    const position = this.classList.contains("o_info_hub_drop_above") ? "before" : "after";

                    this.classList.remove("o_info_hub_drop_above", "o_info_hub_drop_below");

                    const res = await jsonRpc("/info/portal/move_article", {
                        article_id: draggedArticleId,
                        target_category: targetCategory,
                        target_article_id: targetArticleId,
                        position: position
                    });

                    if (res && res.success) {
                        window.location.reload();
                    } else if (res && res.error) {
                        alert(res.error);
                    }
                });
            });

            // Allow dropping in empty/any part of list container
            list.addEventListener("dragover", function (e) {
                e.preventDefault();
            });

            list.addEventListener("drop", async function (e) {
                // If dropped directly on the container (e.g. empty list or end of list)
                if (e.target.closest("[draggable='true']")) return; // handled by the item drop listener

                e.preventDefault();
                const targetCategory = this.getAttribute("data-category");
                const res = await jsonRpc("/info/portal/move_article", {
                    article_id: draggedArticleId,
                    target_category: targetCategory
                });

                if (res && res.success) {
                    window.location.reload();
                } else if (res && res.error) {
                    alert(res.error);
                }
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
