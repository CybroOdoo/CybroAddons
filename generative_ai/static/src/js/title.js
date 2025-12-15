/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SnippetViewer } from "@html_builder/snippets/snippet_viewer";

/**
 * Patch SnippetViewer to:
 * - add custom tooltip on hover showing snippet name
 */
patch(SnippetViewer.prototype, {
    setup() {
        super.setup.call(this);
        this.currentInsertSnippetsCallID = this.currentInsertSnippetsCallID || 0;
    },

    async insertSnippets() {
        if (!this.props?.snippetModel?.snippets) {
            return;
        }
        const insertSnippetsCallID = ++this.currentInsertSnippetsCallID;
        let snippetsToDisplay = [...this.props.snippetModel.snippets.values()].filter(snippet => {
            return !snippet.excluded && snippet.group;
        });
        if (this.state.search) {
            const search = this.state.search;
            const selectorSearch = /^s_[\w-]*$/.test(search) && `[class^="${search}"], [class*=" ${search}"]`;
            const lowerCasedSearch = search.toLowerCase();
            const strMatches = str => str.toLowerCase().includes(lowerCasedSearch);
            snippetsToDisplay = snippetsToDisplay.filter(snippet => {
                return selectorSearch && (
                        snippet.baseBody.matches(selectorSearch)
                        || snippet.baseBody.querySelector(selectorSearch)
                    )
                    || strMatches(snippet.category?.text || '')
                    || strMatches(snippet.displayName || '')
                    || strMatches(snippet.data?.oeKeywords || '');
            });
            if (selectorSearch) {
                snippetsToDisplay.sort((snippetA, snippetB) => {
                    if (snippetA.data?.snippet === search) {
                        return -1;
                    }
                    if (snippetB.data?.snippet === search) {
                        return 1;
                    }
                    const aHasExactClassOnRoot = snippetA.baseBody.classList.contains(search);
                    const bHasExactClassOnRoot = snippetB.baseBody.classList.contains(search);
                    if (aHasExactClassOnRoot !== bHasExactClassOnRoot) {
                        return aHasExactClassOnRoot ? -1 : 1;
                    }
                    const aHasPartialClassOnRoot = snippetA.baseBody.matches(selectorSearch);
                    const bHasPartialClassOnRoot = snippetB.baseBody.matches(selectorSearch);
                    if (aHasPartialClassOnRoot !== bHasPartialClassOnRoot) {
                        return aHasPartialClassOnRoot ? -1 : 1;
                    }
                    return 0;
                });
            }
        } else {
            snippetsToDisplay = snippetsToDisplay.filter(snippet => {
                return snippet.group === this.state.groupSelected;
            });
        }
        const iframeDocument = this.iframeDocument;
        iframeDocument.body.scrollTop = 0;
        const rowEl = document.createElement("div");
        rowEl.classList.add("row", "g-0", "o_snippets_preview_row");
        rowEl.style.setProperty("direction", this.props.frontendDirection || 'ltr');
        const leftColEl = document.createElement("div");
        leftColEl.classList.add("col-lg-6");
        rowEl.appendChild(leftColEl);
        const rightColEl = document.createElement("div");
        rightColEl.classList.add("col-lg-6");
        rowEl.appendChild(rightColEl);
        iframeDocument.body.appendChild(rowEl);
        const BIG_CHUNK_SIZE = 6;
        const SMALL_CHUNK_SIZE = 3;
        const chunks = [snippetsToDisplay.splice(0, BIG_CHUNK_SIZE)];
        while (snippetsToDisplay.length) {
            chunks.push(snippetsToDisplay.splice(0, SMALL_CHUNK_SIZE));
        }
        let leftColSize = 0;
        let rightColSize = 0;
        for (const chunk of chunks) {
            const itemEls = await Promise.all(chunk.map(snippet => {
                let containerEl = null;
                let clonedSnippetEl;
                let originalSnippet;
                if (snippet.isCustom) {
                    originalSnippet = [...this.props.snippetModel.snippets.values()].filter(snip =>
                        !snip.isCustom && snip.name === snippet.name
                    )[0];
                    if (originalSnippet && (
                        originalSnippet.baseBody.querySelector(".s_dialog_preview")
                        || originalSnippet.imagePreview
                        || originalSnippet.name === "s_countdown"
                    )) {
                        clonedSnippetEl = originalSnippet.baseBody.cloneNode(true);
                    }
                }
                if (!clonedSnippetEl) {
                    clonedSnippetEl = snippet.baseBody.cloneNode(true);
                }
                clonedSnippetEl.classList.remove("oe_snippet_body");
                const snippetPreviewWrapEl = document.createElement("div");
                snippetPreviewWrapEl.classList.add("o_snippet_preview_wrap", "position-relative");
                snippetPreviewWrapEl.dataset.snippetId = snippet.name;
                snippetPreviewWrapEl.dataset.snippetKey = snippet.key;
                snippetPreviewWrapEl.dataset.snippetName = snippet.displayName || '';
                snippetPreviewWrapEl.appendChild(clonedSnippetEl);
                this.__onSnippetPreviewClick = this._onSnippetPreviewClick?.bind(this) || (() => this.props.selectSnippet?.(snippet));
                snippetPreviewWrapEl.addEventListener("click", this.__onSnippetPreviewClick);
                snippetPreviewWrapEl.addEventListener("mouseenter", this.__onSnippetPreviewHover.bind(this));
                containerEl = snippetPreviewWrapEl;
                if (snippet.installable) {
                    snippetPreviewWrapEl.classList.add("o_snippet_preview_install");
                    clonedSnippetEl.dataset.moduleId = snippet.moduleId;
                    const installBtnEl = document.createElement("button");
                    installBtnEl.classList.add("o_snippet_preview_install_btn", "btn", "text-white", "rounded-1", "mx-auto", "p-2", "bottom-50");
                    installBtnEl.innerText = _t("Install %s", snippet.displayName || '');
                    snippetPreviewWrapEl.appendChild(installBtnEl);
                }
                const imagePreview = snippet.imagePreview || originalSnippet?.imagePreview;
                if (imagePreview && imagePreview !== 'placeholder.png' && imagePreview !== '/web/static/img/placeholder.png') {
                    try {
                        new URL(imagePreview); // Validate URL
                        clonedSnippetEl.style.setProperty("padding", "0", "important");
                        const previewImgDivEl = document.createElement("div");
                        previewImgDivEl.classList.add("s_dialog_preview", "s_dialog_preview_image");
                        const previewImgEl = document.createElement("img");
                        previewImgEl.src = imagePreview;
                        previewImgDivEl.appendChild(previewImgEl);
                        clonedSnippetEl.innerHTML = "";
                        clonedSnippetEl.appendChild(previewImgDivEl);
                    } catch (e) {
                        console.warn(`Invalid image_preview URL for snippet ${snippet.name}: ${imagePreview}, using fallback`); // Debug
                        clonedSnippetEl.style.setProperty("padding", "0", "important");
                        const previewImgDivEl = document.createElement("div");
                        previewImgDivEl.classList.add("s_dialog_preview", "s_dialog_preview_image");
                        const previewImgEl = document.createElement("img");
                        previewImgEl.src = '/generative_ai/static/src/img/placeholder.png'; // Fallback
                        previewImgDivEl.appendChild(previewImgEl);
                        clonedSnippetEl.innerHTML = "";
                        clonedSnippetEl.appendChild(previewImgDivEl);
                    }
                }
                clonedSnippetEl.classList.remove("o_dynamic_empty");
                if (snippet.isCustom) {
                    const editCustomSnippetEl = document.createElement("div");
                    editCustomSnippetEl.classList.add("d-grid", "mt-2", "mx-5", "gap-2", "d-md-flex", "justify-content-md-end", "o_custom_snippet_edit");
                    const spanEl = document.createElement("span");
                    spanEl.classList.add("w-100");
                    spanEl.textContent = snippet.displayName || '';
                    const renameBtnEl = document.createElement("button");
                    renameBtnEl.classList.add("btn", "fa", "fa-pencil", "me-md-2");
                    renameBtnEl.type = "button";
                    const removeBtnEl = document.createElement("button");
                    removeBtnEl.classList.add("btn", "fa", "fa-trash");
                    removeBtnEl.type = "button";
                    editCustomSnippetEl.appendChild(spanEl);
                    editCustomSnippetEl.appendChild(renameBtnEl);
                    editCustomSnippetEl.appendChild(removeBtnEl);
                    const customSnippetWrapEl = document.createElement("div");
                    customSnippetWrapEl.classList.add("o_custom_snippet_wrap");
                    customSnippetWrapEl.appendChild(snippetPreviewWrapEl);
                    customSnippetWrapEl.appendChild(editCustomSnippetEl);
                    containerEl = customSnippetWrapEl;
                    this.__onRenameCustomBtnClick = this._onRenameCustomBtnClick?.bind(this) || (() => {});
                    renameBtnEl.addEventListener("click", this.__onRenameCustomBtnClick);
                    this.__onDeleteCustomBtnClick = this._onDeleteCustomBtnClick?.bind(this) || (() => {});
                    removeBtnEl.addEventListener("click", this.__onDeleteCustomBtnClick);
                }
                containerEl.classList.add("invisible");
                leftColEl.appendChild(containerEl);
                const imageEls = snippetPreviewWrapEl.querySelectorAll("img");
                return Promise.all(Array.from(imageEls).map(imgEl => {
                    imgEl.setAttribute("loading", "eager");
                    return new Promise(resolve => {
                        if (imgEl.complete) {
                            resolve();
                        } else {
                            imgEl.onload = () => resolve();
                            imgEl.onerror = () => {
                                console.warn(`Failed to load image: ${imgEl.src}, using fallback`); // Debug
                                imgEl.src = '/generative_ai/static/src/img/placeholder.png'; // Fallback
                                resolve();
                            };
                        }
                    });
                })).then(() => containerEl);
            }));
            if (this.currentInsertSnippetsCallID !== insertSnippetsCallID) {
                return;
            }
            const leftColElements = [];
            const rightColElements = [];
            for (const itemEl of itemEls) {
                const size = itemEl.getBoundingClientRect().height;
                if (leftColSize <= rightColSize) {
                    leftColElements.push(itemEl);
                    leftColSize += size;
                } else {
                    rightColElements.push(itemEl);
                    rightColSize += size;
                }
            }
            for (const [colEl, colItemEls] of [
                [leftColEl, leftColElements],
                [rightColEl, rightColElements],
            ]) {
                for (const el of colItemEls) {
                    colEl.appendChild(el);
                    el.classList.remove("invisible");
                }
            }
            while (rowEl.previousSibling) {
                rowEl.previousSibling.remove();
            }
        }
    },

    __onSnippetPreviewHover(ev) {
        const previewEl = ev.currentTarget;
        const title = previewEl.firstElementChild?.getAttribute("title") || previewEl.dataset.snippetName || '';
        if (!title || previewEl.querySelector(".snippet-hover-title-tooltip")) {
            return;
        }
        const tooltip = document.createElement("div");
        tooltip.className = "snippet-hover-title-tooltip position-absolute top-0 start-50 translate-middle-x bg-dark text-white px-5 py-3 rounded shadow-lg";
        Object.assign(tooltip.style, {
            zIndex: "1000",
            pointerEvents: "none",
            fontSize: "2rem",
            fontWeight: "900",
            border: "2px solid white",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
        });
        tooltip.textContent = title;
        previewEl.appendChild(tooltip);
        const removeTooltip = () => {
            tooltip.remove();
            previewEl.removeEventListener("mouseleave", removeTooltip);
        };
        previewEl.addEventListener("mouseleave", removeTooltip, { once: true });
    }
});