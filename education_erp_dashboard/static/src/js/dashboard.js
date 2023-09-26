odoo.define("education_erp_dashboard.EducationalDashboard", function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'EducationalDashboard',
     /* Loading the dashboard template */
     init: function(parent, context) {
                this._super(parent, context);
                this.dashboard_templates = ['MainSection'];
            },
     /* Showing the total exam result and total attendance and hiding
            the academic wise exam result and class wise attendance
            when loading */
     start: function() {
            var self = this;
            self.set("title", 'Dashboard');
            return self._super().then(function() {
            self.$('.academic_exam_result').hide();
            self.$('.exam_result').show();
            self.$('.class_attendance_today').hide();
            self.$('.total_attendance_today').show();
            /* Rendering the dashboard, graphs and filters */
                self.render_dashboards();
                self.render_graphs();
                self.render_filters();
            });
        },
    /* This function is called before the actual start */
    willStart: function(){
        var self = this;
        return self._super()
    },
    /* Function to render dashboard */
    render_dashboards: function() {
            var self = this;
            self.fetch_data()
            var templates = []
            var templates = ['MainSection'];
            _.each(templates, function(template) {
                self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}))
            });
        },
    /* RPC call to fetch the count of applications, students, faculties,
        amenities and total exams */
        fetch_data: function() {
        var self = this;
        rpc.query({
            model: 'erp.dashboard',
            method: "erp_data",
        }).then(function (result) {
                self.$('#all_applications').append('<span>' + result.applications + '</span>');
                self.$('#all_students').append('<span>' + result.students + '</span>');
                self.$('#all_faculties').append('<span>' + result.faculties + '</span>');
                self.$('#all_amenities').append('<span>' + result.amenities + '</span>');
                self.$('#all_exams').append('<span>' + result.exams + '</span>');
            });
        },
        /* Click events for the tiles and change event for the filters */
        events:{
        'click #all_applications':'application_list',
        'click #all_students':'student_list',
        'click #all_faculties':'faculty_list',
        'click #all_amenities':'amenity_list',
        'click #all_attendance':'attendance_list',
        'click #exams':'exam_result',
        'click #timetable':'timetable',
        'click #promotion':'promotions',
        'change #select_period': function(e){
            e.preventDefault();
            if(e.target.value == 'select'){
            this.$('.academic_exam_result').hide();
            this.$('.exam_result').show();
            this.render_exam_result_pie();
            }
            else{
            this.$('.exam_result').hide();
            this.$('.academic_exam_result').show();
            this.get_academic_exam_result(e.target.value);
            }
          },
        'change #select_class': function(e){
            e.preventDefault();
            if(e.target.value == 'select'){
            this.$('.class_attendance_today').hide();
            this.$('.total_attendance_today').show();
            this.render_attendance_doughnut();
            }
            else{
             this.$('.total_attendance_today').hide();
             this.$('.class_attendance_today').show();
             this.get_class_attendance(e.target.value);
            }
          }
        },
    /* Functions that to show the details on click event */
    /* Click event function to show the applications */
        application_list:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Applications",
                 res_model: "education.application",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the students */
      student_list:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Students",
                 res_model: "education.student",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the faculties */
      faculty_list:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Faculties",
                 res_model: "education.faculty",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the amenities */
      amenity_list:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Amenities",
                 res_model: "education.amenities",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the attendance list */
      attendance_list:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Attendance",
                 res_model: "education.attendance",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the exam results */
      exam_result:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Exam Result",
                 res_model: "education.exam",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the time table */
      timetable:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Timetable",
                 res_model: "education.timetable",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Click event function to show the promotions */
      promotions:function(e){
        e.preventDefault();
             this.do_action({
                 type: "ir.actions.act_window",
                 name: "Student Promotions",
                 res_model: "education.student.final.result",
                 views: [[false,'list'],[false,'form']],
                 target: 'current',
                 view_type : 'list',
                 view_mode : 'list',
               });
      },
    /* Calling the functions to creates charts */
      render_graphs:function(){
      var self = this;
      self.render_total_application_graph();
      self.render_exam_result_pie();
      self.render_attendance_doughnut();
      self.render_rejected_accepted_applications();
      self.render_student_strength();
      self.render_class_wise_average_marks();
      },
    /* Calling the filter functions */
      render_filters:function(){
      var self = this;
      self.render_pie_chart_filter();
      self.render_doughnut_chart_filter();
      },
    /* Function to create a bar chart to show application counts in each
    academic year */
      render_total_application_graph:function(){
            var self = this
            var ctx = self.$(".application_count");
            rpc.query({
                model: "erp.dashboard",
                method: "get_all_applications",
            }).then(function (result) {
                var data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: 'Application',
                        data: Object.values(result),
                        backgroundColor: [
                            "#87cefa",
                            "#b0c4de",
                            "#20b2aa",
                        ],
                        borderColor: [
                            "#87cefa",
                            "#b0c4de",
                            "#20b2aa",
                        ],
                        borderWidth: 1
                    },]
                };
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0
                            }
                        }]
                    }
                };
                //Create Chart class object
                new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: {
                        responsive:true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                        },
                    }
                });
            });
      },
    /* Function to create a bar chart that shows the count of accepted and
    rejected applications */
      render_rejected_accepted_applications:function(){
            var self = this
            var ctx = self.$(".rejected_accepted_count");
            rpc.query({
                model: "erp.dashboard",
                method: "get_rejected_accepted_applications",
            }).then(function (result) {
                var data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: 'Application',
                        data: Object.values(result),
                        backgroundColor: [
                            "#778899",
                            "#f08080",
                        ],
                        borderColor: [
                            "#778899",
                            "#f08080",
                        ],
                        borderWidth: 1
                    },]
                };
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0
                            }
                        }]
                    }
                };
                //Create Chart class object
                new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: {
                        scales : {
                            y : {
                                beginAtZero: true,
                                suggestedMin: 0,
                            }
                        },
                        responsive:true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                        },
                    }
                });
            });
      },
    /* Function to create a pie chart that shows the exam results */
        chart_total_result : false,
        render_exam_result_pie:function(){
            var self = this;
            if (this.chart_total_result){
                this.chart_total_result.destroy()
            }
            var ctx = self.$(".exam_result")[0].getContext('2d');
            rpc.query({
                model: "erp.dashboard",
                method: "get_exam_result"
            }).then(function (result) {
            var data;
            if (! result.Fail && ! result.Pass){
                  data = {
                    labels : ['No data'],
                    datasets: [{
                        label: "No Result",
                        data: [1],
                        backgroundColor: [
                            "#f6f7f9"
                        ],
                        borderColor: [
                            "#f6f7f9"
                        ],
                        borderWidth: 1
                    },]
                };
                }
                else{
                data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: "Exam Result",
                        data: Object.values(result),
                        backgroundColor: [
                            "#003f5c",
                            "#dc143c"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#dc143c",
                        ],
                        borderWidth: 1
                    },]
                };
                }
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
                /* Create Chart class object */
                 self.chart_total_result = new Chart(ctx, {
                    type: "pie",
                    data: data,
                    options: options
                });
            });
        },
      /* Function to create a doughnut chart that shows attendance details */
        chart_total_attendance : false,
        render_attendance_doughnut:function(){
            var self = this;
            if(this.chart_total_attendance){
                    this.chart_total_attendance.destroy()
                }
            var ctx = self.$(".total_attendance_today")[0].getContext('2d');
            rpc.query({
                model: "erp.dashboard",
                method: "get_attendance"
            }).then(function (result) {
                var data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: "Attendance",
                        data: Object.values(result),
                        backgroundColor: [
                            "#006400",
                            "#e9967a"
                        ],
                        borderColor: [
                            "#006400",
                            "#e9967a",
                        ],
                        borderWidth: 1
                    },]
                };
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
                /* Create Chart class object */
                self.chart_total_attendance = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },
      /* Function to create a line chart that shows the class wise student strength */
        render_student_strength:function(){
            var self = this
            var ctx = self.$(".student_strength");
            rpc.query({
                model: "erp.dashboard",
                method: "get_student_strength",
            }).then(function (result) {
                var data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: 'Student Strength',
                        data: Object.values(result),
                        Color: [
                            "#8b0000",
                        ],
                        borderColor: [
                            "#8b0000",
                        ],
                        borderWidth: 1
                    },]
                };
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
                //Create Chart class object
                new Chart(ctx, {
                    type: "line",
                    data: data,
                    options: {
                        responsive:true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                        },
                    }
                });
            });
      },
    /* Function to create a bar chart that shows the average marks in each class */
      render_class_wise_average_marks:function(){
            var self = this
            var ctx = self.$(".average_marks");
            rpc.query({
                model: "erp.dashboard",
                method: "get_average_marks",
            }).then(function (result) {
            var data
            if (Object.values(result) == 0){
                  data = {
                    labels : ['No data'],
                    datasets: [{
                        label: "No Marks",
                        data: [1],
                        backgroundColor: [
                            "#f6f7f9"
                        ],
                        borderColor: [
                            "#f6f7f9"
                        ],
                        borderWidth: 1
                    },]
                };
                }
            else{
               data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: 'Average Marks',
                        data: Object.values(result),
                        backgroundColor: [
                            "#cd5c5c",
                        ],
                        borderColor: [
                            "#cd5c5c",
                        ],
                        borderWidth: 1
                    },]
                };
                }
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
                /* Create Chart class object */
                new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: {
                        scales : {
                            y : {
                                beginAtZero: true,
                                suggestedMin: 0,
                            }
                        },

                        responsive:true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                    }
                    }
                });
            });
      },
    /* Function to add the filter option */
      render_pie_chart_filter:function(){
      var self = this
      rpc.query({
                model: "erp.dashboard",
                method: "get_academic_year",
            }).then(function (result) {
                  self.$('#select_period').append('<option value=' + 'select' + '>' + 'Total Result' + '</option>')
                for (let key in result){
                  self.$('#select_period').append('<option value=' + key + '>' + result[key] + '</option>')
            }
      })
    },
   /* Function to get academic wise exam result and to create chart accordingly */
    chart_academy_result : false,
    get_academic_exam_result:function(academic_year){
      var self = this;
      if (this.chart_academy_result){
                this.chart_academy_result.destroy()
            }
      var ctx = self.$(".academic_exam_result")[0].getContext('2d');
      rpc.query({
                model: "erp.dashboard",
                method: "get_academic_year_exam_result",
                args: [academic_year]
            }).then(function (result) {
            var data
            if (! result.Fail && ! result.Pass){
                  data = {
                    labels : ['No data'],
                    datasets: [{
                        label: "No Result",
                        data: [1],
                        backgroundColor: [
                            "#f6f7f9"
                        ],
                        borderColor: [
                            "#f6f7f9"
                        ],
                        borderWidth: 1
                    },]
                };
                }
            else{
            data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: "Exam Result",
                        data: Object.values(result),
                        backgroundColor: [
                            "#003f5c",
                            "#dc143c"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#dc143c",
                        ],
                        borderWidth: 1
                    },]
                };
                }
                //Options to add appearance for the graph
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
                self.chart_academy_result = new Chart(ctx, {
                    type: "pie",
                    data: data,
                    options: options
                });
            });
      },
    /* Function to add filter option for doughnut chart */
      render_doughnut_chart_filter:function(){
      var self = this
      rpc.query({
                model: "erp.dashboard",
                method: "get_classes",
            }).then(function (result) {
                  self.$('#select_class').append('<option value=' + 'select' + '>' + 'Total Attendance' + '</option>')
                for (let key in result){
                  self.$('#select_class').append('<option value=' + key + '>' + result[key] + '</option>')
                  }
            })
      },
    /* Function to get class wise attendance and to create chart accordingly */
      chart_class_attendance : false,
      get_class_attendance:function(clas){
      var self = this;
      if(this.chart_class_attendance){
         this.chart_class_attendance.destroy()
       }
      var ctx = self.$(".class_attendance_today")[0].getContext('2d');
      rpc.query({
                model: "erp.dashboard",
                method: "get_class_attendance_today",
                args: [clas]
            }).then(function (result) {
            var data = {
                    labels : Object.keys(result),
                    datasets: [{
                        label: "Attendance",
                        data: Object.values(result),
                        backgroundColor: [
                             "#006400",
                             "#e9967a"
                        ],
                        borderColor: [
                            "#006400",
                            "#e9967a"
                        ],
                        borderWidth: 1
                    },]
                };
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 16
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                            }
                        }]
                    }
                };
              /* Create Chart class object */
                self.chart_class_attendance = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
      },
    })
    core.action_registry.add('erp_dashboard_tag', DashBoard);
    return DashBoard;
 });
