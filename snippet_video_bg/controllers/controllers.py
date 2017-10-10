# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class SnippetVideoBg(http.Controller):

    @http.route('/set_video_id', type='http', auth="user", methods=['POST'], website=True)
    def index(self, **kw):
        """
        Here set the system param video id.
        :param kw:
        :return:
        """
        video_id = kw.get('id')
        request.env['ir.config_parameter'].set_param(
            'video_id', video_id) if video_id else ''
        return request.redirect('/')

    @http.route('/get_video_id', type='json', methods=['GET', 'POST'], auth="public", website=True)
    def getVideoId(self, **kw):
        """
        returns the saved video id.
        :param kw:
        :return:
        """
        video_id = request.env['ir.config_parameter'].get_param('video_id')
        return {'video_id': video_id}
