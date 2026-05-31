/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { registry} from '@web/core/registry';
import { loadCSS, loadJS } from "@web/core/assets";
const { Component, mount, useRef,onMounted } = owl
import {
    onWillRender,
    onWillStart,
    toRaw,
    useEffect,
    useExternalListener,
    useState,
} from "@odoo/owl";


export class UploadFile extends Component{
    setup()
    {
        this.action = useService("action");
        this.file = useRef("file")
        onWillStart(async () => {
            await loadJS('https://unpkg.com/filepond@^4/dist/filepond.js')
            await loadCSS('https://unpkg.com/filepond@^4/dist/filepond.css')
        });
        onMounted(() => {
        /**Filepond Library is used to upload file into the remote**/
            console.log("filePond", FilePond);
            console.log(this.props.hostId);
            let host = this.props.hostId;
            let user = this.props.username;
            let pass = this.props.password;
            let port_number = this.props.port;
            let upload_location = this.props.upload

            FilePond.create(this.file.el, {
                allowMultiple: true,
                server: {
                    process: {
                        url: './filepond/process',
                        method: 'POST',
                        withCredentials: false,
                        headers: {},
                        timeout: 7000,
                        onload: (response) => {
                            console.log('File uploaded:', response);
                        },
                        onerror: (response) => {
                            console.log('Error:', response);
                        },
                        ondata: (formData) => {
                            // Append additional data to the formData
                            formData.append('host', host);
                            formData.append('username', user);
                            formData.append('password', pass);
                            formData.append('port', port_number);
                            formData.append('upload_location', upload_location);
                            return formData;
                        }
                    },
                    fetch: null,
                    revert: null,
                },
            });
        });

    }
}
UploadFile.template = "upload_file_pop"
registry.category("actions").add("upload_file", UploadFile)