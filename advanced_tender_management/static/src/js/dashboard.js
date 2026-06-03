/**@odoo-module **/

import { Component,onWillStart,onMounted,useRef,useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"
import { session } from "@web/session";
const actionRegistry = registry.category("actions");

class TenderDashboard extends Component {
    setup() {
        this.orm = useService("orm");

        this.ctx1=useRef("tender_type_graph");
        this.ctx2=useRef("category_type_graph");
        this.ctx3=useRef("tender_timeline_chart");

        this.tenderCount=useRef("tender_count");
        this.vendorCount=useRef("vendor_count");
        this.countryCount=useRef("tender_country_count")
        this.activeTenderCount=useRef("active_tenders_count");
        this.tenderCategoryCount=useRef("tender_categories");
        this.activeBidCount=useRef("active_bid_count");
        this.qualifiedBidCount=useRef("qualified_bid_count");
        this.disqualifiedBidCount=useRef("disqualified_bid_count");
        this.editRequestCount=useRef("edit_requests_count");
        this.preQualificationCount=useRef("pre_qualification_count");


        onWillStart(async () => {
                await loadBundle("web.chartjs_lib");
                this.data = await this.orm.call('tender.management','get_tender_details',[[]],{})
            }),
        onMounted(() => {
            this.renderTileValues();
            this.renderTenderTypeChart();
            this.categoryTypeChart();
            this.tenderTimelineChart();
        })
    }
    async renderTileValues(){
        this.tenderCount.el.textContent=this.data['tender_count']
        this.vendorCount.el.textContent=this.data['vendors_count']
        this.activeTenderCount.el.textContent=this.data['active_tenders_count']
        this.tenderCategoryCount.el.textContent=this.data['tender_categories_count']
        this.activeBidCount.el.textContent=this.data['active_bid_count']
        this.qualifiedBidCount.el.textContent=this.data['qualified_bid_count']
        this.disqualifiedBidCount.el.textContent=this.data['disqualified_bid_count']
        this.editRequestCount.el.textContent=this.data['edit_request_count']
        this.preQualificationCount.el.textContent=this.data['pre_qualification_count']
        this.countryCount.el.textContent=this.data['tender_location_count']
    }
    async tenderTimelineChart(){
        var ctx3 = this.ctx3.el.getContext('2d');
        var Tenders= this.data['tender_timeline_data']['tenders']
        var TenderTimelineCount=this.data['tender_timeline_data']['tender_timeline_data']
        this.myChart3 = new Chart(ctx3, {
            type: 'line',
            data: {
                labels: Tenders,
                datasets: [{
                    label: 'Tender Timeline Chart',
                    data: TenderTimelineCount,
                }]
            },
            options: {
                scales: {
                  x: {
                    grid: {
                      display: false
                    }
                  },
                  y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value + ' days';
                            }
                        }
                    }
                }
            }
        });
        this.currentTenderTimelineChart = this.myChart3
    }
    async categoryTypeChart(){
        var ctx2 = this.ctx2.el.getContext('2d');
        var categoryType= this.data['tender_category_data']['category_types']
        var categoryTypeCount=this.data['tender_category_data']['category_type_count']
        this.myChart2 = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: categoryType,
                datasets: [{
                    label: 'Tender Category Chart',
                    data: categoryTypeCount,
                }]
            },
            options: {
                scales: {
                  x: {
                    grid: {
                      display: false
                    }
                  },
                  y: {
                    grid: {
                      display: false
                    }
                  }
                }
            }
        });
        this.currentCategoryTypeChart = this.myChart2
    }

    async renderTenderTypeChart(){
        var ctx1 = this.ctx1.el.getContext('2d');
        var tenderType= this.data['tender_type_data']['tender_types']
        var tenderTypeCount=this.data['tender_type_data']['tender_type_count']
        this.myChart1 = new Chart(ctx1, {
            type: 'pie',
            data: {
                labels: tenderType,
                datasets: [{
                    label: 'Tender Type Chart',
                    data: tenderTypeCount,
                }]
            },
            options: {}
        });
        this.currentTenderTypeChart = this.myChart1
    }
}
TenderDashboard.template = "advanced_tender_management.TenderDashboard";
actionRegistry.add("tender_dashboard_tag", TenderDashboard);