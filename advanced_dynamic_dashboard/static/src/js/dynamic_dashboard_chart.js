/** @odoo-module **/
import { loadJS } from '@web/core/assets';
import { getColor } from "@web/core/colors/colors";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
const { Component, xml, onWillStart, useRef, onMounted } = owl

export class DynamicDashboardChart extends Component {
    // Setup function of the class DynamicDashboardChart
    setup() {
        this.doAction = this.props.doAction.doAction;
        this.chartRef = useRef("chart");
        this.dialog = this.props.dialog;
        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.5.3/jspdf.min.js")
            await loadJS("https://cdn.jsdelivr.net/npm/exceljs@4.4.0/dist/exceljs.min.js")
        })
        onMounted(()=> this.renderChart())
    }
    // Function to export the chart in pdf, image, xlsx and csv format
    exportItem(ev){
        ev.stopPropagation();
        ev.preventDefault();
        var type = $(ev.currentTarget).attr('data-type');
        var canvas = $($($(ev.currentTarget)[0].offsetParent)[0].children[0].lastChild).find("#canvas")[0]
        var dataTitle = $(canvas).attr('data-title')
        var bgCanvas = document.createElement("canvas");
        bgCanvas.width = canvas.width;
        bgCanvas.height = canvas.height;
        var bgCtx = bgCanvas.getContext("2d");
        bgCtx.fillStyle = "white";
        bgCtx.fillRect(0, 0, canvas.width, canvas.height);
        bgCtx.drawImage(canvas, 0, 0);
        var imgData = bgCanvas.toDataURL("image/png");
        if (type === 'png') {
            var downloadLink = document.createElement('a');
            downloadLink.href = imgData;
            downloadLink.download = `${dataTitle}.png`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
        if (type === 'pdf') {
            var pdf = new jsPDF();
            pdf.addImage(imgData, 'PNG', 0, 0);
            pdf.save(`${dataTitle}.pdf`);
        }
        if (type === 'xlsx'){
            var rows = [];
            var items = $('.resize-drag');
            for (let i = 0; i < items.length; i++) {
                if ($(items[i]).attr('data-id') === $(ev.currentTarget).attr('data-id')) {
                    rows.push(this.props.widget.x_axis);
                    rows.push(this.props.widget.y_axis);
                }
            }
            // Prepare the workbook
            const workbook = new ExcelJS.Workbook();
            const worksheet = workbook.addWorksheet('My Sheet');
            for(let i = 0; i < rows.length; i++){
                worksheet.addRow(rows[i]);
            }
            const image = workbook.addImage({
              base64: imgData,
              extension: 'png',
            });
            worksheet.addImage(image, {
              tl: { col: 0, row: 4 },
              ext: { width: canvas.width, height: canvas.height }
            });
            // Save workbook to a file
            workbook.xlsx.writeBuffer()
            .then((buffer) => {
                // Create a Blob object from the buffer
                let blob = new Blob([buffer], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
                let link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.setAttribute("download", `${dataTitle}.xlsx`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            })
        }
        if (type === 'csv') {
            var rows = [];
            var items = $('.resize-drag')
            for (let i = 0; i < items.length; i++) {
                if ($(items[i]).attr('data-id') === $(ev.currentTarget).attr('data-id')) {
                    rows.push(this.props.widget.x_axis);
                    rows.push(this.props.widget.y_axis);
                }
            }
            let csvContent = "data:text/csv;charset=utf-8,";
            rows.forEach(function (rowArray) {
                let row = rowArray.join(",");
                csvContent += row + "\r\n";
            });
            var link = document.createElement("a");
            link.setAttribute("href", encodeURI(csvContent));
            link.setAttribute("download", `${dataTitle}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
    // Function to get the configuration of the chart
    async getConfiguration(ev){
        ev.stopPropagation();
        ev.preventDefault();
        var id = this.props.widget.id
        await this.doAction({
            type: 'ir.actions.act_window',
            res_model: 'dashboard.block',
            res_id: id,
            view_mode: 'form',
            views: [[false, "form"]]
        });
    }
    // Function to remove the chart
    async removeTile(ev){
        ev.stopPropagation();
        ev.preventDefault();
        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete Confirmation"),
            body: _t("Are you sure you want to delete this item?"),
            confirmLabel: _t("YES, I'M SURE"),
            cancelLabel: _t("NO, GO BACK"),
            confirm: async () => {
                await this.props.orm.unlink("dashboard.block", [this.props.widget.id]);
                location.reload();
            },
            cancel: () => {},
        });
    }
    // Function to render the chart
    renderChart(){
        if (this.props.widget.graph_type){
            const x_axis = this.props.widget.x_axis
            const y_axis = this.props.widget.y_axis
            const data = []
            for (let i = 0; i < x_axis.length; i++) {
                const value = { key: x_axis[i], value: y_axis[i] }
                data.push(value);
            }
            new Chart(
                this.chartRef.el,
                    {
                        type: this.props.widget.graph_type || 'bar',
                        data: {
                            labels: data.map(row => row.key),
                            datasets: [
                                {
                                    label: this.props.widget.measured_field || 'Data',
                                    data: data.map(row => row.value),
                                    backgroundColor: data.map((_, index) => getColor(index)),
                                    hoverOffset : 4
                                }
                            ]
                        },
                    }
              );
        }
    }
}

DynamicDashboardChart.template = xml`
    <div class="resize-drag block card"
        t-att-data-x="this.props.widget.data_x"
        t-att-data-y="this.props.widget.data_y"
        t-att-style="'height:'+this.props.widget.height+'; width:'+ this.props.widget.width+ '; transform: translate('+ this.props.widget.translate_x +', '+ this.props.widget.translate_y +');'"
        t-att-data-id="this.props.widget.id">
        <div class="card-body mt-1" id="in_ex_body_hide">

            <div class="block_edit block_setting" t-on-click="(ev) => this.getConfiguration(ev)">
                <i title="Configuration"
                    class="fa fa-pencil block_setting chart-edit"/>
            </div>

            <div class="block_edit block_image" data-type="png" t-on-click="(ev) => this.exportItem(ev)">
                <i title="Save As Image"
                    class="bi bi-image block_image chart-image"/>
            </div>

            <div class="block_edit block_pdf" data-type="pdf" t-on-click="(ev) => this.exportItem(ev)">
                <i title="Export to PDF"
                    class="bi bi-file-earmark-pdf block_pdf chart-pdf"/>
            </div>

            <div class="block_edit block_csv" t-att-data-id="this.props.widget.id" data-type="csv" t-on-click="(ev) => this.exportItem(ev)">
                <i title="Export to CSV"
                    class="bi bi-filetype-csv block_csv chart-csv"/>
            </div>

            <div class="block_edit block_xlsx" t-att-data-id="this.props.widget.id" data-type="xlsx" t-on-click="(ev) => this.exportItem(ev)">
                <i title="Export to XLSX"
                    class="fa fa-file-excel-o block_xlsx chart-xlsx"/>
            </div>

            <div class="block_edit block_delete" t-on-click="(ev) => this.removeTile(ev)">
                <i title="Delete"
                    class="fa fa-times block_delete chart-setting"/>
            </div>
            <h3 class="chart_title">
                <t t-esc="this.props.widget.name"/>
            </h3>
            <div class="row-class">
                <div class="col-md-12 chart_canvas" id="chart_canvas"
                    t-att-data-id="this.props.widget.id">
                    <canvas id="canvas" t-ref="chart" t-att-data-title="this.props.widget.name"/>
                </div>
            </div>
        </div>
    </div>
                `
