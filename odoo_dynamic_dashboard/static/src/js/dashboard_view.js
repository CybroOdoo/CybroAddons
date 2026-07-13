/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { View } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { DashboardCardButtons } from "./dashboard_card_buttons";

export class DashboardView extends Component {
    setup() {
        this.JSON = JSON;
        this.actionService = useService("action");
        this.viewService = useService("view");
        this.orm = useService("orm");

        this.state = useState({
            viewProps: null,
            error: null,
            hasRecords: true, // Default to true to avoid flashing empty state while loading
        });

        // Initial load
        onWillStart(async () => {
            await this.updateViewProps(this.props);
        });

        onWillUpdateProps(async (nextProps) => {
            await this.updateViewProps(nextProps);
        });
    }

    get viewProps() {
        return this.state.viewProps;
    }

    get error() {
        return this.state.error;
    }

    async updateViewProps(props) {
        this.state.error = null;
        if (!props.card || !props.card.model_name) {
            this.state.viewProps = null;
            this.state.hasRecords = false;
            return;
        }

        const type = props.card.view_type || 'kanban';
        const domain = this.getDomain(props);



        // Base props
        let viewProps = {
            resModel: props.card.model_name,
            type: type,
            display: {
                controlPanel: false, // This hides the search and breadcrumbs
                searchPanel: false,
            },
            domain: domain,
            context: {
                ...(props.card.context || {}),
                dashboard_custom_filter_domain: props.customFilterDomain,
                dashboard_custom_filter_model: props.customFilterModel,
            },
        };

        if (type === 'hierarchy') {
            try {
                const modelName = props.card.model_name;

                const [result, allFields] = await Promise.all([
                    this.viewService.loadViews({
                        resModel: modelName,
                        views: [[false, 'hierarchy']],
                        context: viewProps.context,
                    }, { loadIrFilters: false }),
                    this.orm.call(modelName, 'fields_get', [], { context: viewProps.context })
                ]);
                const viewInfo = result.views.hierarchy;
                let fields = allFields;
                if (viewInfo.fields) {
                    Object.assign(fields, viewInfo.fields);
                }

                // IMPORTANT: Ensure child_ids field definition exists even if backend doesn't have it
                // This prevents "Field child_ids not found" error during view initialization
                if (!fields.child_ids) {
                    fields.child_ids = {
                        type: 'one2many',
                        relation: modelName,
                        string: 'Children',
                        searchable: false,
                        sortable: false,
                    };
                }

                // Get the arch, whether injected or loaded
                let arch = viewInfo.arch;
                if (!arch || !arch.includes('hierarchy-box')) {
                    arch = `
                        <hierarchy child_field="child_ids">
                            <templates>
                                <t t-name="hierarchy-box">
                                    <div class="o_hierarchy_node_header d-flex flex-column align-items-center justify-content-center p-2" 
                                         style="background-color: white; border: 1px solid #dee2e6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 140px; cursor: pointer;">
                                        <div class="fw-bold text-truncate w-100 text-center text-primary">
                                            <field name="display_name"/>
                                        </div>
                                        <div class="small text-muted mt-1">
                                            <i class="fa fa-info-circle me-1"/>
                                            <span>View Details</span>
                                        </div>
                                    </div>
                                </t>
                            </templates>
                        </hierarchy>
                    `;
                }

                // CRITICAL: Force create="false" to prevent "NEW" button in modal
                // This handles both injected arch and standard arch
                if (arch) {
                    arch = arch.replace(/<hierarchy/i, '<hierarchy create="false" edit="false" delete="false"');
                }

                // Set arch and fields to viewProps
                viewProps.arch = arch;
                viewProps.fields = fields;

                const models = {
                    [modelName]: { fields: fields }
                };
                viewProps.relatedModels = models;
            } catch (e) {
                // Fallback to avoid complete crash
                this.state.error = "Error initializing hierarchy view: " + e.message;
                this.state.viewProps = null;
                return;
            }
        }

        if (['list', 'kanban', 'hierarchy', 'graph', 'pivot', 'calendar'].includes(type) && viewProps.resModel) {
            viewProps.selectRecord = (resId) => this.openFormView(resId);
            viewProps.limit = props.card.record_limit || 10;

            // Explicitly check for records to handle empty state
            try {
                const count = await this.orm.searchCount(viewProps.resModel, viewProps.domain || []);
                this.state.hasRecords = count > 0;
            } catch (e) {
                this.state.hasRecords = false; // Default to false on error to show empty state (or maybe true to safe?)
            }
        } else {
            // For safety, if we can't search (e.g. no model), assume no records
            this.state.hasRecords = false;
        }

        this.state.viewProps = viewProps;
    }

    parseDomain(domainStr) {
        if (!domainStr || domainStr === "" || domainStr === "[]") return [];
        try {
            if (Array.isArray(domainStr)) return domainStr;
            let processed = domainStr
                .replace(/\(/g, '[')
                .replace(/\)/g, ']')
                .replace(/'/g, '"')
                .replace(/True/g, 'true')
                .replace(/False/g, 'false')
                .replace(/None/g, 'null');
            return JSON.parse(processed);
        } catch (e) {
            return [];
        }
    }

    getDomain(props) {
        try {
            let domain = this.parseDomain(props.card.domain);

            // Apply date filter if present
            const dateFilter = props.dateFilter || 'all';

            if (dateFilter !== 'all') {
                const now = new Date();
                let start, end;

                if (dateFilter === 'today') {
                    start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
                    end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                } else if (dateFilter === 'this_week') {
                    const dayOfWeek = now.getDay();
                    const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
                    start = new Date(now.getFullYear(), now.getMonth(), diff, 0, 0, 0);
                    end = new Date(start);
                    end.setDate(start.getDate() + 6);
                    end.setHours(23, 59, 59);
                } else if (dateFilter === 'this_month') {
                    start = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
                } else if (dateFilter === 'this_quarter') {
                    const month = now.getMonth();
                    const quarterStartMonth = Math.floor(month / 3) * 3;
                    start = new Date(now.getFullYear(), quarterStartMonth, 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), quarterStartMonth + 3, 0, 23, 59, 59);
                } else if (dateFilter === 'this_year') {
                    start = new Date(now.getFullYear(), 0, 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), 11, 31, 23, 59, 59);
                } else if (dateFilter === 'custom') {
                    if (props.customStartDate && props.customEndDate) {
                        start = new Date(props.customStartDate);
                        start.setHours(0, 0, 0, 0);
                        end = new Date(props.customEndDate);
                        end.setHours(23, 59, 59);
                    }
                }

                if (start && end) {
                    // Format dates as YYYY-MM-DD HH:MM:SS in local timezone
                    const formatDate = (date) => {
                        const year = date.getFullYear();
                        const month = String(date.getMonth() + 1).padStart(2, '0');
                        const day = String(date.getDate()).padStart(2, '0');
                        const hours = String(date.getHours()).padStart(2, '0');
                        const minutes = String(date.getMinutes()).padStart(2, '0');
                        const seconds = String(date.getSeconds()).padStart(2, '0');
                        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
                    };

                    const dateFilterDomain = [
                        ['create_date', '>=', formatDate(start)],
                        ['create_date', '<=', formatDate(end)]
                    ];
                    domain = domain.concat(dateFilterDomain);
                }
            }

            // Apply custom backend filter if present in props
            const customFilterDomain = props.customFilterDomain;
            const customFilterModel = props.customFilterModel;
            const cardModelId = Array.isArray(props.card.model_id) ? props.card.model_id[0] : props.card.model_id;

            if (customFilterModel) {
                if (Number(customFilterModel) !== Number(cardModelId)) {
                    // Mismatch: Return impossible domain
                    return [['id', '=', -1]];
                }
            }

            if (customFilterDomain) {
                const parsedCustomDomain = this.parseDomain(customFilterDomain);
                if (parsedCustomDomain && parsedCustomDomain.length > 0) {
                    domain = domain.concat(parsedCustomDomain);
                }
            }

            return domain;
        } catch (e) {
            return [];
        }
    }

    openFormView(resId) {
        if (!this.props.card.enable_click || !resId) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: this.props.card.name || this.props.card.model_name,
            res_model: this.props.card.model_name,
            res_id: parseInt(resId),
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

DashboardView.template = "odoo_dynamic_dashboard.DashboardViewCard";
DashboardView.components = { DashboardCardButtons, View };