/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted } from '@odoo/owl';
import { useBus, useService } from '@web/core/utils/hooks';
import { user } from "@web/core/user";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { CardInfoModal } from "./card_info_modal";
export class DashboardCardButtons extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.ui = useService("ui");
        this.state = useState({
            selectedDashboardId: false,
            selectedColor: this.props.card.chart_color
        });
    }
    async onSelectColor(color) {
        await this.orm.write(
            "dashboard.card",
            [this.props.card.id],
            { color_group_id: color }
        );
        this.dashboardUpdated()
    }
    async onApplyColor(ev) {
        await this.orm.write(
            "dashboard.card",
            [this.props.card.id],
            { chart_color: this.state.selectedColor }
        );
        this.dashboardUpdated()
        const dropdownElement = ev.target.closest('.dropdown-menu');
        if (dropdownElement) {
            dropdownElement.classList.remove('show');
        }
        //        const dropdownInstance = bootstrap.Dropdown.getInstance(dropdownElement.querySelector('[data-bs-toggle="dropdown"]'));
        //        if (dropdownInstance) {
        //            dropdownInstance.hide();
        //        }
    }
    onClickCancelColor(ev) {
        this.state.selectedColor = this.props.card.chart_color
        const dropdownElement = ev.target.closest('.dropdown-menu');
        if (dropdownElement) {
            dropdownElement.classList.remove('show');
        }
    }
    async onClickDuplicate(ev) {
        const operationType = ev.currentTarget.dataset.type; // 'move' | 'copy'
        const selectedDashboardId = parseInt(this.state.selectedDashboardId);

        if (!selectedDashboardId) {
            this.notification.add(_t("Please choose the dashboard"), {
                type: "danger",
            });
            return;
        }

        const currentDashboardId = this.props.card.dashboard_menu_id?.[0];

        // 🚫 Prevent moving to same dashboard
        if (
            operationType === "move" &&
            currentDashboardId === selectedDashboardId
        ) {
            this.notification.add(
                _t("You're trying to move the card to the same dashboard"),
                { type: "warning" }
            );
            return;
        }

        if (operationType === "move") {
            // ✅ EXISTING FUNCTIONALITY: write
            await this.orm.write(
                "dashboard.card",
                [this.props.card.id],
                { dashboard_menu_id: selectedDashboardId, gs_x: 0, gs_y: 0 }
            );

            this.notification.add(
                _t("Successfully moved the card"),
                { type: "success" }
            );
        }

        if (operationType === "copy") {
            // ✅ EXISTING FUNCTIONALITY: copy
            await this.orm.call(
                "dashboard.card",
                "copy",
                [this.props.card.id],
                {
                    default: { dashboard_menu_id: selectedDashboardId, gs_x: 0, gs_y: 0 },
                }
            );

            this.notification.add(
                _t("Successfully copied the card"),
                { type: "success" }
            );
        }

        this.action.doAction("soft_reload");
    }
    onClickInfo() {
        this.dialogService.add(CardInfoModal, {
            card: this.props.card,
        });
    }
    async onClickEdit() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Edit Card",
            res_model: "dashboard.card",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            res_id: this.props.card.id,
            context: {
                form_view_ref: "odoo_dynamic_dashboard.dashboard_card_view_form_wizard",
            },
        },
            {
                onClose: async () => {
                    this.dashboardUpdated()
                },
            })
    }
    dashboardUpdated() {
        this.env.bus.trigger('dashboard_card_updated', {
            id: this.props.card.id
        })
    }
    onClickDelete() {
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Confirmation"),
            body: _t("Are you sure you want to delete this card?"),
            confirm: async () => {
                await this.orm.unlink("dashboard.card", [parseInt(this.props.card.id)]);
                this.action.doAction("soft_reload")
            },
            cancel: () => { },
        });
    }

    async onSaveAsImage(ev) {
        ev.preventDefault();

        this.ui.block();

        // Show a loading notification
        this.notification.add(_t("Preparing image..."), {
            type: "info",
        });

        // Use setTimeout to defer heavy processing and prevent UI freeze
        // This allows the browser to render the notification first
        setTimeout(async () => {
            try {
                // Find the card element - look for the parent grid-stack-item
                const cardElement = ev.target.closest('.grid-stack-item');

                if (!cardElement) {
                    this.notification.add(_t("Unable to find card element"), {
                        type: "danger",
                    });
                    return;
                }

                // Load html2canvas library
                let html2canvas;
                try {
                    // Try to load from Odoo's bundled libraries first
                    html2canvas = (await odoo.loader.modules.get('@web/lib/html2canvas/html2canvas')).default;
                } catch (e) {
                    // If not available, load from CDN
                    if (!window.html2canvas) {
                        await new Promise((resolve, reject) => {
                            const script = document.createElement('script');
                            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
                            script.onload = resolve;
                            script.onerror = reject;
                            document.head.appendChild(script);
                        });
                    }
                    html2canvas = window.html2canvas;
                }

                if (!html2canvas) {
                    this.notification.add(_t("Failed to load image capture library"), {
                        type: "danger",
                    });
                    return;
                }

                // Clone the card element for off-screen manipulation
                const clonedCard = cardElement.cloneNode(true);

                // Manually copy canvas contents because cloneNode doesn't copy canvas pixels
                const originalCanvases = cardElement.querySelectorAll('canvas');
                const clonedCanvases = clonedCard.querySelectorAll('canvas');
                originalCanvases.forEach((canvas, index) => {
                    const clonedCanvas = clonedCanvases[index];
                    if (clonedCanvas) {
                        const ctx = clonedCanvas.getContext('2d');
                        ctx.drawImage(canvas, 0, 0);
                    }
                });

                // Style the clone to be positioned off-screen but still rendered
                clonedCard.style.position = 'absolute';
                clonedCard.style.left = '-9999px';
                clonedCard.style.top = '0';
                clonedCard.style.zIndex = '-1';

                // Remove hover actions from clone
                const clonedHoverActions = clonedCard.querySelector('.hover-actions');
                if (clonedHoverActions) {
                    clonedHoverActions.remove();
                }

                // Add clone to document body
                document.body.appendChild(clonedCard);

                // Sanitize content for export (fix unsupported CSS)
                this._sanitizeCloneForExport(clonedCard);

                // Find and expand all scrollable elements in the clone
                const scrollableElements = clonedCard.querySelectorAll('*');
                scrollableElements.forEach((element) => {
                    const computedStyle = window.getComputedStyle(element);

                    // Check if element has overflow or is scrollable
                    if (computedStyle.overflow === 'auto' ||
                        computedStyle.overflow === 'scroll' ||
                        computedStyle.overflow === 'hidden' ||
                        computedStyle.overflowY === 'auto' ||
                        computedStyle.overflowY === 'scroll' ||
                        computedStyle.overflowY === 'hidden' ||
                        computedStyle.overflowX === 'auto' ||
                        computedStyle.overflowX === 'scroll' ||
                        element.scrollHeight > element.clientHeight ||
                        element.scrollWidth > element.clientWidth) {

                        // Expand to show full content
                        element.style.overflow = 'visible';
                        element.style.overflowY = 'visible';
                        element.style.overflowX = 'visible';
                        element.style.height = 'auto';
                        element.style.maxHeight = 'none';
                        element.style.minHeight = element.scrollHeight + 'px';
                    }
                });

                // Wait for layout to stabilize
                await new Promise(resolve => setTimeout(resolve, 300));

                // Capture the cloned card
                const canvas = await html2canvas(clonedCard, {
                    backgroundColor: '#ffffff',
                    scale: 2,
                    logging: false,
                    useCORS: true,
                    allowTaint: true,
                });

                // Remove the clone from DOM
                document.body.removeChild(clonedCard);

                // Convert canvas to blob and download
                canvas.toBlob((blob) => {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    const cardName = this.props.card.name || 'dashboard-card';
                    const fileName = `${cardName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.png`;

                    link.href = url;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);

                    this.notification.add(_t("Image saved successfully"), {
                        type: "success",
                    });
                });

            } catch (error) {
                this.notification.add(_t("Failed to save image: " + error.message), {
                    type: "danger",
                });
            } finally {
                this.ui.unblock();
            }
        }, 50);
    }

    async onSaveAsPDF(ev) {
        ev.preventDefault();

        this.ui.block();

        // Show a loading notification
        this.notification.add(_t("Preparing PDF..."), {
            type: "info",
        });

        // Use setTimeout to defer heavy processing and prevent UI freeze
        setTimeout(async () => {
            try {
                // Find the card element
                const cardElement = ev.target.closest('.grid-stack-item');

                if (!cardElement) {
                    this.notification.add(_t("Unable to find card element"), {
                        type: "danger",
                    });
                    return;
                }

                // Load required libraries
                let html2canvas, jsPDF;

                try {
                    // Try to load html2canvas from Odoo's bundled libraries first
                    html2canvas = (await odoo.loader.modules.get('@web/lib/html2canvas/html2canvas')).default;
                } catch (e) {
                    // If not available, load from CDN
                    if (!window.html2canvas) {
                        await new Promise((resolve, reject) => {
                            const script = document.createElement('script');
                            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
                            script.onload = resolve;
                            script.onerror = reject;
                            document.head.appendChild(script);
                        });
                    }
                    html2canvas = window.html2canvas;
                }

                // Load jsPDF from CDN
                if (!window.jspdf) {
                    await new Promise((resolve, reject) => {
                        const script = document.createElement('script');
                        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                }
                jsPDF = window.jspdf.jsPDF;

                if (!html2canvas || !jsPDF) {
                    this.notification.add(_t("Failed to load required libraries"), {
                        type: "danger",
                    });
                    return;
                }

                // Clone the card element for off-screen manipulation
                const clonedCard = cardElement.cloneNode(true);

                // Manually copy canvas contents because cloneNode doesn't copy canvas pixels
                const originalCanvases = cardElement.querySelectorAll('canvas');
                const clonedCanvases = clonedCard.querySelectorAll('canvas');
                originalCanvases.forEach((canvas, index) => {
                    const clonedCanvas = clonedCanvases[index];
                    if (clonedCanvas) {
                        const ctx = clonedCanvas.getContext('2d');
                        ctx.drawImage(canvas, 0, 0);
                    }
                });

                // Style the clone to be positioned off-screen but still rendered
                clonedCard.style.position = 'absolute';
                clonedCard.style.left = '-9999px';
                clonedCard.style.top = '0';
                clonedCard.style.zIndex = '-1';

                // Remove hover actions from clone
                const clonedHoverActions = clonedCard.querySelector('.hover-actions');
                if (clonedHoverActions) {
                    clonedHoverActions.remove();
                }

                // Add clone to document body
                document.body.appendChild(clonedCard);

                // Sanitize content for export (fix unsupported CSS)
                this._sanitizeCloneForExport(clonedCard);

                // Find and expand all scrollable elements in the clone
                const scrollableElements = clonedCard.querySelectorAll('*');
                scrollableElements.forEach((element) => {
                    const computedStyle = window.getComputedStyle(element);

                    if (computedStyle.overflow === 'auto' ||
                        computedStyle.overflow === 'scroll' ||
                        computedStyle.overflow === 'hidden' ||
                        computedStyle.overflowY === 'auto' ||
                        computedStyle.overflowY === 'scroll' ||
                        computedStyle.overflowY === 'hidden' ||
                        computedStyle.overflowX === 'auto' ||
                        computedStyle.overflowX === 'scroll' ||
                        element.scrollHeight > element.clientHeight ||
                        element.scrollWidth > element.clientWidth) {

                        element.style.overflow = 'visible';
                        element.style.overflowY = 'visible';
                        element.style.overflowX = 'visible';
                        element.style.height = 'auto';
                        element.style.maxHeight = 'none';
                        element.style.minHeight = element.scrollHeight + 'px';
                    }
                });

                // Wait for layout to stabilize
                await new Promise(resolve => setTimeout(resolve, 300));

                // Capture the cloned card as canvas
                const canvas = await html2canvas(clonedCard, {
                    backgroundColor: '#ffffff',
                    scale: 2,
                    logging: false,
                    useCORS: true,
                    allowTaint: true,
                });

                // Remove the clone from DOM
                document.body.removeChild(clonedCard);

                // Convert canvas to PDF
                const imgData = canvas.toDataURL('image/png');
                const imgWidth = canvas.width;
                const imgHeight = canvas.height;

                // Calculate PDF dimensions (A4 size in mm)
                const pdfWidth = 210; // A4 width in mm
                const pdfHeight = (imgHeight * pdfWidth) / imgWidth;

                // Create PDF
                const pdf = new jsPDF({
                    orientation: pdfHeight > pdfWidth ? 'portrait' : 'landscape',
                    unit: 'mm',
                    format: 'a4'
                });

                // Calculate scaling to fit content on page
                const pageWidth = pdf.internal.pageSize.getWidth();
                const pageHeight = pdf.internal.pageSize.getHeight();
                const widthRatio = pageWidth / pdfWidth;
                const heightRatio = pageHeight / pdfHeight;
                const ratio = Math.min(widthRatio, heightRatio);

                const finalWidth = pdfWidth * ratio;
                const finalHeight = pdfHeight * ratio;

                // Center the image on the page
                const xOffset = (pageWidth - finalWidth) / 2;
                const yOffset = (pageHeight - finalHeight) / 2;

                pdf.addImage(imgData, 'PNG', xOffset, yOffset, finalWidth, finalHeight);

                // Generate filename and save
                const cardName = this.props.card.name || 'dashboard-card';
                const fileName = `${cardName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.pdf`;
                pdf.save(fileName);

                this.notification.add(_t("PDF saved successfully"), {
                    type: "success",
                });

            } catch (error) {
                this.notification.add(_t("Failed to save PDF: " + error.message), {
                    type: "danger",
                });
            } finally {
                this.ui.unblock();
            }
        }, 50);
    }

    async onExportItem(ev) {
        const card = this.props.card;
        const exportData = {};

        // Fields to EXCLUDE from export
        const excludeFields = [
            'id', 'dashboard_menu_id', 'create_uid', 'create_date',
            'write_uid', 'write_date', '__last_update', 'model_name',
            'chart_x_axis_data', 'chart_y_axis_data' // computed fields
        ];

        // Serialize fields
        for (const [key, value] of Object.entries(card)) {
            if (!excludeFields.includes(key) && !key.endsWith('_ids')) {
                // Handle Many2one (it's usually [id, name] in JS props)
                if (Array.isArray(value) && value.length === 2) {
                    exportData[key] = value[0];
                } else {
                    exportData[key] = value;
                }
            }
        }

        // Fetch and Serialize One2many fields (Table Field Lines and Todos)
        if (card.table_field_line_ids && card.table_field_line_ids.length > 0) {
            const tableFields = await this.orm.read('dashboard.card.field', card.table_field_line_ids, ['sequence', 'field_id']);
            exportData.table_field_line_ids = tableFields.map(f => [0, 0, {
                sequence: f.sequence,
                field_id: f.field_id[0]
            }]);
        }

        if (card.todo_ids && card.todo_ids.length > 0) {
            const todos = await this.orm.read('dashboard.todo', card.todo_ids, ['name', 'status', 'is_done', 'priority_backup']);
            exportData.todo_ids = todos.map(t => [0, 0, {
                name: t.name,
                status: t.status,
                is_done: t.is_done,
                priority_backup: t.priority_backup
            }]);
        }

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportData, null, 4));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", (card.name || "dashboard_card") + ".json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();

        this.notification.add(_t("Card configuration exported successfully"), {
            type: "success",
        });
    }

    async onExportToExcel(ev) {
        ev.preventDefault();

        this.ui.block();

        this.notification.add(_t("Preparing Excel export..."), {
            type: "info",
        });

        setTimeout(async () => {
            try {
                // Load XLSX library from CDN if not already loaded
                if (!window.XLSX) {
                    await new Promise((resolve, reject) => {
                        const script = document.createElement('script');
                        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                }

                const data = await this._getExportData();
                if (!data || data.length === 0) {
                    this.notification.add(_t("No data found to export"), {
                        type: "warning",
                    });
                    return;
                }

                const ws = XLSX.utils.json_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, "Data");

                const cardName = this.props.card.name || 'dashboard-card';
                const fileName = `${cardName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.xlsx`;
                XLSX.writeFile(wb, fileName);

                this.notification.add(_t("Excel file downloaded successfully"), {
                    type: "success",
                });
            } catch (error) {
                this.notification.add(_t("Failed to export to Excel: " + error.message), {
                    type: "danger",
                });
            } finally {
                this.ui.unblock();
            }
        }, 50);
    }

    async onExportToCSV(ev) {
        ev.preventDefault();

        this.ui.block();

        this.notification.add(_t("Preparing CSV export..."), {
            type: "info",
        });

        setTimeout(async () => {
            try {
                const data = await this._getExportData();
                if (!data || data.length === 0) {
                    this.notification.add(_t("No data found to export"), {
                        type: "warning",
                    });
                    return;
                }

                // Convert JSON to CSV
                const headers = Object.keys(data[0]);
                const csvRows = [];
                csvRows.push(headers.join(','));

                for (const row of data) {
                    const values = headers.map(header => {
                        const val = row[header];
                        const escaped = ('' + val).replace(/"/g, '""');
                        return `"${escaped}"`;
                    });
                    csvRows.push(values.join(','));
                }

                const csvString = csvRows.join('\n');
                const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');

                const cardName = this.props.card.name || 'dashboard-card';
                const fileName = `${cardName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.csv`;

                link.href = url;
                link.setAttribute('download', fileName);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);

                this.notification.add(_t("CSV file downloaded successfully"), {
                    type: "success",
                });
            } catch (error) {
                this.notification.add(_t("Failed to export to CSV: " + error.message), {
                    type: "danger",
                });
            } finally {
                this.ui.unblock();
            }
        }, 50);
    }

    _sanitizeCloneForExport(clonedCard) {
        // Fix for html2canvas crashing on color-mix()
        const masonryImages = clonedCard.querySelectorAll('.masonry-card-image');
        masonryImages.forEach(img => {
            const style = window.getComputedStyle(img);
            const color = style.getPropertyValue('--color').trim() || '#6366f1';
            // Replace complex gradient with simple one
            img.style.background = `linear-gradient(135deg, ${color}, #000000)`;
        });

        const avatars = clonedCard.querySelectorAll('.masonry-user-avatar');
        avatars.forEach(avatar => {
            const style = window.getComputedStyle(avatar);
            const color = style.getPropertyValue('--color').trim() || '#6366f1';
            avatar.style.background = `linear-gradient(135deg, ${color}, #333333)`;
        });
    }

    async _getExportData() {
        const card = this.props.card;
        let data = [];


        if (card.type === 'table' && card.table_rows) {
            try {
                const batches = JSON.parse(card.table_rows);
                data = batches.flat();
            } catch (e) {
            }
        } else if (card.type === 'chart') {
            try {
                const xData = JSON.parse(card.chart_x_axis_data || "[]");
                const yData = JSON.parse(card.chart_y_axis_data || "[]");

                const groupByField = card.group_by_field_id;
                const measureField = card.measure_field_id;

                const groupByLabel = (Array.isArray(groupByField) && groupByField.length > 1) ? groupByField[1] : 'Category';
                const measureLabel = (Array.isArray(measureField) && measureField.length > 1) ? measureField[1] : 'Value';

                data = xData.map((label, index) => ({
                    [groupByLabel]: label,
                    [measureLabel]: yData[index] || 0
                }));
            } catch (e) {
            }
        } else if (card.type === 'views') {

            try {
                // The model_id is [id, display_name] but we need the technical name
                // Let's check if there's a model property or we need to fetch it
                let modelName = null;

                // Try to get model from different possible properties
                if (card.model) {
                    modelName = card.model;
                } else if (card.model_id && Array.isArray(card.model_id) && card.model_id.length > 0) {
                    // We have the model ID, need to fetch the technical name
                    const modelId = card.model_id[0];

                    // Fetch the ir.model record to get technical name
                    const modelRecord = await this.orm.searchRead(
                        'ir.model',
                        [['id', '=', modelId]],
                        ['model'],
                        { limit: 1 }
                    );

                    if (modelRecord && modelRecord.length > 0) {
                        modelName = modelRecord[0].model;
                    }
                }


                if (!modelName) {
                    data = [];
                    return data;
                }

                // Parse domain
                let domain = [];
                try {
                    domain = card.domain ? JSON.parse(card.domain) : [];
                } catch (e) {
                    domain = [];
                }


                // Define fields to fetch
                const fields = ['id', 'display_name'];

                // Fetch data directly using searchRead
                const records = await this.orm.searchRead(
                    modelName,
                    domain,
                    fields,
                    { limit: card.record_limit || 10 }
                );


                // Format the data
                data = records.map(rec => {
                    const row = {};
                    for (const [key, val] of Object.entries(rec)) {
                        if (Array.isArray(val) && val.length === 2) {
                            row[key] = String(val[1]);
                        } else if (val === false || val === null) {
                            row[key] = "";
                        } else {
                            row[key] = String(val);
                        }
                    }
                    return row;
                });


            } catch (e) {
                data = [];
            }
        } else if (card.type === 'block') {
            // For blocks, we can export the primary value/title
            data = [{
                "Title": card.name,
                "Description": card.description,
                "Type": card.type
            }];
        }


        return data;
    }
}
DashboardCardButtons.template = 'DashboardCardButtons';
