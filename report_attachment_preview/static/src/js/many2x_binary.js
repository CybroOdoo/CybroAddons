import { Many2XBinary } from "@web/views/fields/many2x_binary/many2x_binary";
import { patch } from "@web/core/utils/patch";

/**
 * Link attachment files to a URL ending with the file name, so the browser
 * tab opened for the preview shows the file name instead of the record id.
 * Also applies to the mail composer attachments, whose component extends
 * Many2XBinary.
 */
patch(Many2XBinary.prototype, {
    getUrl(id) {
        const file = this.props.files.find((file) => file.id === id);
        if (!file?.name) {
            return super.getUrl(id);
        }
        // Slashes would split the name into several URL segments.
        const filename = encodeURIComponent(file.name.replaceAll("/", "_"));
        return `/web/content/${id}/${filename}`;
    },
});
