# -*- coding: utf-8 -*-
from odoo import http

# class DiscussNews(http.Controller):
#     @http.route('/discuss_news/discuss_news/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/discuss_news/discuss_news/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('discuss_news.listing', {
#             'root': '/discuss_news/discuss_news',
#             'objects': http.request.env['discuss_news.discuss_news'].search([]),
#         })

#     @http.route('/discuss_news/discuss_news/objects/<model("discuss_news.discuss_news"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('discuss_news.object', {
#             'object': obj
#         })