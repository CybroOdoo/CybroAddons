import {
    click,
    contains,
    defineMailModels,
    openFormView,
    start,
    startServer,
} from "@mail/../tests/mail_test_helpers";
import { after, describe, expect, test } from "@odoo/hoot";
import { onRpc } from "@web/../tests/web_test_helpers";

describe.current.tags("desktop");
defineMailModels();

test("download all attachments button is present in attachment box", async () => {
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "Test Partner" });
    pyEnv["ir.attachment"].create([
        {
            mimetype: "text/plain",
            name: "test_doc.txt",
            res_id: partnerId,
            res_model: "res.partner",
        },
    ]);
    await start();
    await openFormView("res.partner", partnerId, {
        arch: `
            <form>
                <sheet></sheet>
                <chatter open_attachments="True"/>
            </form>`,
    });
    await contains(".o-mail-AttachmentBox");
    await contains("button:contains('Download All Attachments')");
});

test("onClickDownloadAttachment shows info dialog when response is empty", async () => {
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "Test Partner Empty" });
    pyEnv["ir.attachment"].create([
        {
            mimetype: "text/plain",
            name: "test_doc.txt",
            res_id: partnerId,
            res_model: "res.partner",
        },
    ]);

    onRpc("/chatter/attachments/download/zip", (request) => {
        const url = new URL(request.url);
        expect.step(`${url.pathname}${url.search}`);
        return new Response(new Blob([], { type: "application/zip" }), {
            status: 200,
            headers: { "Content-Type": "application/zip" },
        });
    });

    await start();
    await openFormView("res.partner", partnerId, {
        arch: `
            <form>
                <sheet></sheet>
                <chatter open_attachments="True"/>
            </form>`,
    });

    await contains("button:contains('Download All Attachments')");
    await click("button:contains('Download All Attachments')");

    expect.verifySteps([
        `/chatter/attachments/download/zip?res_id=${partnerId}&res_model=res.partner`,
    ]);
    await contains(".modal-body:contains('There are no attachments to download.')");
});

test("onClickDownloadAttachment triggers download when response has content", async () => {
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "Test Partner With Data" });
    pyEnv["ir.attachment"].create([
        {
            mimetype: "text/plain",
            name: "test_doc.txt",
            res_id: partnerId,
            res_model: "res.partner",
        },
    ]);

    onRpc("/chatter/attachments/download/zip", (request) => {
        const url = new URL(request.url);
        expect.step(`${url.pathname}${url.search}`);
        return new Response(new Blob(["PK fake zip data"], { type: "application/zip" }), {
            status: 200,
            headers: { "Content-Type": "application/zip" },
        });
    });

    let resolveDownload;
    const downloadPromise = new Promise((resolve) => {
        resolveDownload = resolve;
    });

    // Intercept click on HTMLAnchorElement to:
    // 1. Capture the download filename and assert it.
    // 2. Prevent the browser from triggering a real file download to disk.
    const originalClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function () {
        if (this.hasAttribute("download")) {
            expect.step(`download: ${this.getAttribute("download")}`);
            resolveDownload();
            return;
        }
        return originalClick.apply(this, arguments);
    };
    after(() => {
        HTMLAnchorElement.prototype.click = originalClick;
    });

    await start();
    await openFormView("res.partner", partnerId, {
        arch: `
            <form>
                <sheet></sheet>
                <chatter open_attachments="True"/>
            </form>`,
    });

    await contains("button:contains('Download All Attachments')");
    await click("button:contains('Download All Attachments')");

    await downloadPromise;
    expect.verifySteps([
        `/chatter/attachments/download/zip?res_id=${partnerId}&res_model=res.partner`,
        `download: attachments_res.partner_${partnerId}.zip`,
    ]);
});

test("onClickDownloadAttachment shows error dialog on fetch failure", async () => {
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "Test Partner Error" });
    pyEnv["ir.attachment"].create([
        {
            mimetype: "text/plain",
            name: "test_doc.txt",
            res_id: partnerId,
            res_model: "res.partner",
        },
    ]);

    onRpc("/chatter/attachments/download/zip", () => {
        return new Response("Internal Server Error", {
            status: 500,
            statusText: "Internal Server Error",
        });
    });

    await start();
    await openFormView("res.partner", partnerId, {
        arch: `
            <form>
                <sheet></sheet>
                <chatter open_attachments="True"/>
            </form>`,
    });

    await contains("button:contains('Download All Attachments')");
    await click("button:contains('Download All Attachments')");

    await contains(".modal-body:contains('Failed to download attachments. Please check server logs.')");
});
