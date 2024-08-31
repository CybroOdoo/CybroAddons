/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, useState} from "@odoo/owl";
import {FileInput} from "@web/core/file_input/file_input";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";
import {useX2ManyCrud} from "@web/views/fields/relational_utils";

/**
 * The Many2ManyAttachmentPreview component is designed to manage the preview and handling
 * of many2many fields that contain file attachments. It allows users to upload, preview,
 * and remove files associated with a record.
 *
 * @class
 * @extends Component
 *
 * @prop {Object} props - The props object includes all the standard field properties,
 *                        as well as additional properties such as acceptedFileExtensions,
 *                        className, and numberOfFiles.
 * @prop {String} props.acceptedFileExtensions - (Optional) A string defining the accepted file
 *                                               extensions for uploads.
 * @prop {String} props.className - (Optional) A string defining any additional CSS classes
 *                                  to be applied.
 * @prop {Number} props.numberOfFiles - (Optional) A number representing the maximum number of
 *                                      files allowed.
 *
 * @setup
 * @method setup - Initializes services and state for the component, including ORM service,
 *                 notification service, and operations for managing many2many CRUD.
 *
 * @state {Object} state - Contains component state, including a flag for internal logic handling.
 *
 * @getter uploadText - Retrieves the label for the upload button, typically the field's label.
 *
 * @getter files - Returns a list of files associated with the record, including their IDs
 *                 and other relevant data.
 *
 * @method getUrl(id) - Constructs the URL to access a file attachment by its ID.
 * @param {Number} id - The ID of the file attachment.
 * @returns {String} - The URL for the file attachment.
 *
 * @method getExtension(file) - Extracts the file extension from a file's name.
 * @param {Object} file - The file object.
 * @returns {String} - The file extension.
 *
 * @method onFileUploaded(files) - Handles the logic after files are uploaded,
 *                                 including error handling and saving the records.
 * @param {Array} files - An array of uploaded files.
 * @returns {Promise<void>}
 *
 * @method onFileRemove(deleteId) - Handles the logic for removing a file by its ID,
 *                                  including updating the records.
 * @param {Number} deleteId - The ID of the file to be removed.
 * @returns {Promise<void>}
 *
 * @supportedTypes - Specifies that this component supports "many2many" fields.
 *
 * @fieldsToFetch - Defines the fields to be fetched from the related records, such as
 *                  'name' and 'mimetype'.
 *
 * @registry.category("fields").add("many2many_attachment_preview", Many2ManyAttachmentPreview)
 *                             - Registers the component in the Odoo registry.
 */

export class Many2ManyAttachmentPreview extends Component {
    static template = 'many2many_attachment_preview.Many2ManyImageField'
    static components = {
        FileInput,
    };
    static props = {
        ...standardFieldProps,
        acceptedFileExtensions: {type: String, optional: true},
        className: {type: String, optional: true},
        numberOfFiles: {type: Number, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.operations = useX2ManyCrud(() => this.props.value, true);
        this.state = useState({
            flag: false,
        });
    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((record) => {
            return {
                ...record.data,
                id: record.resId,
            };
        });
    }

    getUrl(id) {
        return "/web/content/ir.attachment/" + id + "/datas";
    }

    getExtension(file) {
        return file.name.replace(/^.*\./, "");
    }

    async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: this.env._t("Uploading error"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
        }
    }

    async onFileRemove(deleteId) {
        const record = this.props.value.records.find((record) => record.data.id === deleteId);
        this.operations.removeRecord(record);
    }
}

Many2ManyAttachmentPreview.supportedTypes = ["many2many"];
Many2ManyAttachmentPreview.fieldsToFetch = {
    name: {
        type: 'char'
    },
    mimetype: {
        type: 'char'
    },
}
registry.category("fields").add("many2many_attachment_preview", Many2ManyAttachmentPreview)
