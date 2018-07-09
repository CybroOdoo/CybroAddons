odoo.define('target_achievement_invoice.dashboard', function (require) {
"use strict";
    var core = require('web.core');
    var CrmDashboard = require('sales_team.dashboard');
    var Model = require('web.Model');
    var QWeb = core.qweb;
    CrmDashboard.include({
        render: function() {
            this._super();
            var self = this;
            self.fetch_data().then(function(result) {
                var sales_dashboard = QWeb.render('sales_team.SalesDashboard', {
                    widget: self,
                    show_demo: self.show_demo,
                    values: result,
                });

                var pie_div = "<div class='dashboard_donut_chart'></div>";
                var $pie_div = $(pie_div);

                var width = 550;
                var height = 350;
                var radius = height/2;
                var color = d3.scale.category10();
                // getting data to show
                var uid = self.dataset.context.uid;
                new Model('crm.team').call('find_target', ['', uid]).done(function (res_data) {
                    console.log("res_data:  ", res_data)
                    var dataset = res_data;

                    var pie=d3.layout.pie()
                            .value(function(d){return d.percent})
                            .sort(null)
                            .padAngle(.03);

                    var w=300,h=300;

                    var outerRadius=w/2;
                    var innerRadius=85;

                    var color = d3.scale.category10();

                    var arc=d3.svg.arc()
                            .outerRadius(outerRadius)
                            .innerRadius(innerRadius);

                    var svg=d3.select($pie_div[0])
                            .append("svg")
                            .attr({
                                width:w+300,
                                height:h,
                                class:'shadow'
                            }).append('g')
                            .attr({
                                transform:'translate('+w/2+','+h/2+')'
                            });
                    var path=svg.selectAll('path')
                            .data(pie(dataset))
                            .enter()
                            .append('path')
                            .attr({
                                d:arc,
                                fill:function(d,i){
                                    return color(d.data.name);
                                }
                            });

                    var text=svg.selectAll('text')
                      .data(pie(dataset))
                      .enter()
                      .append("text")
                      .attr("transform", function (d) {
                          return "translate(" + arc.centroid(d) + ")";
                      })
                      .attr("dy", ".4em")
                      .attr("text-anchor", "middle")
                      .text(function(d){
                          return d.data.percent+"%";
                      })
                      .style({
                          fill:'black',
                          'font-size':'10px',
                          'color':'black'
                      });
                    var legendRectSize=20;
                    var legendSpacing=7;
                    var legendHeight=legendRectSize+legendSpacing;


                    var legend=svg.selectAll('.legend')
                      .data(color.domain())
                      .enter()
                      .append('g')
                      .attr({
                          class:'legend',
                          transform:function(d,i){
                              //Just a calculation for x and y position
                              return 'translate(185,' + ((i*legendHeight)-65) + ')';
                          }
                      });
                    legend.append('rect')
                      .attr({
                          width:legendRectSize,
                          height:legendRectSize,
                          rx:70,
                          ry:20
                      })
                      .style({
                          fill:color,
                          stroke:color
                      });

                    legend.append('text')
                      .attr({
                          x:75,
                          y:15
                      })
                      .text(function(d){
                          return d;
                      }).style({
                          fill:'#929DAF',
                          'font-size':'14px'
                      });

                     var target = svg.select('target')
                        .data("Target")
                        .enter()
                        .append('g');

                    var html_string = $pie_div[0].outerHTML;
                    $(html_string).prependTo(self.$el);
                });
            });
            return;
    },
});

});

