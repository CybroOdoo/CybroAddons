odoo.define('theme_autofly.blog', function(require){
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const { qweb } = require('web.core');

    publicWidget.registry.latest_blog = publicWidget.Widget.extend({
        selector: '.blog_index1',
        willStart: async function(){
            await rpc.query({
                route: '/blog_snippet_autofly'
            }).then((data) => {
                this.blog_data = data
            })
        },
        slug: function(rec) {
            return rec[1].split(' ').join('-') + '-' + rec[0]
       },
        start: function(){
            this.$el.find('.container').html(qweb.render('blog_snippet', {
                blog_data: this.blog_data,
                slug: this.slug
            }))
        },
    })
})