odoo.define('theme_diva.blog', function(require){
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var QWeb = core.qweb

    publicWidget.registry.get_blog_post = publicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index3_blog.xml'],
        selector : '.blog_index',
        start: function(){
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
            data = JSON.parse(data)
            return data['background-image']
        },
        changeDateFormat: function(data){
            var formattedDate = moment(new Date(data)).format('MMM DD YYYY')
            return formattedDate
        }
    });

    publicWidget.registry.get_blog_posts = publicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index2_blog.xml'],
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