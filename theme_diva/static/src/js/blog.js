/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement, renderToFragment } from "@web/core/utils/render";
    var get_blog_post = PublicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index3_blog.xml'],
        selector : '.blog_index',
        willStart: async function(){
            const data = await jsonrpc('/get_blog_post', {})
            this.$el.html(renderToFragment('theme_diva.diva_index3_blog_snippet', {
                posts_recent: data.posts_recent,
                getBackground: this.getBackground,
                changeDateFormat: this.changeDateFormat
            }))
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
PublicWidget.registry.get_blog_post = get_blog_post;
return get_blog_post;
    var get_blog_posts = PublicWidget.Widget.extend({
        xmlDependencies: ['theme_diva/static/src/xml/index2_blog.xml'],
        selector : '.blog_2',
        willStart: async function(){
            var self = this;
           const data = await jsonrpc('/get_blog_posts', {})
            .then((data) => {
              this.$el.html(renderToElement('theme_diva.diva_index2_blog', {
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
PublicWidget.registry.get_blog_posts = get_blog_posts;
return get_blog_posts;