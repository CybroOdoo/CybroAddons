// Expose pdf.js as window.pdfjsLib and restore the AMD loader.
window.pdfjsLib = window.pdfjsLib || window['pdfjs-dist/build/pdf'] || (typeof globalThis !== 'undefined' && globalThis['pdfjs-dist/build/pdf']);
window.define = window._temp_define;
