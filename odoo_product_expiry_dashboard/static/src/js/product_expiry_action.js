odoo.define('odoo_product_expiry_dashboard.product_expiry', function (require) {
  'use strict';
  var AbstractAction = require('web.AbstractAction');
  var core = require('web.core');
  var rpc = require('web.rpc');
  var ProductExpiryDashboard = AbstractAction.extend({
    template: 'ProductExpiryDashboard',
    events: {
    //Events
    'change #start_date': 'filter_date',
    'change #end_date': 'filter_date',
    'click .expired': 'expired_click',
    'click .today': 'today_click',
    'click .one-day': 'one_day_click',
    'click .seven-day': 'seven_day_click',
    'click .thirty-day': 'thirty_day_click',
    'click .one-twenty-day': 'one_twenty_day_click'
    },
    start: function () {
    //Call functions to fetch the data to display on the dashboard
      this.fetch_products_expiry()
      this.render_expired_products_graph()
      this.expiry_by_category()
      this.near_exp_category()
      this.near_exp_products()
      this.product_expired_today()
      this.get_expire_product_location()
      this.get_expire_product_warehouse()
    },
    filter_date(ev) {
    //Works if start date or end date is changed. Fetch the data according to
    //the date chosen
      var start_date = this.$("#start_date").val()
      var end_date = this.$("#end_date").val()
      this.fetch_products_expiry(start_date, end_date)
      this.render_expired_products_graph(start_date, end_date)
      this.expiry_by_category(start_date, end_date)
    },
    fetch_products_expiry(start_date, end_date) {
    //Fetch the data to be displayed on the tiles of the dashboard.
      this.$('#expired').remove()
      this.$("#today").remove()
      this.$("#one_day").remove()
      this.$("#seven_day").remove()
      this.$("#thirty_day").remove()
      this.$("#one_twenty_day").remove()
      var date_dict = { 'start_date': start_date, 'end_date': end_date }
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_product_expiry',
        args: [date_dict]
      }).then(function (result) {
         $(".expired").append('<center>'
          + '<span style="font-size: xxx-large;" id="expired">' + result['expired'] + '</span>'
          + '</center>')
         $(".today").append('<center>'
          + '<span style="font-size: xxx-large;" id="today">' + result['today'] + '</span>'
          + '</center>')
        $(".one-day").append('<center>'
          + '<span style="font-size: xxx-large;" id="one_day">' + result['one_day'] + '</span>'
          + '</center>')
        $(".seven-day").append('<center>'
          + '<span style="font-size: xxx-large;" id="seven_day">' + result['seven_day'] + '</span>'
          + '</center>')
        $(".thirty-day").append('<center>'
          + '<span style="font-size: xxx-large;" id="thirty_day">' + result['thirty_day'] + '</span>'
          + '</center>')
        $(".one-twenty-day").append('<center>'
          + '<span style="font-size: xxx-large;" id="one_twenty_day">' + result['one_twenty_day'] + '</span>'
          + '</center>')
      })
    },
    product_expired_today() {
    //Function for fetching all products expiring today
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_product_expired_today'
      }).then(function (result) {
        $('.product_expired_heading').append('<p style="font-size: 38px;margin-top: -10px;">' + result + '</p>')
      })
    },
    render_expired_products_graph(start_date, end_date) {
    //Function for rendering the graph of expired products
      let chartStatus = Chart.getChart('expired_product_count');
      if (chartStatus != undefined) {
        chartStatus.destroy();
      }
      var product_array = []
      var expired_qty_array = []
      var date_dict = { 'start_date': start_date, 'end_date': end_date }
      let data = rpc.query({
        model: 'stock.production.lot',
        method: 'get_expired_product',
        args: [date_dict]
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_array.push(index)
          expired_qty_array.push(name)
        })
        if (product_array.length != 0) {
          const ctx = $('#expired_product_count')
          new Chart(ctx, {
            type: 'pie',
            data: {
              labels: product_array,
              datasets: [{
                label: 'Quantity',
                data: expired_qty_array,
                borderWidth: 1,
                backgroundColor: ["#e60000", "#d279d2", "#4099ff","#2ed8b6",
                "#FFB64D, #ffcb80"],
              }]
            },
          });
          $(".chart_heading").show()
        }
        else {
          $(".chart_heading").hide()
        }
      })
    },
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
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_product_expiry_by_category',
        args: [date_dict]
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_category_array.push(index)
          expired_qty_array.push(name)
        })
        if (product_category_array.length != 0) {
          const ctx = $('#expired_product_category_count')
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
        }
        else {
          $(".chart_heading").hide()
        }
      })
    },
    near_exp_products() {
    //Function for rendering graph of products expiring in 7 days
      var product_array = []
      var nearby_expire_qty = []
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_near_expiry_product',
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_array.push(index)
          nearby_expire_qty.push(name)
        })
        if (product_array.length != 0) {
          const ctx = $('#nearby_expire_product')
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
        }
      })
    },
   near_exp_category() {
    //Function for rendering graph of products expiring in 7 days based on
    //their category
      var product_category_array = []
      var nearby_expire_qty = []
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_near_expiry_category',
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_category_array.push(index)
          nearby_expire_qty.push(name)
        })
        const ctx = $('#nearby_expire_catg')
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
      })
    },
    get_expire_product_location() {
     //Function for rendering graph of expiring products based on
    //their location
      var product_location_array = []
      var nearby_expire_qty = []
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_expire_product_location',
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_location_array.push(index)
          nearby_expire_qty.push(name)
        })
        const ctx = $('#nearby_expire_location')
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
      })
    },
    get_expire_product_warehouse() {
    //Function for rendering graph of expiring products based on
    //their warehouse
      var product_warehouse_array = []
      var nearby_expire_qty = []
      rpc.query({
        model: 'stock.production.lot',
        method: 'get_expire_product_warehouse',
      }).then(function (result) {
        $.each(result, function (index, name) {
          product_warehouse_array.push(index)
          nearby_expire_qty.push(name)
        })
        const ctx = $('#nearby_expire_warehouse')
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
      })
    },
    expired_click(){
    //Click event of expired products tile
    this.click_event(-1,"Expired")
    },
    today_click() {
    //Click event of expire today tile
      this.click_event(0,"Expire Today");
    },
    one_day_click() {
    //Click event of expire in one day tile
      this.click_event(1,"Expiry in One Day");
    },
    seven_day_click() {
    //Click event of expire in one 7 days tile
      this.click_event(7, "Expiry in Seven Days");
    },
    thirty_day_click() {
    //Click event of expire in 30 days tile
      this.click_event(30, "Expiry in Thirty Days");
    },
    one_twenty_day_click() {
    //Click event of expire in 120 day tile
      this.click_event(120, "Expiry in One Twenty Days");
    },
    click_event(days,name){
    //Function for displaying corresponding products while clicking on a tile
      var today = new Date();
      var start_date = this.$("#start_date").val()
      var end_date = this.$("#end_date").val()
      var Domain = []
      if(start_date != ""){
        Domain.push(['expiration_date', '>=', start_date])
      }
       if(end_date != ""){
        Domain.push(['expiration_date', '<=', end_date])
      }
      today.setDate(today.getDate())
      today.setHours(0, 0, 0, 0);
      var dateString = today.toLocaleDateString();
      var timeString = today.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      var formattedDateTime = dateString + ' ' + timeString;
      if(days==-1){
        Domain.push(['expiration_date', '<', formattedDateTime])
      }
      else if(days==0){
        Domain.push(['expiration_date', '=', formattedDateTime])
      }
      else if(days==1){
      // Calculate the end date for the next-day range (one days from
        //        the today).
        today.setDate(today.getDate() + 1);
        today.setHours(0, 0, 0, 0);
        // Format the date and time as a formatted date-time string.
        var dateString = today.toLocaleDateString();
        var timeString = today.toLocaleTimeString([], { hour: '2-digit',
        minute: '2-digit', second: '2-digit' });
        var formattedDateTime = dateString + ' ' + timeString;
        Domain.push(['expiration_date', '=', formattedDateTime])
      }
      else if(days==7){
      // Calculate the end date for the seven-day range (6th days from
        //        today).
        today.setDate(today.getDate() + 1);
        today.setHours(0, 0, 0, 0);
        var dateString = today.toLocaleDateString();
        var timeString = today.toLocaleTimeString([], { hour: '2-digit', minute:
         '2-digit', second: '2-digit' });
        var tomorrow_date = dateString + ' ' + timeString;
        today.setDate(today.getDate() + 6);
        var dateString = today.toLocaleDateString();
        var seven_day_date = dateString + ' ' + timeString;
        Domain.push(['expiration_date', '<=', seven_day_date],
        ['expiration_date', '>', tomorrow_date])
      }
      else if(days==30){
        today.setDate(today.getDate() + 8);
        today.setHours(0, 0, 0, 0);
        var dateString = today.toLocaleDateString();
        var timeString = today.toLocaleTimeString([], { hour: '2-digit', minute:
         '2-digit', second: '2-digit' });
        var seventh_day = dateString + ' ' + timeString;
        // Calculate the end date for the thirty-day range (thirty days from
        //        the eighth day).
        today.setDate(today.getDate() + 22);
        dateString = today.toLocaleDateString();
        var thirty_day_date = dateString + ' ' + timeString;
        Domain.push(['expiration_date', '<=', thirty_day_date],
        ['expiration_date', '>', seventh_day])
      }
      else if(days==120){
       today.setDate(today.getDate() + 31);
        today.setHours(0, 0, 0, 0);
        var dateString = today.toLocaleDateString();
        var timeString = today.toLocaleTimeString([], { hour: '2-digit', minute:
         '2-digit', second: '2-digit' });
        var thirtieth_day = dateString + ' ' + timeString;
        // Calculate the end date for the one hundred twenty-day range
//        (eighty-nine days from the thirty-first day).
        today.setDate(today.getDate() + 89);
        dateString = today.toLocaleDateString();
        var day_one_twenty = dateString + ' ' + timeString;
        Domain.push(['expiration_date', '<=', day_one_twenty],
        ['expiration_date', '>', thirtieth_day])
      }
      this.do_action({
        name: name,
        type: 'ir.actions.act_window',
        view_mode: 'list',
        res_model: 'stock.production.lot',
        views: [[false, 'list'], [false, 'form']],
        domain: Domain,
        target: 'current',
      })
    },
  });
  core.action_registry.add("product_expiry", ProductExpiryDashboard);
  return ProductExpiryDashboard;
});
