# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
from odoo import http
from odoo.http import request


class MailPushNotification(http.Controller):
    """Controller for handling push notifications using Firebase
    Cloud Messaging"""

    @http.route('/firebase-messaging-sw.js', type='http', auth="public")
    def firebase_http(self):
        """Returns the Firebase service worker script.
        :return: The Firebase service worker script.
        :rtype: str"""
        if request.env.company and request.env.company.push_notification:
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
                request.env.company.api_key, request.env.company.auth_domain,
                request.env.company.project_id_firebase,
                request.env.company.storage_bucket,
                request.env.company.messaging_sender_id_firebase,
                request.env.company.app_id_firebase,
                request.env.company.measurement_id_firebase)
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

    @http.route('/push_notification', type='http', auth="public",
                csrf=False)
    def get_registration_tokens(self, **post):
        """Handles registration tokens for push notifications.
         Create a new registration token if it doesn't already exist
        :param post: POST request data containing registration token.
        :type post: dict
       """
        user_notification = request.env['push.notification'].sudo().search(
            [('register_id', '=', post.get('name'))], limit=1)
        if not user_notification:
            request.env['push.notification'].sudo().create({
                'register_id': post.get('name'),
                'user_id': request.env.user.id
            })

    @http.route('/firebase_config_details', type='json', auth="public")
    def send_datas(self):
        """Sends Firebase configuration details.
        :return: JSON containing Firebase configuration details.
        :rtype: str"""
        if request.env.company and request.env.company.push_notification:
            return json.dumps({
                'vapid': request.env.company.vapid,
                'config': {
                    'apiKey': request.env.company.api_key,
                    'authDomain': request.env.company.auth_domain,
                    'projectId': request.env.company.project_id_firebase,
                    'storageBucket': request.env.company.storage_bucket,
                    'messagingSenderId': request.env.company.messaging_sender_id_firebase,
                    'appId': request.env.company.app_id_firebase,
                    'measurementId': request.env.company.measurement_id_firebase
                }
            })

    @http.route('/firebase_credentials', type="json", auth="public")
    def firebase_credentials(self, **kw):
        """ Retrieve Firebase credentials for the current company."""
        return {'id': request.env.company.id,
                'push_notification': request.env.company.push_notification}