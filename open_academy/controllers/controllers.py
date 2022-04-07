# -*- coding: utf-8 -*-
# from odoo import http


# class Openacademy(http.Controller):
#     @http.route('/open_academy/open_academy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/open_academy/open_academy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('openacademy.listing', {
#             'root': '/open_academy/open_academy',
#             'objects': http.request.env['open_academy.open_academy'].search([]),
#         })

#     @http.route('/open_academy/open_academy/objects/<model("open_academy.open_academy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('openacademy.object', {
#             'object': obj
#         })
