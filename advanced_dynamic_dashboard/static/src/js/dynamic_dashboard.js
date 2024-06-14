/** @odoo-module **/
import { registry } from "@web/core/registry";
import { loadJS } from '@web/core/assets';
import { DynamicDashboardTile} from './dynamic_dashboard_tile';
import { DynamicDashboardChart} from './dynamic_dashboard_chart';
import { useService } from "@web/core/utils/hooks";
const { Component, useRef, mount, onWillStart, onMounted} = owl;

export class AdvancedDynamicDashboard extends Component {
    // Setup function to run when the template of the class AdvancedDynamicDashboard renders
    setup() {
        this.ThemeSelector = useRef('ThemeSelector');
        this.action = useService("action");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.actionId = this.props.actionId
        this.rpc = useService("rpc");
        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.5.3/jspdf.min.js")
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js")
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.9.3/html2pdf.bundle.min.js")
        })
        onMounted(()=>{
            this.renderDashboard();
        })
    }

    onChangeTheme(){
        /* Function for changing color of the theme of the dashboard */
        $(".container").attr('style', this.ThemeSelector.el.value + 'min-height:-webkit-fill-available;')
    }

    ResizeDrag() {
    /* Function for resizing and dragging the div resize-drag */
        $('.items .resize-drag').each(function(index, element) {
            interact(element).resizable({
                edges: { left: true, right: true, bottom: true, top: true },
                listeners: {
                    move (event) {
                        var target = event.target
                        var x = (parseFloat(target.getAttribute('data-x')) || 0)
                        var y = (parseFloat(target.getAttribute('data-y')) || 0)
                        // update the element's style
                        target.style.width = event.rect.width + 'px'
                        target.style.height = event.rect.height + 'px'
                        // translate when resizing from top or left edges
                        x += event.deltaRect.left
                        y += event.deltaRect.top
                    }
                },
                modifiers: [
                    // keep the edges inside the parent
                    interact.modifiers.restrictEdges({
                        outer: 'parent'
                    }),
                    // minimum size
                    interact.modifiers.restrictSize({
                        min: { width: 100, height: 50 }
                    })
                ],
                inertia: true
            }).draggable({
                listeners: {move: dragMoveListener},
                inertia: true,
                modifiers: [
                    interact.modifiers.restrictRect({
                        restriction: 'parent',
                        endOnly: true
                    })
                ]
            })

            function dragMoveListener (event) {
                var target = event.target
                // keep the dragged position in the data-x/data-y attributes
                var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx
                var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy
                // translate the element
                target.style.transform = 'translate(' + x + 'px, ' + y + 'px)'
                // update the posiion attributes
                target.setAttribute('data-x', x)
                target.setAttribute('data-y', y)
            }
            // this function is used later in the resizing
            window.dragMoveListener = dragMoveListener
        });
    }

    async renderDashboard(){
    /* Function for rendering the dashboard */
        var self = this;
        $("#save_layout").hide();
        await this.orm.call('dashboard.theme', 'get_records', [[]]).then(function (response) {
            response.forEach((ev) => {
                const options = document.createElement("option");
                options.value = ev.style;
                options.text = ev.name;
                self.ThemeSelector.el.append(options)
            });
        })
        await this.orm.call("dashboard.block", "get_dashboard_vals", [[], this.actionId]).then( function (response){
            for (let i = 0; i < response.length; i++) {
                if (response[i].type === 'tile'){
                    mount(DynamicDashboardTile, $('.items')[0], { props: {
                        widget: response[i], doAction: self.action, dialog:self.dialog, orm: self.orm
                    }});
                }
                else{
                    mount(DynamicDashboardChart, $('.items')[0], { props: {
                        widget: response[i], doAction: self.action, rpc: self.rpc, dialog:self.dialog, orm: self.orm
                    }});
                }
            }
        })
    }

    editLayout(ev) {
    /* Function for editing the layout , it enables resizing and dragging functionality */
        $('.items .resize-drag').each(function(index, element) {
            interact(element).draggable(true)
            interact(element).resizable(true)
        });
        ev.stopPropagation();
        ev.preventDefault();
        $("#edit_layout").hide();
        $("#save_layout").show();
        this.ResizeDrag()
    }

    saveLayout(ev){
    /* Function for saving the layout */
        var self = this;
        ev.stopPropagation();
        ev.preventDefault();
        $("#edit_layout").show();
        $("#save_layout").hide();
        var data_list = []
        $('.items .resize-drag').each(function(index, element) {
            interact(element).draggable(false)
            interact(element).resizable(false)
            data_list.push({
                'id' : element.dataset['id'],
                'data-x': element.dataset['x'],
                'data-y': element.dataset['y'],
                'height': element.clientHeight,
                'width': element.clientWidth,
            })
        });
        self.orm.call('dashboard.block','get_save_layout', [[], data_list]).then( function (response){
            window.location.reload();
        });
    }

    changeViewMode(ev){
    /* Function for changing the mode of the view */
        ev.stopPropagation();
        ev.preventDefault();
        const currentMode = $(".mode").attr("mode");
        if (currentMode == "light"){
            $('.theme').attr('style','display: none;')
            $(".container").attr('style', 'background-color: #383E45;min-height:-webkit-fill-available; !important')
            $(".mode").attr("mode", "dark")
            $(".bi-moon-stars-fill").attr('class', 'bi bi-cloud-sun-fill view-mode-icon')
            $(".bi-cloud-sun-fill").attr('style', 'color:black;margin-left:10px;')
            $(".mode").attr('style','display: none !important');
            $("#search-input-chart").attr('style', 'background-color: white; !important')
            $("#search-button").attr('style', 'background-color: #BB86FC; !important')
            $("#dropdownMenuButton").attr('style', 'background-color: #03DAC5;margin-top:-4px; !important')
            $("#text_add").attr('style', 'color: black; !important')
            $(".date-label").attr('style', 'color: black;font-family:monospace; !important')
            $(".block_setting").attr('style', 'color: white; !important')
            $(".block_delete").attr('style', 'color: white; !important')
            $(".block_image").attr('style', 'color: #03DAC5; !important')
            $(".block_pdf").attr('style', 'color: #03DAC5; !important')
            $(".block_csv").attr('style', 'color: #03DAC5; !important')
            $(".block_xlsx").attr('style', 'color: #03DAC5; !important')
        }
        else {
            $('.theme').attr('style','display: block;')
            $(".container").attr('style', this.ThemeSelector.el.value + 'min-height:-webkit-fill-available;')
            $(".mode").attr("mode", "light")
            $(".bi-cloud-sun-fill").attr('class', 'bi bi-moon-stars-fill view-mode-icon')
            $(".view-mode-icon").attr('style', 'color:black;margin-left:10px; !important')
            $(".mode").attr('style','display: none !important');
            $(".mode").attr('style','color: white !important');
            $("#search-input-chart").attr('style', 'background-color: none; !important')
            $("#search-button").attr('style', 'background-color: none; !important')
            $("#dropdownMenuButton").attr('style', 'background-color: none;margin-top:-4px; !important')
            $("#text_add").attr('style', 'color: white; !important')
            $(".date-label").attr('style', 'color: black; !important;font-family:monospace; !important')
            $(".block_setting").attr('style', 'color: black; !important')
            $(".block_delete").attr('style', 'color: black; !important')
            $(".block_image").attr('style', 'color: black; !important')
            $(".block_pdf").attr('style', 'color: black; !important')
            $(".block_csv").attr('style', 'color: black; !important')
            $(".block_xlsx").attr('style', 'color: black; !important')
        }
    }
    onClickAdd(event){
    /* For enabling the toggle button */
        event.stopPropagation();
        event.preventDefault();
        $(".dropdown-addblock").toggle()
    }
    onClickAddItem(event){
    /* Function for adding tiles and charts */
        event.stopPropagation();
        event.preventDefault();
        self = this;
        var type = event.target.getAttribute('data-type');
        if (type == 'graph'){
            var chart_type = event.target.getAttribute('data-chart_type');
        }
        if (type == 'tile'){
            var randomColor = '#' + ('000000' + Math.floor(Math.random() * 16777216).toString(16)).slice(-6);
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'dashboard.block',
                view_mode: 'form',
                views: [[false, 'form']],
                context: {
                    'form_view_initial_mode': 'edit',
                    'default_name': 'New Tile',
                    'default_type': type,
                    'default_height': '155px',
                    'default_width': '300px',
                    'default_tile_color': randomColor,
                    'default_text_color': '#FFFFFF',
                    'default_val_color': '#F3F3F3',
                    'default_fa_icon': 'fa fa-bar-chart',
                    'default_client_action_id': parseInt(self.actionId)
                }
            })
        }
        else{
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'dashboard.block',
                view_mode: 'form',
                views: [[false, 'form']],
                context: {
                    'form_view_initial_mode': 'edit',
                    'default_name': 'New ' + chart_type,
                    'default_type': type,
                    'default_height': '565px',
                    'default_width': '588px',
                    'default_graph_type': chart_type,
                    'default_fa_icon': 'fa fa-bar-chart',
                    'default_client_action_id': parseInt(self.actionId)
                },
            })
        }
    }

    dateFilter(){
    /* Function for filtering the data based on the creation date */
        $(".items").empty();
        var start_date = $("#start-date").val();
        var end_date = $("#end-date").val();
        var self = this;
        if (!start_date){
            start_date = "null"
        }
        if (!end_date){
            end_date = "null"
        }
        this.orm.call("dashboard.block", "get_dashboard_vals", [[], this.actionId, start_date, end_date]).then( function (response){
            for (let i = 0; i < response.length; i++) {
                if (response[i].type === 'tile'){
                    mount(DynamicDashboardTile, $('.items')[0], { props: {
                        widget: response[i], doAction: self.action, dialog:self.dialog, orm: self.orm
                    }});
                }
                else{
                    mount(DynamicDashboardChart, $('.items')[0], { props: {
                        widget: response[i], doAction: self.action, rpc: self.rpc, dialog:self.dialog, orm: self.orm
                    }});
                }
            }
        })
    }

    async clickSearch(){
    /* Function for searching the blocks with their names */
        var input = $("#search-input-chart").val();
        await this.rpc('/custom_dashboard/search_input_chart', {'search_input': input}).then(function (response) {
            var blocks = $(".items .resize-drag");
            blocks.each(function(index, element){
                var dataId = $(element).data('id');
                if (response.includes(dataId)){
                    $(element).css("visibility", "visible");
                }
                else{
                    $(element).css("visibility", "hidden");
                }
            })
        })
    }

    showViewMode(ev){
    /* Function for showing the mode text */
        const currentMode = $(".mode").attr("mode");
        if (currentMode == "light"){
            $(".mode").text("Dark Mode")
            $(".mode").attr('style','display: inline-block !important; color: black !important');
        }
        else{
            $(".mode").text("Light Mode")
            $(".mode").attr('style','display: inline-block !important; color: black !important');
        }
    }
    hideViewMode(ev){
    /* Function for hiding the mode text */
        $(".mode").fadeOut(2000);
    }
    clearSearch(){
    /* Function for clearing the search input */
        $("#search-input-chart").val('');
        var blocks = $(".items .resize-drag");
        blocks.each(function(index, element){
            $(element).css("visibility", "visible");
        })
    }

    async printPdf() {
    /* Function for printing whole dashboard in pdf format */
        var elements = $('.items .resize-drag')
        var newElement = document.createElement('div');
        newElement.className = 'pdf';
        elements.each(function(index, elem){
            newElement.appendChild(elem);
        });
        for (var x=0; x< $(newElement)[0].children.length; x++){
            $($(newElement)[0].children[x])[0].style.transform = ""
        }
        var opt = {
            margin:       0.3,
            filename:     'Dashboard.pdf',
            image:        { type: 'jpeg', quality: 1 },
            html2canvas:  { scale: 1 },
            jsPDF:        { unit: 'mm', format: 'a3', orientation: 'portrait' }
        };
        html2pdf().set(opt).from(newElement).save().then(()=>{
            window.location.reload()
        })
    }

    async createPDF(){
    /* Function for getting pdf data in string format */
        var elements = $('.items .resize-drag')
        var newElement = document.createElement('div');
        newElement.className = 'pdf';
        elements.each(function(index, elem){
            newElement.appendChild(elem);
        });
        for (var x=0; x< $(newElement)[0].children.length; x++){
            $($(newElement)[0].children[x])[0].style.transform = ""
        }
        var opt = {
            margin:       0.3,
            filename:     'Dashboard.pdf',
            image:        { type: 'jpeg', quality: 1 },
            html2canvas:  { scale: 1 },
            jsPDF:        { unit: 'mm', format: 'a3', orientation: 'portrait' }
        };
        var pdf = html2pdf().set(opt).from(newElement).toPdf()
        var pdfOutput = await pdf.output('datauristring');
        console.log(pdfOutput)
        return pdfOutput
    }

    async sendMail(){
        /* Function for creating pdf and sending mail to the selected users */
        /* This function calls the createPDF() function and returns the pdf datas */
        var created_pdf = await this.createPDF();
        var base64code = created_pdf.split(',')[1];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'SEND MAIL',
            res_model: 'dashboard.mail',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_base64code': base64code,
            }
        })
    }
}
AdvancedDynamicDashboard.template = "owl.AdvancedDynamicDashboard"
registry.category("actions").add("AdvancedDynamicDashboard", AdvancedDynamicDashboard)
