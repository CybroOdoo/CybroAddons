# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
from odoo import http
from odoo.http import request


class MailPushNotification(http.Controller):
    """Controller for handling push notifications using Firebase
    Cloud Messaging"""

    def _get_active_company(self):
        if request.env.company and request.env.company.push_notification:
            return request.env.company
        return request.env['res.company'].sudo().search([('push_notification', '=', True)], limit=1)

    @http.route('/firebase-messaging-sw.js', type='http', auth="public")
    def firebase_http(self):
        """Returns the Firebase service worker script."""
        company = self._get_active_company()
        if company and company.push_notification:
            firebase_js = """
            this.addEventListener('fetch', function(e) {
              e.respondWith(
                caches.match(e.request).then(function(response) {
                  return response || fetch(e.request);
                })
              );
            });
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-app.js');
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-messaging.js');
            var firebaseConfig = {
                apiKey: '%s',
                authDomain: '%s',
                projectId: '%s',
                storageBucket: '%s',
                messagingSenderId: '%s',
                appId: '%s',
                measurementId: '%s',
            };
            firebase.initializeApp(firebaseConfig);
            const messaging = firebase.messaging();
            messaging.setBackgroundMessageHandler(function(payload) {
            const notificationTitle = "Background Message Title";
            const notificationOptions = {
                body: payload.notification.body,
                icon:'/mail_push_notification/static/description/icon.png',
            };
            return self.registration.showNotification(
                notificationTitle,
                notificationOptions,
            );
            });
            """ % (
                company.api_key or '', company.auth_domain or '',
                company.project_id_firebase or '',
                company.storage_bucket or '',
                company.messaging_sender_id_firebase or '',
                company.app_id_firebase or '',
                company.measurement_id_firebase or '')
        else:
            firebase_js = """
                this.addEventListener('fetch', function(e) {
                  e.respondWith(
                    caches.match(e.request).then(function(response) {
                      return response || fetch(e.request);
                    })
                  );
                });
            """
        return http.request.make_response(firebase_js, [
            ('Content-Type', 'text/javascript')])

    @http.route('/push_notification', type='jsonrpc', auth="user")
    def get_registration_tokens(self, name=None, **kwargs):
        """Handles registration tokens for push notifications."""
        if name:
            user_notification = request.env['push.notification'].search([
                ('user_id', '=', request.env.user.id),
                ('register_id', '=', name),
            ], limit=1)
            if not user_notification:
                request.env['push.notification'].create({
                    'register_id': name,
                    'user_id': request.env.user.id,
                })
            return True

    @http.route('/firebase_config_details', type='jsonrpc', auth="public")
    def send_datas(self):
        """Sends Firebase configuration details."""
        company = self._get_active_company()
        if company and company.push_notification:
            return json.dumps({
                'vapid': company.vapid or '',
                'config': {
                    'apiKey': company.api_key or '',
                    'authDomain': company.auth_domain or '',
                    'projectId': company.project_id_firebase or '',
                    'storageBucket': company.storage_bucket or '',
                    'messagingSenderId': company.messaging_sender_id_firebase or '',
                    'appId': company.app_id_firebase or '',
                    'measurementId': company.measurement_id_firebase or ''
                }
            })

    @http.route('/firebase_credentials', type="jsonrpc", auth="public")
    def firebase_credentials(self, **kw):
        """ Retrieve Firebase credentials for the current company."""
        company = self._get_active_company()
        return {'id': company.id if company else False,
                'push_notification': company.push_notification if company else False}
