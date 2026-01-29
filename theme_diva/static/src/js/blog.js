odoo.define('theme_diva.blog', function(require){
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var QWeb = core.qweb
    publicWidget.registry.get_blog_post = publicWidget.Widget.extend({
      /*
        Widget for displaying recent blog posts.
        Attributes:
            xmlDependencies (Array[str]): List of XML dependencies for this widget.
            selector (str): CSS selector for the widget's target element.
        */
        xmlDependencies: ['/theme_diva/static/src/xml/index3_blog_templates.xml'],
        selector : '.blog_index',
        start: function(){
         /*
            Function called when the widget starts.
            Retrieves recent blog posts data and renders the template.
            */
            ajax.jsonRpc('/get_blog_post', 'call', {})
            .then((data) => {
              this.$el.html(QWeb.render('diva_index3_blog', {
                posts_recent: data.posts_recent,
                getBackground: this.getBackground,
                changeDateFormat: this.changeDateFormat
              }))
            });
        },
        getBackground: function(data){
         /*
            Function to extract background image data from JSON data.
            */
            data = JSON.parse(data)
            return data['background-image']
        },
        changeDateFormat: function(data){
         /*
            Function to format the date to a human-readable format.
            */
            var formattedDate = moment(new Date(data)).format('MMM DD YYYY')
            return formattedDate
        }
    });
    publicWidget.registry.get_blog_posts = publicWidget.Widget.extend({
     /*
        Widget for displaying more recent blog posts.
        Attributes:
            xmlDependencies (Array[str]): List of XML dependencies for this widget.
            selector (str): CSS selector for the widget's target element.
        */
        xmlDependencies: ['/theme_diva/static/src/xml/index2_blog_templates.xml'],
        selector : '.blog_2',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_blog_posts', 'call', {})
            .then((data) => {
              this.$el.html(QWeb.render('diva_index2_blog', {
                posts_recent: data.posts_recent,
                getBackground: this.getBackground,
                changeDateFormat: this.changeDateFormat
              }))
            });
        },
        getBackground: function(data){
            data = JSON.parse(data)
            return data['background-image']
        },
        changeDateFormat: function(data){
            var formattedDate = moment(new Date(data)).format('MMM DD YYYY')
            return formattedDate
        }
    });
});
