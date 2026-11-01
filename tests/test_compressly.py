"""Browser regressions for the dependency-free Compressly app.

Run: uv run --python 3.12 --with pytest --with playwright pytest tests/test_compressly.py
Install Chromium first: uv run --with playwright playwright install chromium
"""
import functools
import http.server
import re
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/tools/compressly/"
    server.shutdown()
    server.server_close()


@pytest.fixture
def page(browser, url):
    context = browser.new_context(locale="en-US", permissions=["clipboard-read", "clipboard-write"])
    page = context.new_page()
    page.goto(url)
    yield page
    context.close()


def upload(page, name="sample.png", color="red"):
    data = page.evaluate("""color => {
        const c = document.createElement('canvas'); c.width = 32; c.height = 24;
        c.getContext('2d').fillStyle = color;
        c.getContext('2d').fillRect(0, 0, 16, 24);
        return Array.from(Uint8Array.from(atob(c.toDataURL().split(',')[1]), x => x.charCodeAt(0)));
    }""", color)
    page.locator('#fileInput').set_input_files({"name": name, "mimeType": "image/png", "buffer": bytes(data)})


def ready(page):
    expect(page.locator('#btnDownload')).to_be_enabled()
    expect(page.locator('#compressedImage')).to_have_attribute('src', re.compile(r'^blob:'))


def delay_encoding(page):
    page.evaluate("""() => {
        window.pendingEncodes = [];
        const real = HTMLCanvasElement.prototype.toBlob;
        HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
            let result;
            const encoded = new Promise(resolve => { result = resolve; });
            pendingEncodes.push(async () => callback(await encoded));
            real.call(this, result, ...args);
        };
    }""")


def test_clear_discards_pending_compression(page):
    upload(page)
    ready(page)
    delay_encoding(page)
    page.locator('#formatSelect').select_option('image/jpeg')
    page.wait_for_function('pendingEncodes.length === 1')
    page.locator('#btnClear').click()
    page.evaluate('pendingEncodes.shift()()')
    expect(page.locator('#btnDownload')).to_be_disabled()
    assert not page.locator('#compressedImage').get_attribute('src')


def test_settings_disable_stale_export(page):
    upload(page)
    ready(page)
    delay_encoding(page)
    page.locator('#formatSelect').select_option('image/jpeg')
    page.wait_for_function('pendingEncodes.length === 1')
    expect(page.locator('#btnDownload')).to_be_disabled()
    page.evaluate('pendingEncodes.shift()()')
    ready(page)


def test_corrupt_image_reports_error_and_recovers(page):
    page.locator('#fileInput').set_input_files({
        'name': 'broken.png', 'mimeType': 'image/png', 'buffer': b'not an image'
    })
    expect(page.locator('#toast')).to_have_class(re.compile(r'error'))
    upload(page)
    ready(page)


@pytest.mark.parametrize('fmt', ['image/png', 'image/jpeg', 'image/webp'])
def test_copy_writes_real_png_without_downloading(page, fmt):
    downloads = []
    page.on('download', lambda download: downloads.append(download))
    upload(page)
    ready(page)
    page.locator('#formatSelect').select_option(fmt)
    ready(page)
    expect(page.locator('#btnCopy')).to_be_enabled()
    page.locator('#btnCopy').click()
    expect(page.locator('#toast')).to_contain_text('copied')
    result = page.evaluate("""async () => {
        const items = await navigator.clipboard.read();
        const blob = await items[0].getType('image/png');
        const image = await createImageBitmap(blob);
        return {type: blob.type, width: image.width, height: image.height};
    }""")
    assert result == {'type': 'image/png', 'width': 32, 'height': 24}
    assert not downloads


def test_copy_permission_failure_preserves_download(page):
    upload(page)
    ready(page)
    page.evaluate("() => { navigator.clipboard.write = () => Promise.reject(new DOMException('Denied', 'NotAllowedError')); }")
    page.locator('#btnCopy').click()
    expect(page.locator('#toast')).to_have_class(re.compile('error'))
    expect(page.locator('#btnDownload')).to_be_enabled()
    expect(page.locator('#btnCopy')).to_be_enabled()


def test_canvas_failure_is_reported(page):
    upload(page)
    ready(page)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.evaluate("() => { HTMLCanvasElement.prototype.getContext = () => null; }")
    page.locator('#formatSelect').select_option('image/jpeg')
    expect(page.locator('#toast')).to_have_class(re.compile('error'))
    expect(page.locator('#compressedInfo')).not_to_contain_text('Processing')
    assert not errors


def test_latest_encoding_wins(page):
    upload(page)
    ready(page)
    delay_encoding(page)
    page.locator('#formatSelect').select_option('image/jpeg')
    page.locator('#formatSelect').select_option('image/webp')
    page.wait_for_function('pendingEncodes.length === 2')
    page.evaluate('pendingEncodes.pop()()')
    ready(page)
    newest = page.locator('#compressedImage').get_attribute('src')
    page.evaluate('pendingEncodes.shift()()')
    assert page.locator('#compressedImage').get_attribute('src') == newest


def test_unsupported_clipboard_keeps_download(page):
    page.add_init_script("Object.defineProperty(window, 'ClipboardItem', {value: undefined})")
    page.reload()
    upload(page)
    ready(page)
    expect(page.locator('#btnCopy')).to_be_disabled()
    expect(page.locator('#copyHint')).to_contain_text('unavailable')


@pytest.mark.parametrize('fmt,extension', [('image/png', 'png'), ('image/jpeg', 'jpg'), ('image/webp', 'webp')])
def test_download_retains_selected_format(page, fmt, extension):
    upload(page)
    ready(page)
    page.locator('#formatSelect').select_option(fmt)
    ready(page)
    with page.expect_download() as event:
        page.locator('#btnDownload').click()
    download = event.value
    assert download.suggested_filename == f'sample_compressed_q75.{extension}'
    data = Path(download.path()).read_bytes()
    if extension == 'png':
        assert data.startswith(b'\x89PNG')
    elif extension == 'jpg':
        assert data.startswith(b'\xff\xd8')
    else:
        assert data[8:12] == b'WEBP'


@pytest.mark.parametrize('lang,label', [('es', 'Copiar'), ('en', 'Copy'), ('de', 'kopieren'), ('zh-CN', '复制'), ('zh-TW', '複製')])
def test_localized_copy_and_mobile_layout(page, lang, label):
    page.set_viewport_size({'width': 375, 'height': 812})
    upload(page)
    ready(page)
    page.locator('#settingsBtn').click()
    page.locator('#langSelect').select_option(lang)
    page.locator('#closeSettingsBtn').click()
    expect(page.locator('#btnCopy')).to_contain_text(label)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    expect(page.locator('#settingsPanel')).to_be_hidden()
