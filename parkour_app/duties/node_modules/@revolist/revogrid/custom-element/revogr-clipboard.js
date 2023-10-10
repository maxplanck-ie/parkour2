/*!
 * Built by Revolist
 */
import { proxyCustomElement, HTMLElement, createEvent } from '@stencil/core/internal/client';

const Clipboard = /*@__PURE__*/ proxyCustomElement(class extends HTMLElement {
  constructor() {
    super();
    this.__registerHost();
    this.copyRegion = createEvent(this, "copyRegion", 3);
    this.pasteRegion = createEvent(this, "pasteRegion", 3);
  }
  onPaste(e) {
    const clipboardData = this.getData(e);
    const isHTML = clipboardData.types.indexOf('text/html') > -1;
    const data = isHTML ? clipboardData.getData('text/html') : clipboardData.getData('text');
    const parsedData = isHTML ? this.htmlParse(data) : this.textParse(data);
    this.pasteRegion.emit(parsedData);
    e.preventDefault();
  }
  copyStarted(e) {
    this.copyRegion.emit(this.getData(e));
    e.preventDefault();
  }
  async doCopy(e, data) {
    e.setData('text/plain', data ? this.parserCopy(data) : '');
  }
  parserCopy(data) {
    return data.map(rgRow => rgRow.join('\t')).join('\n');
  }
  textParse(data) {
    const result = [];
    const rows = data.split(/\r\n|\n|\r/);
    for (let y in rows) {
      result.push(rows[y].split('\t'));
    }
    return result;
  }
  htmlParse(data) {
    const result = [];
    const table = document.createRange().createContextualFragment(data).querySelector('table');
    for (const rgRow of Array.from(table.rows)) {
      result.push(Array.from(rgRow.cells).map(cell => cell.innerText));
    }
    return result;
  }
  getData(e) {
    var _a;
    return e.clipboardData || ((_a = window) === null || _a === void 0 ? void 0 : _a.clipboardData);
  }
}, [0, "revogr-clipboard", {
    "doCopy": [64]
  }, [[4, "paste", "onPaste"], [4, "copy", "copyStarted"]]]);
function defineCustomElement$1() {
  if (typeof customElements === "undefined") {
    return;
  }
  const components = ["revogr-clipboard"];
  components.forEach(tagName => { switch (tagName) {
    case "revogr-clipboard":
      if (!customElements.get(tagName)) {
        customElements.define(tagName, Clipboard);
      }
      break;
  } });
}
defineCustomElement$1();

const RevogrClipboard = Clipboard;
const defineCustomElement = defineCustomElement$1;

export { RevogrClipboard, defineCustomElement };
