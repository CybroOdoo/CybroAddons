/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { useRef, Component, onMounted, useState} from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { WebClient } from "@web/webclient/webclient";
class ProductExpiryDashboard extends Component {
    static template = "odoo_product_expiry_dashboard.expiry_dashboard_template";
    setup(){
        this.actionService = useService("action");
        this.rootRef = useRef("root");
		this.state = useState({
            expire_quantity: {},
        });
           onMounted(async () => {
            await this.render_graphs();
        });
    }

    render_graphs(){
        this.fetch_products_expiry()
        this.render_expired_products_graph();
         this.near_exp_products()
         this.expiry_by_category()
         this.near_exp_category()
         this.get_expire_product_location()
         this.get_expire_product_warehouse()
        }

    FilterDate(ev) {
      var start_date = this.rootRef.el.querySelector('#start_date').value;
      var end_date = this.rootRef.el.querySelector('#end_date').value;
      if (start_date && end_date){
      this.fetch_products_expiry(start_date, end_date)
      this.render_expired_products_graph(start_date, end_date)
      this.expiry_by_category(start_date, end_date)
}
    }

   fetch_products_expiry(start_date, end_date) {
    //Fetch the data to be displayed on the tiles of the dashboard.
      var date_dict = { 'start_date': start_date, 'end_date': end_date }
      var self = this
      rpc('/web/dataset/call_kw/stock.lot/get_product_expiry',{
                model: 'stock.lot',
                method: 'get_product_expiry',
                args: [date_dict],
                kwargs: {},
            }).then(function (result) {
            self.state.expire_quantity = result
      })
    }

    render_expired_products_graph(start_date, end_date) {
    //Function for rendering the graph of expired products
      let chartStatus = Chart.getChart('expired_product_count');
      if (chartStatus != undefined) {
        chartStatus.destroy();
      }
      var product_array = []
      var expired_qty_array = []
      var date_dict = { 'start_date': start_date, 'end_date': end_date }
      var self = this
      let data = rpc('/web/dataset/call_kw/stock.lot/get_expired_product',{
                model: 'stock.lot',
                method: 'get_expired_product',
                args: [date_dict],
                kwargs: {},
            }).then(function (result) {
              for (const [index, name] of Object.entries(result)) {
                    product_array.push(index);
                    expired_qty_array.push(name);
                }
        if (product_array.length != 0) {
          const ctx = self.rootRef.el.querySelector('#expired_product_count')
          new Chart(ctx, {
            type: 'pie',
            data: {
              labels: product_array,
              datasets: [{
                label: 'Quantity',
                data: expired_qty_array,
                borderWidth: 0.5,
                backgroundColor: ["#e60000", "#d279d2", "#4099ff","#2ed8b6",
                "#FFB64D, #ffcb80"],
              }]
            },
          });
          self.rootRef.el.querySelector('.expired_produt_count_chart').style.display = "none";
        }
        else {
         self.rootRef.el.querySelector('.expired_produt_count_chart').style.display = "";
        }
      })
    }

    expiry_by_category(start_date, end_date) {
    //Function for rendering the graph of product's expiry based on their
    //category
      let chartStatus = Chart.getChart('expired_product_category_count');
      if (chartStatus != undefined) {
        chartStatus.destroy();
      }
      var product_category_array = []
      var expired_qty_array = []
      var date_dict = { 'start_date': start_date, 'end_date': end_date }
      var self = this
      let data = rpc('/web/dataset/call_kw/stock.lot/get_expired_product',{
                model: 'stock.lot',
                method: 'get_product_expiry_by_category',
                args: [date_dict],
                kwargs: {},
            }).then(function (result) {
                for (const [index, name] of Object.entries(result)) {
                product_category_array.push(index);
                expired_qty_array.push(name);
            }
        if (product_category_array.length != 0) {
          const ctx = self.rootRef.el.querySelector('#expired_product_category_count')
          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: product_category_array,
              datasets: [{
                label: 'Quantity',
                data: expired_qty_array,
                borderWidth: 1,
                backgroundColor: ["#4099ff", "#e60000", "#d279d2", "#2ed8b6",
                "#FFB64D, #ffcb80"],
              }]
            },
          });
          self.rootRef.el.querySelector('.expired_product_catg_count').style.display = "none";
        }
        else {
          self.rootRef.el.querySelector('.expired_product_catg_count').style.display = "";
        }
      })
    }
    expired_click = () => {
    //Click event of expired products tile
    this.click_event(-1,"Expired")
    }
    today_click = () => {
    //Click event of expire today tile
      this.click_event(0,"Expire Today");
    }
    one_day_click = () => {
    //Click event of expire in one day tile
      this.click_event(1,"Expiry in One Day");
    }
    seven_day_click = () => {
    //Click event of expire in one 7 days tile
      this.click_event(7, "Expiry in Seven Days");
    }
    thirty_day_click = () => {
    //Click event of expire in 30 days tile
      this.click_event(30, "Expiry in Thirty Days");
    }
    one_twenty_day_click = () => {
    //Click event of expire in 120 day tile
      this.click_event(120, "Expiry in One Twenty Days");
    }

    click_event(days,name){
    //Function for displaying corresponding products while clicking on a tile
      var today = new Date();
      var start_date = this.rootRef.el.querySelector('#start_date').value;
      var end_date = this.rootRef.el.querySelector('#end_date').value;
      var Domain = []
      if(start_date != ""){
        Domain.push(['expiration_date', '>=', start_date])
      }
       if(end_date != ""){
        Domain.push(['expiration_date', '<=', end_date])
      }
      
      function formatDateTime(d, is_end) {
          var month = '' + (d.getMonth() + 1),
              day = '' + d.getDate(),
              year = d.getFullYear();
          if (month.length < 2) month = '0' + month;
          if (day.length < 2) day = '0' + day;
          var timeStr = is_end ? " 23:59:59" : " 00:00:00";
          return [year, month, day].join('-') + timeStr;
      }
      
      var today_start = formatDateTime(today, false);
      var tomorrow = new Date();
      tomorrow.setDate(today.getDate() + 1);
      var tomorrow_start = formatDateTime(tomorrow, false);
      
      if(days==-1){
        Domain.push(['expiration_date', '<', today_start])
      } else if (days == 0) {
        var end_date_str = formatDateTime(today, true);
        Domain.push(['expiration_date', '>=', today_start], ['expiration_date', '<=', end_date_str]);
      } else {
        var end_date_target = new Date();
        end_date_target.setDate(today.getDate() + days);
        var end_date_str = formatDateTime(end_date_target, true);
        Domain.push(['expiration_date', '>=', tomorrow_start], ['expiration_date', '<=', end_date_str]);
      }

      this.actionService.doAction({
        name: name,
        type: 'ir.actions.act_window',
        view_mode: 'list',
        res_model: 'stock.lot',
        views: [[false, 'list'], [false, 'form']],
        domain: Domain,
        target: 'current',
      })
    }

    near_exp_category() {
    //Function for rendering graph of products expiring in 7 days based on
    //their category
      var product_category_array = []
      var nearby_expire_qty = []
      var self = this
      rpc('/web/dataset/call_kw/stock.lot/get_near_expiry_category',{
                model: 'stock.lot',
                method: 'get_near_expiry_category',
                args: [],
                kwargs: {},
            }).then(function (result) {
           for (const [index, name] of Object.entries(result)) {
                    product_category_array.push(index);
                    nearby_expire_qty.push(name);
                }
        if(product_category_array.length != 0){
        const ctx = self.rootRef.el.querySelector('#nearby_expire_catg')
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: product_category_array,
            datasets: [{
              label: 'Quantity',
              data: nearby_expire_qty,
             backgroundColor: ["#FFB64D", "#4099ff", "#e60000", "#d279d2",
             "#2ed8b6", "#ffcb80"],
              borderWidth: 1
            }]
          },
        })
        self.rootRef.el.querySelector('.nearby_expire_cat').style.display = "none";
        }else{
        self.rootRef.el.querySelector('.nearby_expire_cat').style.display = "";
        }
      })
    }

    near_exp_products() {
    //Function for rendering graph of products expiring in 7 days
      var product_array = []
      var nearby_expire_qty = []
      var self = this
      rpc('/web/dataset/call_kw/stock.lot/get_near_expiry_product',{
                model: 'stock.lot',
                method: 'get_near_expiry_product',
                args: [],
                kwargs: {},
            }).then(function (result) {
        for (const [index, name] of Object.entries(result)) {
        product_array.push(index);
        nearby_expire_qty.push(name);
    }
        if (product_array.length != 0) {
          const ctx = self.rootRef.el.querySelector('#nearby_expire_product')
          new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: product_array,
              datasets: [{
                label: 'Quantity',
                data: nearby_expire_qty,
                borderWidth: 1,
               backgroundColor: ["#ffcb80", "#4099ff", "#e60000", "#d279d2",
                "#2ed8b6", "#FFB64D"],
              }]
            },
          });
          self.rootRef.el.querySelector('.nearby_expire_prod').style.display = "none";
        }else{
        self.rootRef.el.querySelector('.nearby_expire_prod').style.display = "";
        }
      })
    }

    get_expire_product_location() {
     //Function for rendering graph of expiring products based on
    //their location
      var product_location_array = []
      var nearby_expire_qty = []
      var self = this
      rpc('/web/dataset/call_kw/stock.lot/get_expire_product_location',{
                model: 'stock.lot',
                method: 'get_expire_product_location',
                args: [],
                kwargs: {},
            }).then(function (result) {
       for (const [index, name] of Object.entries(result)) {
        product_location_array.push(index);
        nearby_expire_qty.push(name);
    }
        if (product_location_array.length != 0){
        const ctx = self.rootRef.el.querySelector('#nearby_expire_location')
        new Chart(ctx, {
          type: 'pie',
          data: {
            labels: product_location_array,
            datasets: [{
              label: 'Quantity',
              data: nearby_expire_qty,
              backgroundColor: ["#ffcb80", "#FFB64D", "#4099ff", "#e60000",
               "#d279d2", "#2ed8b6"],
              borderWidth: 1
            }]
          },
        })
       self.rootRef.el.querySelector('.nearby_expire_loc').style.display = "none";
        }else{
       self.rootRef.el.querySelector('.nearby_expire_loc').style.display = "";
        }
      })
    }
//
    get_expire_product_warehouse() {
    //Function for rendering graph of expiring products based on
    //their warehouse
      var product_warehouse_array = []
      var nearby_expire_qty = []
      var self = this
      rpc('/web/dataset/call_kw/stock.lot/get_expire_product_warehouse',{
                model: 'stock.lot',
                method: 'get_expire_product_warehouse',
                args: [],
                kwargs: {},
            }).then(function (result) {
       for (const [index, name] of Object.entries(result)) {
            product_warehouse_array.push(index);
            nearby_expire_qty.push(name);
        }
        if (product_warehouse_array.length != 0){
        const ctx = self.rootRef.el.querySelector('#nearby_expire_warehouse')
        new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: product_warehouse_array,
            datasets: [{
              label: 'Quantity',
              data: nearby_expire_qty,
              borderWidth: 1,
              backgroundColor: ["#4099ff", "#e60000", "#ffcb80", "#FFB64D",
               "#d279d2", "#2ed8b6"],
            }]
          },
        })
        self.rootRef.el.querySelector('.nearby_expire_wh').style.display = "none";
        }else{
         self.rootRef.el.querySelector('.nearby_expire_wh').style.display = "";
        }
      })
    }
    }
registry.category("actions").add("product_expiry", ProductExpiryDashboard);
