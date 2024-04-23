odoo.define('advanced_dynamic_dashboard.Dashboard', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var Dialog = require('web.Dialog');
    var DynamicDashboard = AbstractAction.extend({
        template: 'advanced_dynamic_dashboard',
        events: {
            'click .add_block': '_onClick_add_block',
            'click .block_setting': '_onClick_block_setting',
            'click .block_delete': '_onClick_block_delete',
            'click #search-button': 'search_chart',
            'click #searchclear': 'clear_search',
            'click #dropdownNavbar': 'navbar_toggle',
            'mouseenter #dropdownMenuButton': 'dropdown_toggle',
            'click .chart_item_export': 'export_item',
            'click #edit_layout': '_onClick_edit_layout',
            'click #save_layout': '_onClick_save_layout',
            'change #theme-toggle': 'switch_mode',
            'change #start-date': '_onchangeFilter',
            'change #end-date': '_onchangeFilter',
            'mouseenter #theme-change-icon': 'show_mode_text',
            'mouseleave #theme-change-icon': 'hide_mode_text',
            'click .tile': '_onClick_tile'
        },
        //Function to Initializes all the values while loading the file
        init: function (parent, context) {
            this.action_id = context['id'];
            this._super(parent, context);
            this.block_ids = [];
        },
        //Returns the function fetch_data when page load.
        willStart: function () {
            var self = this;
            return $.when(this._super()).then(function () {
                return self.fetch_data();
            });
        },
        //Function return render_dashboards() and gridstack_init()
        start: function () {
            self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
            });
        },
        //Fetch data and call rpc query to create chart or tile. return block_ids
        fetch_data: function () {
            self = this;
            var def1 = this._rpc({
                model: 'dashboard.block',
                method: 'get_dashboard_vals',
                args: [[], this.action_id]
            }).then(function (result) {
                self.block_ids = result;
            });
            return $.when(def1);
        },
        //Function change text of dark and light mode while clicking the dark and light button.
        show_mode_text: function () {
            this.$el.find('.theme_icon').next(this.el.querySelector('.theme-text')).remove();
            if ( this.$el.find('#theme-toggle').is(':checked')) {//Set text "Light Mode"
                this.$el.find('.theme_icon').after('<span style="color: #d6e7ff" class="theme-text">⠀Light Mode</span>');
            } else {
            //Set text "Dark Mode"
                this.$el.find('.theme_icon').after('<span style="color: #000000" class="theme-text">⠀Dark Mode</span>');
            }
            this.$el.find('.theme_icon').next(this.el.querySelector('.theme-text')).fadeIn();
        },
        //While click button, hide the mode icon and text
        hide_mode_text: function () {
            this.$el.find('.theme_icon').next(this.el.querySelector('.theme-text')).fadeOut(function () {
                $(this).remove();
            });
        },
        //Function to change dashboard theme dark and light mode.
        switch_mode: function (ev) {
            this.$el.find('.theme_icon').next('.theme-text').remove();
            const isDarkTheme = this.$el.find('#theme-toggle').is(':checked');
            $(this.el.parentElement).toggleClass('dark-theme', isDarkTheme);
            this.$el.find('.theme_icon').toggleClass('bi-sun-fill', isDarkTheme);
            this.$el.find('.theme_icon').toggleClass('bi-moon-stars-fill', !isDarkTheme);
            this.$el.find('.dropdown-export').toggleClass('dropdown-menu-dark', isDarkTheme);
        },
        //Function for applying filter
        _onchangeFilter: function() {
            var start_date = this.$('#start-date').val();
            var end_date = this.$('#end-date').val();
            if (!start_date) {
                start_date = "null";
            }
            if (!end_date) {
                end_date = "null";
            }
            this._rpc({
                model: 'dashboard.block',
                method: 'get_dashboard_vals',
                args: [[], this.action_id, start_date, end_date],
            }).then(function (result) {
                self.block_ids = result;
                // Reinitialize gridstack layout after updating data
                self.gridstack_init(self);
                self.$('.o_dynamic_dashboard').empty();
                self.render_dashboards();
            });
        },
        //Function fetch random color values and set chart color
        get_colors: function (x_axis) {
            return x_axis.map(() => `rgb(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)})`);
        },
        //Set bar chart label, color, data and options. And return data and options
        get_values_bar: function (block) {
            var data = {
                labels: block.x_axis,
                datasets: [{
                    data: block.y_axis,
                    backgroundColor: this.get_colors(block.x_axis),
                    borderColor: 'rgba(200, 200, 200, 0.75)',
                    borderWidth: 1
                }]
            };
            var options = {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            };
            return [data, options];
        },
        //Set pie chart data and options. And return data and options.
        get_values_pie: function (block) {
            var data = {
                labels: block['x_axis'],
                datasets: [{
                    label: '',
                    data: block['y_axis'],
                    backgroundColor: this.get_colors(block['x_axis']),
                    hoverOffset: 4
                }]
            };
            return [data, {}];
        },
        //Set line chart label, data and options. And return data and options.
        get_values_line: function (block) {
            var data = {
                labels: block['x_axis'],
                datasets: [{
                    label: '',
                    data: block['y_axis'],
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            };
            return [data, {}];
        },
        // Set doughnut chart data and options. And return data and options.
        get_values_doughnut: function (block) {
            var data = {
                labels: block['x_axis'],
                datasets: [{
                    label: '',
                    data: block['y_axis'],
                    backgroundColor: this.get_colors(block['x_axis']),
                    hoverOffset: 4
                }]
            };
            return [data, {}];
        },
        // Set radar chart data and options. And return data and options.
        get_values_radar: function (block) {
            var data = {
                labels: block['x_axis'],
                datasets: [{
                    label: '',
                    data: block['y_axis'],
                    fill: true,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    pointBackgroundColor: 'rgb(255, 99, 132)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 99, 132)'
                }]
            };
            var options = {
                    elements: {
                        line: {
                            borderWidth: 3
                        }
                    }
                }
            return [data, options];
        },
        // Used gridstack to drag and resize chart and tile.
        gridstack_init: function (self) {// Used gridstack to drag and resize chart and tile.
            self.$('.grid-stack').gridstack({
                animate: true,
                duration: 200,
                handle: '.grid-stack-item-content',
                draggable: {
                    handle: '.grid-stack-item-content',
                    scroll: true
                },
                resizable:{
                aspectRatio:20/18,
                },
                alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
                float: true
            });
            self.gridstack_off(self);
        },
        // Enable move and resize functionality
        gridstack_on: function (self) {
            var gridstack = self.$('.grid-stack').data('gridstack');
            gridstack.enableMove(true);
            gridstack.enableResize(true);
        },
        // Disable move and resize functionality
        gridstack_off: function (self) {
            var gridstack = self.$('.grid-stack').data('gridstack');
            gridstack.enableMove(false);
            gridstack.enableResize(false);
        },
        //Function for rendering dashboards
        render_dashboards: function () {
            self.$("#save_layout").hide();//Hide save_layout button
            _.each(this.block_ids, function (block) {
                if (block['type'] == 'tile') {
                    self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTile', {widget: block}));
                    // Add the new tile to the Gridstack layout with correct position and size
                    var newTile = self.$('.o_dynamic_dashboard').children().last();
                    // Check if the Gridstack element is initialized
                    var gridstack = self.$('.grid-stack').data('gridstack');
                    if (gridstack) {
                        gridstack.addWidget(newTile, block.x, block.y, block.width, block.height, block.autoPosition);
                    }
                } else {
                    // Block type = 'chart'
                    self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardChart', {widget: block}));
                    if (!('x_axis' in block)) {
                        return false;
                    }
                    var type = block['graph_type'];
                    var chart_type = 'self.get_values_' + `${type}(block)`;
                    // Set up and render the chart using Chart.js
                    var newChartContainer = self.$('.o_dynamic_dashboard').children().last();
                    new Chart(self.$('.chart_graphs').last(), {
                        type: block['graph_type'],
                        data: eval(chart_type)[0],
                        options: eval(chart_type)[1]
                    });
                    // Check if the Gridstack element is initialized
                    var gridstack = self.$('.grid-stack').data('gridstack');
                    if (gridstack) {
                        // Add the new chart container to the Gridstack layout at the original position
                        gridstack.addWidget(newChartContainer, block.x, block.y, block.width, block.height, block.autoPosition);
                    }
                }
            });
            // Toggling dropdown for exporting, clicked item, closing all others
            // When clicked on one, also when mouse leaves parent.
            self.$(".block_export").on({
                click: function () {//Show the export dropdown.
                    if ($(this).next(".dropdown-export").is(':visible')) {
                        $(this).next(".dropdown-export").hide();
                    } else {
                        $(this).next('.dropdown-export').hide();
                        $(this).next(".dropdown-export").show();
                    }
                }
            });
            //Function to hide dropdown-export list while mouse leave the block.
            self.$(".grid-stack-item").on({
                mouseleave: function () {
                   self.$('.dropdown-export').hide();
                }
            });
            //Function to hide dropdown-addblock list if mouse leave dropdown
            //list.
            self.$(".dropdown-addblock").on({
                mouseleave: function () {
                    self.$(".dropdown-addblock").hide();
                }
            });
            self.gridstack_init(self);
            if (localStorage.getItem("toggleState") == 'true') {
                self.$(".toggle").prop('checked', true)
                $(self.el.parentElement).addClass('dark-theme');
                self.$(".theme_icon").removeClass('bi-moon-stars-fill');
                self.$(".theme_icon").addClass('bi-sun-fill');
                self.$(".dropdown-export").addClass('dropdown-menu-dark');
            } else {
                $(self.el.parentElement).removeClass('dark-theme');
                self.$(".theme_icon").removeClass('bi-sun-fill');
                self.$(".theme_icon").addClass('bi-moon-stars-fill');
                self.$(".dropdown-export").removeClass('dropdown-menu-dark');
            }
        },
        //Function to toggle the navbar.
        navbar_toggle: function () {
            this.$('.navbar-collapse').toggle();
        },
        //Function to export chart into jpg, png or csv formate.
        export_item: function (e) {
            var type = $(e.currentTarget).attr('data-type');
            var canvas = $(e.currentTarget).closest('.export_option').siblings('.row').find('#canvas')[0];
            var dataTitle = canvas.getAttribute("data-title");
            // Create a new canvas with a white background
            var bgCanvas = document.createElement("canvas");
            bgCanvas.width = canvas.width;
            bgCanvas.height = canvas.height;
            var bgCtx = bgCanvas.getContext("2d");
            bgCtx.fillStyle = "white";
            bgCtx.fillRect(0, 0, canvas.width, canvas.height);
            // Draw the chart onto the new canvas
            bgCtx.drawImage(canvas, 0, 0);
            // Export the new canvas as an image
            var imgData = bgCanvas.toDataURL("image/png");
            if (type === 'png') {
                this.$el.find('.chart_png_export').attr({
                    href: imgData,
                    download: `${dataTitle}.png`
                });
            }
            if (type === 'pdf') {
                var pdf = new jsPDF();
                pdf.addImage(bgCanvas.toDataURL("image/png"), 'PNG', 0, 0);
                pdf.save(`${dataTitle}.pdf`);
            }
            if (type === 'csv') {
                var rows = [];
                // Check if the id inside the object is equal to this id
                for (var obj of this.block_ids) {
                    if (obj.id == $(e.currentTarget).attr('data-id')) {
                        rows.push(obj.x_axis);
                        rows.push(obj.y_axis);
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
                document.body.appendChild(link); // Required for FF
                link.click();
            }
        },
        //Function to toggle the button Add Items.
        dropdown_toggle: function () {
            this.$el.find('.dropdown-addblock').show();
        },
        //Function return all block in exact position.
        on_reverse_breadcrumb: function () {
            this.fetch_data().then(function () {//Fetch all datas
                self.render_dashboards();
                self.gridstack_init(self);
                location.reload();
            });
        },
        // Fetch search input value and filter the chart and tile.
        search_chart: function (e) {
            e.stopPropagation();
            var self = this;
            // Hide certain elements
            self.$(this).next("#theme-change-icon").hide();
            self.$("#edit_layout").hide();
            self.$("#save_layout").hide();
            self.$(".date-inputs").hide();
            // Clear existing Gridstack layout
            self.$('.grid-stack').data('gridstack').removeAll();
            // Empty the dynamic dashboard container
            self.$('.o_dynamic_dashboard').empty();
            // Fetch filtered data using Ajax
            ajax.jsonRpc("/custom_dashboard/search_input_chart", 'call', {
                'search_input': self.$("#search-input-chart").val()
            }).then(function (res) {
                // Iterate through block_ids
                _.each(self.block_ids, function (block) {
                    if (res.includes(block['id'])) {
                        // Check block type and render accordingly
                        if (block['type'] == 'tile') {
                            self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardTile', {widget: block}));
                            // Add the new tile to the Gridstack layout
                            var newTile = self.$('.o_dynamic_dashboard').children().last();
                            self.$('.grid-stack').data('gridstack').addWidget(newTile, block.x, block.y, block.width, block.height, block.autoPosition);
                        } else {  // Block type = 'chart'
                            self.$('.o_dynamic_dashboard').append(QWeb.render('DynamicDashboardChart', {widget: block}));
                            // Check if 'x_axis' is present in block
                            if (!('x_axis' in block)) {
                                return false;
                            }
                            // Set up and render the chart using Chart.js
                            var type = block['graph_type'];
                            var newChartContainer = self.$('.o_dynamic_dashboard').children().last();
                            var chart_type = 'self.get_values_' + `${block['graph_type']}(block)`
                            new Chart(self.$('.chart_graphs').last(), {
                                type: block['graph_type'],
                                data: eval(chart_type)[0],
                                options: eval(chart_type)[1]
                            });
                            // Add the new chart container to the Gridstack layout at the original position
                            self.$('.grid-stack').data('gridstack').addWidget(newChartContainer, block.x, block.y, block.width, block.height, block.autoPosition);
                        }
                    }
                });
            });
            // Initialize Gridstack
            self.gridstack_init(self);
        },
        //Function to clear search box and call the functon on_reverse_breadcrumb().
        clear_search: function () {
            self.$("#search-input-chart").val("");
            self.$("#theme-change-icon").show();
            self.$("#edit_layout").show();
            self.$("#save_layout").hide();
            self.$(".date-inputs").show();
            self.block_ids = [];
            self.on_reverse_breadcrumb();
        },
        //Function to edit blocks and redirect to the model dashboard.block
        _onClick_block_setting: function (event) {
            event.stopPropagation();
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dashboard.block',
                view_mode: 'form',
                res_id: parseInt($(event.currentTarget).closest('.block').attr('data-id')),
                views: [[false, 'form']],
                context: {'form_view_initial_mode': 'edit'},
            }, {on_reverse_breadcrumb: self.on_reverse_breadcrumb})
        },
        //While click on cross icon, the block will be deleted.
        _onClick_block_delete: function (event) {
            event.stopPropagation();
            bootbox.confirm({//Popup to conform delete
                message: "Are you sure you want to delete this item?",
                title: "Delete confirmation",
                buttons: {
                    cancel: {
                        label: 'NO, GO BACK',
                        className: 'btn-primary'
                    },
                    confirm: {
                        label: 'YES, I\'M SURE',
                        className: 'btn-danger'
                    }
                },
                //Function to unlink block
                callback: function (result) {
                    if (result) {
                        rpc.query({
                            model: 'dashboard.block',
                            method: 'unlink',
                            args: [parseInt($(event.currentTarget).closest('.block').attr('data-id'))], // ID of the record to unlink
                        }).then(function (result) {
                             location.reload()
                            self.on_reverse_breadcrumb();
                        }).catch(function (error) {
                        });
                    } else {
                        // Do nothing
                    }
                }
            });
        },
        // Method for converting to camel case
        convertToCamelCase: function (chartType) {
            switch (chartType) {
                case "bar":
                    return "Bar";
                case "radar":
                    return "Radar";
                case "pie":
                    return "Pie";
                case "line":
                    return "Line";
                case "doughnut":
                    return "Doughnut";
                default:
                    // If the chart type is not recognized, you can handle it accordingly
                    return chartType;
            }
        },
        //Fetch data and create chart or tile
        _onClick_add_block: function (e) {
            var type = $(e.currentTarget).attr('data-type');
            if (type == 'graph') {
                var chart_type = $(e.currentTarget).attr('data-chart_type');
            }
            if (type === 'tile') {
                var randomColor = '#' + ('000000' + Math.floor(Math.random() * 16777216).toString(16)).slice(-6);
                this.do_action({// Redirect to dashboard.block
                    type: 'ir.actions.act_window',
                    res_model: 'dashboard.block',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    context: {
                        'form_view_initial_mode': 'edit',
                        'default_name': 'New Tile',
                        'default_type': type,
                        'default_height': 2,
                        'default_width': 2,
                        'default_tile_color': randomColor,
                        'default_text_color': '#FFFFFF',
                        'default_fa_icon': 'fa fa-bar-chart',
                        'default_client_action_id': parseInt(self.action_id)
                    },
                    on_close: function () {
                        window.location.reload();
                    }
                });
            } else {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'dashboard.block',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    context: {
                        'form_view_initial_mode': 'edit',
                        'default_name': 'New ' + self.convertToCamelCase(chart_type),
                        'default_type': type,
                        'default_height': 5,
                        'default_width': 4,
                        'default_graph_type': chart_type,
                        'default_graph_size': 'col-lg-4',
                        'default_fa_icon': 'fa fa-bar-chart',
                        'default_client_action_id': parseInt(self.action_id)
                    },
                    on_close: function(){
                        window.location.reload();
                    }
                });
            }
            // Fetching saved layout from localstorage memory.
        },
        // Function to hide edit_layout button and show save_layout button. and also work the function gridstack_on(self)
        _onClick_edit_layout: function (e) {
            e.stopPropagation();
            self.$(".date-inputs").hide();
            self.$("#edit_layout").hide();
            self.$("#save_layout").show();
            self.gridstack_on(self);
        },
        //Function to save the edited value
        _onClick_save_layout: function (e) {
            e.stopPropagation();
            self.$(".date-inputs").show();
            self.$("#edit_layout").show();
            self.$("#save_layout").hide();
            var grid_data_list = [];
            this.$el.find('.grid-stack-item').each(function () {
                grid_data_list.push({
                    'id': $(this).data('id'),
                    'x': $(this).data('gs-x'),
                    'y': $(this).data('gs-y'),
                    'width': $(this).data('gs-width'),
                    'height': $(this).data('gs-height')
                })
            });
            this._rpc({
                model: 'dashboard.block',
                method: 'get_save_layout',
                args: [[], this.action_id, grid_data_list]
            });
            self.gridstack_off(self);
        },
        // Function to view the tree view of the tile.
        _onClick_tile: function (e) {
            e.stopPropagation();
            ajax.jsonRpc('/tile/details', 'call', {
                'id': $(e.currentTarget).attr('data-id')
            }).then(function (result) {
                if (result['model_name']) {
                    self.do_action({
                        name: result['model_name'],
                        type: 'ir.actions.act_window',
                        res_model: result['model'],
                        view_mode: 'tree,form',
                        views: [[false, 'list'], [false, 'form']],
                        domain: result['filter']
                    });
                } else {
                    Dialog.alert(this, "Configure the tile's model and parameters.");
                }
            });
        },
    });
    core.action_registry.add('advanced_dynamic_dashboard', DynamicDashboard);
    return DynamicDashboard;
});
