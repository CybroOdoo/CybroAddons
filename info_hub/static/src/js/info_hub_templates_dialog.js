/** @odoo-module **/

import { Component, useState, onMounted, markup } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class BrowseTemplatesPreviewDialog extends Component {
    static template = "info_hub.BrowseTemplatesPreviewDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        preview: { type: Object },
        onUseTemplate: { type: Function },
        isApplyOnly: { type: Boolean, optional: true },
        onEditTemplate: { type: Function, optional: true },
        onDeleteTemplate: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            selectedCategory: "workspace",
            loading: false,
        });
    }

    get renderedBody() {
        return this.props.preview.body ? markup(this.props.preview.body) : "";
    }

    onCategoryChange(ev) {
        this.state.selectedCategory = ev.target.value;
    }

    async useTemplate() {
        if (!this.props.isApplyOnly && !this.state.selectedCategory) {
            this.notification.add("Please select a target category.", { type: "warning" });
            return;
        }
        await this.props.onUseTemplate(this.state.selectedCategory);
        this.props.close();
    }

    async editTemplate() {
        if (this.props.onEditTemplate) {
            await this.props.onEditTemplate();
        }
        this.props.close();
    }

    deleteTemplate() {
        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete Template"),
            body: _t("Are you sure you want to delete this template? This will move it to the trash."),
            confirmLabel: _t("Delete"),
            confirm: async () => {
                this.state.loading = true;
                try {
                    await this.orm.call("info.hub.article", "action_archive", [[this.props.preview.id]]);
                    if (this.props.onDeleteTemplate) {
                        await this.props.onDeleteTemplate();
                    }
                    this.props.close();
                } catch (error) {
                    console.error("Failed to delete template:", error);
                    this.notification.add("Failed to move template to trash.", { type: "danger" });
                } finally {
                    this.state.loading = false;
                }
            },
            cancel: () => {},
        });
    }
}

/**
 * Dialog for browsing and applying info article templates.
 */
export class BrowseTemplatesDialog extends Component {
    static template = "info_hub.BrowseTemplatesDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onTemplateSelected: { type: Function, optional: true },
        onTemplateApplied: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            categories: [],
            templates: [],
            selectedCategoryId: null,
            searchQuery: "",
            loading: true,
        });

        onMounted(() => {
            this._loadData();
        });
    }

    async _loadData() {
        try {
            const [categories, templates] = await Promise.all([
                this.orm.searchRead(
                    "info.hub.template.category",
                    [],
                    ["id", "name", "icon"],
                    { order: "sequence asc, id asc" }
                ),
                this.orm.searchRead(
                    "info.hub.article",
                    [["is_template", "=", true]],
                    ["id", "name", "icon", "template_category_id", "template_description", "template_sequence"],
                    { order: "template_sequence asc, id asc" }
                ),
            ]);
            this.state.categories = categories;
            this.state.templates = templates;
        } catch (error) {
            console.error("Failed to load template gallery data:", error);
            this.notification.add("Failed to load templates metadata.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    get filteredTemplates() {
        const query = this.state.searchQuery.toLowerCase().trim();
        const catId = this.state.selectedCategoryId;

        return this.state.templates.filter((t) => {
            const matchesCategory = !catId || (t.template_category_id && t.template_category_id[0] === catId);
            const matchesSearch = !query ||
                t.name.toLowerCase().includes(query) ||
                (t.template_description && t.template_description.toLowerCase().includes(query));
            return matchesCategory && matchesSearch;
        });
    }

    selectCategory(catId) {
        this.state.selectedCategoryId = catId;
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    async onSelectTemplate(templateId) {
        try {
            const previewData = await this.orm.call("info.hub.article", "get_template_preview", [templateId]);
            if (!previewData || !previewData.id) {
                this.notification.add("This template is invalid or no longer exists.", { type: "danger" });
                return;
            }

            this.dialog.add(BrowseTemplatesPreviewDialog, {
                preview: previewData,
                isApplyOnly: !!this.props.onTemplateApplied,
                onUseTemplate: async (category) => {
                    try {
                        if (this.props.onTemplateApplied) {
                            await this.props.onTemplateApplied(templateId);
                        } else {
                            const newArticleId = await this.orm.call(
                                "info.hub.article",
                                "create_article_from_template",
                                [templateId, category]
                            );
                            if (this.props.onTemplateSelected) {
                                await this.props.onTemplateSelected(newArticleId);
                            }
                        }
                        this.props.close();
                    } catch (err) {
                        const errorMsg = err.message || err.data?.message || "Verify your workspace permissions.";
                        this.notification.add("Permission denied or failed to process template: " + errorMsg, { type: "danger" });
                    }
                },
                onEditTemplate: this.props.onTemplateSelected ? async () => {
                    await this.props.onTemplateSelected(templateId);
                    this.props.close();
                } : undefined,
                onDeleteTemplate: async () => {
                    await this._loadData();
                }
            });
        } catch (err) {
            this.notification.add("Could not fetch template details. Ensure you have appropriate access.", { type: "danger" });
        }
    }
}

/**
 * Dialog for configuring and inserting an embedded list view block.
 */
export class InsertListViewDialog extends Component {
    static template = "info_hub.InsertListViewDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onInsert: { type: Function },
        itemName: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            itemName: this.props.itemName || "",
        });
    }

    insert() {
        const name = this.state.itemName.trim() || "Todos";
        this.props.onInsert(name);
        this.props.close();
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.insert();
        }
    }
}

/**
 * Dialog for configuring and inserting an embedded Kanban view block.
 */
export class InsertKanbanViewDialog extends Component {
    static template = "info_hub.InsertKanbanViewDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onInsert: { type: Function },
    };

    setup() {
        this.state = useState({
            itemName: "",
        });
    }

    onInsertClick() {
        const name = this.state.itemName.trim() || "Items";
        this.props.onInsert(name);
        this.props.close();
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onInsertClick();
        }
    }
}

/**
 * Dialog for configuring and inserting an embedded calendar view block.
 */
export class InsertCalendarViewDialog extends Component {
    static template = "info_hub.InsertCalendarViewDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onInsert: { type: Function },
        itemName: { type: String, optional: true },
        scale: { type: String, optional: true },
        showWeekends: { type: Boolean, optional: true },
        isAdvancedMode: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({
            itemName: this.props.itemName || "",
            scale: this.props.scale || "week",
            showWeekends: this.props.showWeekends !== undefined ? this.props.showWeekends : true,
            startHour: "12:00 am",
            endHour: "--:--",
        });
    }

    insert() {
        const name = this.state.itemName.trim() || "Meetings";
        this.props.onInsert({
            itemName: name,
            scale: this.state.scale || "week",
            showWeekends: this.state.showWeekends !== undefined ? this.state.showWeekends : true,
        });
        this.props.close();
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.insert();
        }
    }
}

/**
 * Dialog that shows the version history of an article and allows restoring a previous body snapshot.
 */
export class InfoArticleVersionHistoryDialog extends Component {
    static template = "info_hub.InfoArticleVersionHistoryDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        articleId: { type: Number },
        currentBody: { type: String },
        onRestore: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            versions: [],
            selectedVersionId: null,
            loading: true,
            showComparison: true,
        });

        onMounted(() => {
            this._loadVersions();
        });
    }

    async _loadVersions() {
        try {
            const versions = await this.orm.searchRead(
                "info.hub.article.version",
                [["article_id", "=", this.props.articleId]],
                ["id", "body", "create_uid", "create_date"],
                { order: "create_date desc, id desc" }
            );
            this.state.versions = versions;
            if (versions.length > 0) {
                this.state.selectedVersionId = versions[0].id;
            }
        } catch (error) {
            console.error("Failed to load versions:", error);
            this.notification.add("Failed to load version history.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    get selectedVersion() {
        return this.state.versions.find((v) => v.id === this.state.selectedVersionId) || null;
    }

    get latestVersion() {
        return this.state.versions[0] || null;
    }

    _maskDynamicElements(html) {
        if (!html) return "";
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const selectors = [
            '[data-embedded="view"]',
            '[data-embedded="kanban"]',
            '[data-embedded="info_list"]',
            '[data-embedded="info_calendar"]',
            '[data-embedded="articleIndex"]',
            '[data-embedded="tableOfContent"]',
            '[data-embedded="file"]',
            '.o_info_embedded_kanban',
            '.o_info_kanban_block',
            '.o_info_list_host',
            '.o_info_calendar_host',
            '.o_file_box'
        ];
        const targets = doc.querySelectorAll(selectors.join(','));
        targets.forEach(el => {
            const placeholder = doc.createElement("div");
            placeholder.className = "o_info_hub_history_dynamic_placeholder";
            placeholder.innerHTML = `
                <div class="o_info_hub_placeholder_glow"></div>
                <div class="o_info_hub_placeholder_content">
                    <div class="o_info_hub_placeholder_icon_wrapper">
                        <i class="fa fa-puzzle-piece"></i>
                    </div>
                    <div class="o_info_hub_placeholder_text_wrapper">
                        <span class="o_info_hub_placeholder_title">Dynamic Element</span>
                        <span class="o_info_hub_placeholder_subtitle">Non-editable preview block</span>
                    </div>
                </div>
            `;
            el.replaceWith(placeholder);
        });
        return doc.body.innerHTML;
    }

    get displayedBody() {
        const selected = this.selectedVersion;
        if (!selected) return markup("");

        const selectedBodyMasked = this._maskDynamicElements(selected.body || "");

        if (!this.state.showComparison) {
            return markup(selectedBodyMasked);
        }

        const currentBodyMasked = this._maskDynamicElements(this.props.currentBody || "");
        const diffHtml = renderHtmlDiff(selectedBodyMasked, currentBodyMasked);
        return markup(diffHtml);
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr + "Z");
        if (isNaN(date.getTime())) return dateStr;

        const pad = (n) => String(n).padStart(2, '0');

        const month = pad(date.getMonth() + 1);
        const day = pad(date.getDate());
        const year = date.getFullYear();

        let hours = date.getHours();
        const minutes = pad(date.getMinutes());
        const seconds = pad(date.getSeconds());
        const ampm = hours >= 12 ? 'PM' : 'AM';

        hours = hours % 12;
        hours = hours ? hours : 12;
        const formattedHours = pad(hours);

        return `${month}/${day}/${year} ${formattedHours}:${minutes}:${seconds} ${ampm}`;
    }

    selectVersion(versionId) {
        this.state.selectedVersionId = versionId;
    }

    toggleComparison() {
        this.state.showComparison = !this.state.showComparison;
    }

    async restore() {
        const selected = this.selectedVersion;
        if (!selected) return;

        try {
            this.state.loading = true;
            await this.orm.write("info.hub.article", [this.props.articleId], {
                body: selected.body || "",
            });
            await this.props.onRestore(selected.body || "");
            this.props.close();
        } catch (error) {
            console.error("Failed to restore article:", error);
            this.notification.add("Failed to restore article.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }
}

function diffTokens(oldTokens, newTokens) {
    if (oldTokens.length * newTokens.length > 2000000) {
        return oldTokens.map(t => ({ type: 'equal', value: t }));
    }
    const dp = Array(oldTokens.length + 1).fill(null).map(() => Array(newTokens.length + 1).fill(0));
    for (let i = 1; i <= oldTokens.length; i++) {
        for (let j = 1; j <= newTokens.length; j++) {
            if (oldTokens[i - 1] === newTokens[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    const result = [];
    let i = oldTokens.length;
    let j = newTokens.length;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && oldTokens[i - 1] === newTokens[j - 1]) {
            result.unshift({ type: 'equal', value: oldTokens[i - 1] });
            i--;
            j--;
        } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
            result.unshift({ type: 'insert', value: newTokens[j - 1] });
            j--;
        } else {
            result.unshift({ type: 'delete', value: oldTokens[i - 1] });
            i--;
        }
    }
    return result;
}

function renderHtmlDiff(oldHtml, newHtml) {
    const tokenRegex = /<[^>]+>|[^<>\s]+|\s+/g;
    const oldTokens = oldHtml.match(tokenRegex) || [];
    const newTokens = newHtml.match(tokenRegex) || [];

    const diff = diffTokens(oldTokens, newTokens);

    let rendered = "";
    for (const token of diff) {
        const val = token.value;
        const isTag = val.startsWith('<') && val.endsWith('>');

        if (isTag) {
            rendered += val;
        } else {
            if (token.type === 'equal') {
                rendered += val;
            } else if (token.type === 'insert') {
                rendered += `<ins>${val}</ins>`;
            } else if (token.type === 'delete') {
                rendered += `<del>${val}</del>`;
            }
        }
    }
    return rendered;
}
