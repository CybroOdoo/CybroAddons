/** @odoo-module **/
import {
    registerInstancePatchModel,
    registerFieldPatchModel,
    registry
} from '@mail/model/model_core';
import Dialog from "web.Dialog";
const {
    _t
} = require('web.core');
const composer_view = registry['mail.composer_view']
import {
    one2one
} from '@mail/model/model_field';
var flag = false;
var recorder, gumStream;
registerInstancePatchModel('mail.composer_view', 'mail/static/src/models/composer_view/composer_view.js', {
    recordVoice: function() {
        //Check security of site
        if (location.href.includes('https:')) {
            /**
             * Asks for access to the user's microphone if not granted yet, then
             * starts recording.
             */
            var self = this;
            if (recorder && recorder.state == "recording") {
                recorder.stop();
                gumStream.getAudioTracks()[0].stop();
                if (this.el.children.length == 4) {
                    this.el.children[2].children[1].children[0].children[1].children[1].style.color = "";
                    this.el.children[2].children[1].children[0].children[1].children[1].style.background = "";
                } else {
                    this.el.children[1].children[1].children[0].children[1].children[1].style.color = "";
                    this.el.children[1].children[1].children[0].children[1].children[1].style.background = "";
                }
            } else {
                if (this.el.children.length == 4) {
                    this.el.children[2].children[1].children[0].children[1].children[1].style.color = "#008000";
                    this.el.children[2].children[1].children[0].children[1].children[1].style.background = "#b5f1b5";
                } else {
                    this.el.children[1].children[1].children[0].children[1].children[1].style.color = "#008000";
                    this.el.children[1].children[1].children[0].children[1].children[1].style.background = "#b5f1b5";
                }
                var audioElements = $('.o_attachment_audio');
                //Pause Audio When Recording a new Audio
                audioElements.each(function(index, element) {
                    for (let i = 0; i < element.children.length; i++) {
                        const childElement = element.children[i];
                        childElement.pause()
                    }
                });
                navigator.mediaDevices.getUserMedia({
                    audio: true
                }).then((stream) => {
                    gumStream = stream;
                    recorder = new MediaRecorder(stream);
                    recorder.ondataavailable = async function(event) {
                        var reader = new FileReader();
                        reader.readAsDataURL(event.data);
                        reader.onloadend = async function() {
                            var data = reader.result;
                            var fl = [];
                            var array = data.split(','),
                                mime = array[0].match(/:(.*?);/)[1],
                                bstr = atob(array[1]),
                                n = bstr.length,
                                u8arr = new Uint8Array(n);
                            while (n--) {
                                u8arr[n] = bstr.charCodeAt(n);
                            }
                            var voice_file = new File([u8arr], 'message.mp3', {
                                type: mime
                            });
                            fl.push(voice_file);
                            await self._fileUploaderRef.comp.uploadFiles(fl)
                        };
                    };
                    recorder.start();
                });
            }
        } else {
            //If the site is not https,an alert will display.
            if (flag == false) {
                flag = true
                var dialog = new Dialog(this, {
                    size: 'medium',
                    buttons: '',
                    $content: $('<div>', {
                        text: _t("Site is not secure,use secured site(https)")
                    }),
                }).open()
            }
        }
    },
});

/**
 * Registers a field patch model for the 'mail.attachment' model.
 */
registerFieldPatchModel('mail.attachment', 'mail/static/src/models/attachment/attachment.js', {
    attachment: one2one('mail.attachmentAudio', {
        inverse: 'attachment',
        isCausal: true,
    }),
});