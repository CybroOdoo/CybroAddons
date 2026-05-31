/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, mount, useRef,onMounted } = owl
import { jsonrpc } from "@web/core/network/rpc_service";
import { loadCSS, loadJS } from "@web/core/assets";
import {
    onWillRender,
    onWillStart,
    toRaw,
    useEffect,
    useExternalListener,
    useState,
} from "@odoo/owl";
import { renderToFragment } from "@web/core/utils/render";
import { UploadFile } from "./upload_file"

let dir_loc = []
let target_path = ''
let down_loc = ''
let local_select_path = []
let remote_select_path = []
let remote_connected = false

export class FileExplorer extends Component {
	setup(){
    	this.action = useService("action");
    	this.rpc = this.env.services.rpc
    	this.orm = useService('orm');
    	this.state = useState({ files: [],fileToDownload: '' ,remote_expand_files:[], file_list:[], remote_sub_file: [], files_details: [], showFileInput: false, host_id:'',user_name:'',pass: '',port:'',isDragging: false, upload_loc:'', isModalOpen: false, downloadLocation: "",});
    	 onWillStart(async () => {
            await this.loadFiles();
        });
	}

	onClickFileRemoteLocal(event) {
	/** onClickRemoteLocal will check whether the click is from local directory or from remote directory and call
	 the function which is necessary whether to do local function(onClickFile) or remote file function**/
	let remoteValue=''
        const clickedElement = event.target.closest('.grid-item');
        if (clickedElement) {
            const clickedPath = clickedElement.id;
            const clickedFile = this.state.files.find(file => file.path === clickedPath);
            if (clickedFile) {
                 remoteValue = clickedFile.remote;
            }
        }
        if (remoteValue ==='false'){
            this.onClickFile(event)
            local_select_path.push(event.srcElement.parentElement.id)
        }
        else
        {
            let fileName = event.target.classList.contains('grid-icon') ? event.target.nextElementSibling.innerText : event.target.innerText
            let fileType = null;
            if(fileName)
            {
                if (fileName.includes('.')){

                    fileType = fileName.split('.').pop();
                }
            }
            if (fileType == null)
            {
                this.onClickFile_remote(event)
                remote_select_path.push(event.srcElement.parentElement.id)
            }
            else
            {
                return
            }
        }
    }


    async loadFiles() {
    /** The files in that directory will be rendered into the template**/
        try {
            const response = await this.orm.call('ftp.integration', 'get_directories_local', []);
            this.state.files = response.files;
        } catch (error) {
            console.error('Error loading files:', error.message, error.stack);
        }
    }

    async onClickFile(ev) {
    /**Get the Files and Directories of a File and Render them into the template**/
        try {
            let directory_path = ev.srcElement.parentElement.id;
            const response = await this.orm.call('ftp.integration', 'get_file_detailed_local', [directory_path]);
            this.state.files = response.files;
        } catch (error) {
            console.error('Error retrieving file details:', error.message, error.stack);
        }
    }

    async onClickConnect(ev) {
    /**Triggers when connect button is clicked, get host,user,password,and port from input and using them call function to
    connect to the host using these credentials**/
    try {
        let host = this.state.host_id;
        let user = this.state.user_name;
        let password = this.state.pass;
        let port_number = this.state.port;
        this.props.host = host
        const response = await this.orm.call('ftp.integration', 'connect_remote', [host, user, password, port_number]);
        this.state.files = response.files_list;
        remote_connected = true
    } catch (error) {
        console.error('Error connecting to remote server:', error.message, error.stack);
    }
}


    async onClickFile_remote(ev) {
    /**Gets directories and files of the remote side file and render them into the tmeplate**/
        let directory_path = ev.srcElement.parentElement.id;
        try {
            let host = this.state.host_id;
            let user = this.state.user_name;
            let password = this.state.pass;
            let port_number = this.state.port;
            let path = directory_path;
            target_path = path;
            this.state.upload_loc = target_path;
            const response = await this.orm.call('ftp.integration', 'get_remote_file_details', [host, user, password, port_number, path]);
            this.state.files = response.remote_files;
        } catch (error) {
            console.error('Error fetching remote file details:', error.message, error.stack);
        }
    }
    async RedirectBack() {
    /**check whether redirect to previous directory is for remote or local and call necessary function for that**/
        if (remote_connected === true)
        {
            this.redirect_back_remote()
        }
        else
        {
            this.redirect_back_local()
        }

    }
    async redirect_back_remote() {
    /**Function trigger and load previous directory files and directory and render them into template of the remote**/
        let return_path = remote_select_path.pop();
        if (remote_select_path.length > 0) {
            return_path = remote_select_path.pop();

            try {
                let host = this.state.host_id;
                let user = this.state.user_name;
                let password = this.state.pass;
                let port_number = this.state.port;
                const response = await this.orm.call('ftp.integration', 'get_remote_file_details', [host, user, password, port_number, return_path]);
                this.state.files = response.remote_files;
            } catch (error) {
                console.error('Error fetching remote file details:', error.message, error.stack);
            }
        } else {
            try {
                let host = this.state.host_id;
                let user = this.state.user_name;
                let password = this.state.pass;
                let port_number = this.state.port;
                const response = await this.orm.call('ftp.integration', 'connect_remote', [host, user, password, port_number]);
                this.state.files = response.files_list;
                remote_connected = true;
            } catch (error) {
                console.error('Error connecting to remote server:', error.message, error.stack);
            }
    }
    }

    async redirect_back_local() {
    /**Get the previous directory files and directories and render them into template of local **/
        let return_path;
        return_path = local_select_path.pop();
        if (local_select_path.length > 0) {
            return_path = local_select_path.pop();
        } else {
            return_path = '/';
        }

        try {
            const response = await this.orm.call('ftp.integration', 'get_file_detailed_local', [return_path]);
            this.state.files = response.files;
        } catch (error) {
            console.error("Failed to retrieve files:", error);
        }
    }


    UploadFile()
    /**the DIV of upload file will only been shown when this function triggers**/
    {
        this.state.showFileInput = !this.state.showFileInput;
    }

     DownloadFile(file) {
        this.state.isModalOpen = true;
        this.state.fileToDownload = file.path;
    }
    closeModal() {
        this.state.isModalOpen = false;
    }
    confirmDownload() {
        this.DownloadFileFinal(this.state.fileToDownload, this.state.downloadLocation);
        this.closeModal();
    }
    async DownloadFileFinal(file, downloadLocation) {
        console.log(`Downloading ${file} to ${downloadLocation}`);
        let host = this.state.host_id;
        let user = this.state.user_name;
        let password = this.state.pass;
        let port_number = this.state.port;
        const remote_path = file;
        const fileName = remote_path.split('/').pop();
        const local_path = `${downloadLocation}/${fileName}`;

        try {
            const result = await this.orm.call('ftp.integration', 'download_to_local', [[], host, user, password, port_number, remote_path, local_path]);
            if (result.status === 'success') {
                console.log(result.message);
            } else {
                alert(`Error: ${result.message || 'An error occurred while downloading the file.'}`);
            }
        } catch (error) {
            alert(`An unexpected error occurred: ${error.message || error}`);
        }
    }


}
FileExplorer.components = { UploadFile }
FileExplorer.template = "client_action.file_explorer"
registry.category("actions").add("file_explorer", FileExplorer)


