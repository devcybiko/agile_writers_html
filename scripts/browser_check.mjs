// Run against a separately started local server and Chrome DevTools endpoint.
import fs from 'node:fs/promises';

const [debugUrl, base, output, ...arguments_] = process.argv.slice(2);
const offline = arguments_.includes('--block-external');
const extraPages = arguments_.filter(x => x !== '--block-external');
if (!debugUrl || !base || !output) throw new Error('Usage: node browser_check.mjs DEBUG_URL BASE_URL OUTPUT_JSON [PAGE ...]');
const targets = await (await fetch(`${debugUrl}/json`)).json();
const target = targets.find(t => t.type === 'page');
if (!target) throw new Error('No Chrome page target');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0;
const pending = new Map();
const failures = [];
const external = new Set();
const errors = [];
const requests = [];
const activeRequests = new Map();
const pages = [];
let currentPage = 'about:blank';
ws.onmessage = event => {
  const msg = JSON.parse(event.data);
  if (msg.method === 'Fetch.requestPaused') {
    const url = new URL(msg.params.request.url);
    const local = url.origin === new URL(base).origin;
    call(local ? 'Fetch.continueRequest' : 'Fetch.failRequest', local ? { requestId: msg.params.requestId } : { requestId: msg.params.requestId, errorReason: 'BlockedByClient' }).catch(error => errors.push(error.message));
  }
  if (msg.id && pending.has(msg.id)) {
    const [resolve, reject] = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
  }
  if (msg.method === 'Network.responseReceived' && msg.params.response.status >= 400) failures.push({ url: msg.params.response.url, status: msg.params.response.status });
  if (msg.method === 'Network.responseReceived') {
    const request = activeRequests.get(msg.params.requestId);
    if (request) { request.status = msg.params.response.status; request.mimeType = msg.params.response.mimeType; }
  }
  if (msg.method === 'Network.loadingFailed' && !msg.params.canceled) {
    failures.push({ error: msg.params.errorText, requestId: msg.params.requestId });
    const request = activeRequests.get(msg.params.requestId);
    if (request) request.error = msg.params.errorText;
  }
  if (msg.method === 'Network.requestWillBeSent') {
    const u = msg.params.request.url;
    if (msg.params.redirectResponse) {
      const previous = activeRequests.get(msg.params.requestId);
      if (previous) previous.status = msg.params.redirectResponse.status;
    }
    const record = { page: currentPage, url: u, type: msg.params.type, initiator: msg.params.initiator, status: null };
    requests.push(record);
    activeRequests.set(msg.params.requestId, record);
    if (/^https?:/.test(u) && new URL(u).origin !== new URL(base).origin) external.add(u);
  }
  if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.text);
};
function call(method, params = {}) {
  const current = ++id;
  return new Promise((resolve, reject) => { pending.set(current, [resolve, reject]); ws.send(JSON.stringify({ id: current, method, params })); });
}
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const evaluate = async expression => (await call('Runtime.evaluate', { expression, returnByValue: true })).result.value;
async function navigate(path) { currentPage = new URL(path, base).href; await call('Page.navigate', { url: currentPage }); await wait(3500); }
await call('Page.enable');
await call('Runtime.enable');
await call('Network.enable');
await call('Network.setCacheDisabled', { cacheDisabled: true });
await call('Fetch.disable');
if (offline) await call('Fetch.enable', { patterns: [{ urlPattern: 'http://*' }, { urlPattern: 'https://*' }] });
await call('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
await navigate('/');
const home = await evaluate(`(() => ({ title: document.title, carousel: !!document.querySelector('.slick-initialized'), slides: document.querySelectorAll('.slick-slide:not(.slick-cloned)').length, imagesBroken: [...document.images].filter(x => x.complete && !x.naturalWidth).map(x => x.currentSrc), before: document.querySelector('.slick-slide.slick-current')?.getAttribute('data-slick-index') }))()`);
await evaluate(`document.querySelector('.slick-next')?.click()`);
await wait(1600);
home.after = await evaluate(`document.querySelector('.slick-slide.slick-current')?.getAttribute('data-slick-index')`);
home.arrowFont = await evaluate(`getComputedStyle(document.querySelector('.slick-next'), '::before').fontFamily`);
home.heroBackground = await evaluate(`getComputedStyle(document.querySelector('.breadcrumb-wrapper')).backgroundImage`);
await evaluate(`document.querySelector('.slick-prev')?.click()`);
await wait(1600);
home.afterPrevious = await evaluate(`document.querySelector('.slick-slide.slick-current')?.getAttribute('data-slick-index')`);
home.articleLink = await evaluate(`document.querySelector('a[href*="2019/01/17/guest-post-the-importance-of-colors-to-your-brand"]')?.href || null`);
await navigate('/2019/01/17/guest-post-the-importance-of-colors-to-your-brand/');
const article = await evaluate(`({ title: document.title, heading: document.querySelector('h1')?.innerText, imagesBroken: [...document.images].filter(x => x.complete && !x.naturalWidth).map(x => x.currentSrc) })`);
await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
await navigate('/');
const mobile = await evaluate(`({ width: innerWidth, documentWidth: document.documentElement.scrollWidth, menu: !!document.querySelector('.slicknav_btn'), carousel: !!document.querySelector('.slick-initialized') })`);
mobile.menuBefore = await evaluate(`document.querySelector('.slicknav_btn')?.getAttribute('aria-expanded')`);
await evaluate(`document.querySelector('.slicknav_btn')?.click()`);
await wait(500);
mobile.menuAfter = await evaluate(`document.querySelector('.slicknav_btn')?.getAttribute('aria-expanded')`);
const screenshot = await call('Page.captureScreenshot', { format: 'png' });
await fs.writeFile(output.replace(/\.json$/, '-mobile.png'), Buffer.from(screenshot.data, 'base64'));
await call('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
for (const path of extraPages) {
  await navigate(path);
  pages.push({ path, ...(await evaluate(`({ title: document.title, imagesBroken: [...document.images].filter(x => x.complete && !x.naturalWidth).map(x => x.currentSrc), search: document.querySelectorAll('input[name="s"]').length, forms: document.querySelectorAll('form').length })`)) });
}
await fs.writeFile(output, JSON.stringify({ offline, home, article, mobile, pages, failures, external: [...external], errors, requests }, null, 2) + '\n');
console.log(JSON.stringify({ home, article, mobile, failures, externalCount: external.size, errors }, null, 2));
ws.close();
