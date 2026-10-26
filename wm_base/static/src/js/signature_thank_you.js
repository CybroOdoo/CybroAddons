// Thank-you page: when shown inside the Sign Now iframe, offer a way back.
    if (window.self !== window.top) {
        const doneContainer = document.getElementById('iframe-done-container');
        if (doneContainer) doneContainer.classList.remove('d-none');
        const doneBtn = document.getElementById('iframe-done-btn');
        if (doneBtn) {
            doneBtn.addEventListener('click', function() {
                window.parent.postMessage({ type: 'signature_complete' }, '*');
            });
        }
    }
