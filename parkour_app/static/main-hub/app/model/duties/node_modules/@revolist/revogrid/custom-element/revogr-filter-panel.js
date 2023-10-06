/*!
 * Built by Revolist
 */
import { h, proxyCustomElement, HTMLElement, createEvent, Host } from '@stencil/core/internal/client';
import { i as isFilterBtn, A as AndOrButton, T as TrashButton } from './filter.button.js';
import { d as debounce_1 } from './debounce.js';

const RevoButton = (props, children) => {
  return (h("button", Object.assign({}, props, { class: Object.assign(Object.assign({}, (typeof props.class === 'object' ? props.class : props.class ? { [props.class]: true } : '')), { ['revo-button']: true }) }), children));
};

(function closest() {
  if (!Element.prototype.matches) {
    Element.prototype.matches =
      Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
  }
  if (!Element.prototype.closest) {
    Element.prototype.closest = function (s) {
      let el = this;
      do {
        if (Element.prototype.matches.call(el, s)) {
          return el;
        }
        el = el.parentElement || el.parentNode;
      } while (el !== null && el.nodeType === 1);
      return null;
    };
  }
})();

const filterStyleCss = ".revo-drag-icon{-webkit-mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 438 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M421.875,70.40625 C426.432292,70.40625 430.175781,68.9414062 433.105469,66.0117188 C436.035156,63.0820312 437.5,59.3385417 437.5,54.78125 L437.5,54.78125 L437.5,15.71875 C437.5,11.1614583 436.035156,7.41796875 433.105469,4.48828125 C430.175781,1.55859375 426.432292,0.09375 421.875,0.09375 L421.875,0.09375 L15.625,0.09375 C11.0677083,0.09375 7.32421875,1.55859375 4.39453125,4.48828125 C1.46484375,7.41796875 0,11.1614583 0,15.71875 L0,15.71875 L0,54.78125 C0,59.3385417 1.46484375,63.0820312 4.39453125,66.0117188 C7.32421875,68.9414062 11.0677083,70.40625 15.625,70.40625 L15.625,70.40625 L421.875,70.40625 Z M421.875,226.65625 C426.432292,226.65625 430.175781,225.191406 433.105469,222.261719 C436.035156,219.332031 437.5,215.588542 437.5,211.03125 L437.5,211.03125 L437.5,171.96875 C437.5,167.411458 436.035156,163.667969 433.105469,160.738281 C430.175781,157.808594 426.432292,156.34375 421.875,156.34375 L421.875,156.34375 L15.625,156.34375 C11.0677083,156.34375 7.32421875,157.808594 4.39453125,160.738281 C1.46484375,163.667969 0,167.411458 0,171.96875 L0,171.96875 L0,211.03125 C0,215.588542 1.46484375,219.332031 4.39453125,222.261719 C7.32421875,225.191406 11.0677083,226.65625 15.625,226.65625 L15.625,226.65625 L421.875,226.65625 Z M421.875,382.90625 C426.432292,382.90625 430.175781,381.441406 433.105469,378.511719 C436.035156,375.582031 437.5,371.838542 437.5,367.28125 L437.5,367.28125 L437.5,328.21875 C437.5,323.661458 436.035156,319.917969 433.105469,316.988281 C430.175781,314.058594 426.432292,312.59375 421.875,312.59375 L421.875,312.59375 L15.625,312.59375 C11.0677083,312.59375 7.32421875,314.058594 4.39453125,316.988281 C1.46484375,319.917969 0,323.661458 0,328.21875 L0,328.21875 L0,367.28125 C0,371.838542 1.46484375,375.582031 4.39453125,378.511719 C7.32421875,381.441406 11.0677083,382.90625 15.625,382.90625 L15.625,382.90625 L421.875,382.90625 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 438 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M421.875,70.40625 C426.432292,70.40625 430.175781,68.9414062 433.105469,66.0117188 C436.035156,63.0820312 437.5,59.3385417 437.5,54.78125 L437.5,54.78125 L437.5,15.71875 C437.5,11.1614583 436.035156,7.41796875 433.105469,4.48828125 C430.175781,1.55859375 426.432292,0.09375 421.875,0.09375 L421.875,0.09375 L15.625,0.09375 C11.0677083,0.09375 7.32421875,1.55859375 4.39453125,4.48828125 C1.46484375,7.41796875 0,11.1614583 0,15.71875 L0,15.71875 L0,54.78125 C0,59.3385417 1.46484375,63.0820312 4.39453125,66.0117188 C7.32421875,68.9414062 11.0677083,70.40625 15.625,70.40625 L15.625,70.40625 L421.875,70.40625 Z M421.875,226.65625 C426.432292,226.65625 430.175781,225.191406 433.105469,222.261719 C436.035156,219.332031 437.5,215.588542 437.5,211.03125 L437.5,211.03125 L437.5,171.96875 C437.5,167.411458 436.035156,163.667969 433.105469,160.738281 C430.175781,157.808594 426.432292,156.34375 421.875,156.34375 L421.875,156.34375 L15.625,156.34375 C11.0677083,156.34375 7.32421875,157.808594 4.39453125,160.738281 C1.46484375,163.667969 0,167.411458 0,171.96875 L0,171.96875 L0,211.03125 C0,215.588542 1.46484375,219.332031 4.39453125,222.261719 C7.32421875,225.191406 11.0677083,226.65625 15.625,226.65625 L15.625,226.65625 L421.875,226.65625 Z M421.875,382.90625 C426.432292,382.90625 430.175781,381.441406 433.105469,378.511719 C436.035156,375.582031 437.5,371.838542 437.5,367.28125 L437.5,367.28125 L437.5,328.21875 C437.5,323.661458 436.035156,319.917969 433.105469,316.988281 C430.175781,314.058594 426.432292,312.59375 421.875,312.59375 L421.875,312.59375 L15.625,312.59375 C11.0677083,312.59375 7.32421875,314.058594 4.39453125,316.988281 C1.46484375,319.917969 0,323.661458 0,328.21875 L0,328.21875 L0,367.28125 C0,371.838542 1.46484375,375.582031 4.39453125,378.511719 C7.32421875,381.441406 11.0677083,382.90625 15.625,382.90625 L15.625,382.90625 L421.875,382.90625 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");width:11px;height:7px;background-size:cover;background-repeat:no-repeat}.revo-alt-icon{-webkit-mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 384 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M192.4375,383 C197.424479,383 201.663411,381.254557 205.154297,377.763672 L205.154297,377.763672 L264.25,318.667969 C270.234375,312.683594 271.605794,306.075846 268.364258,298.844727 C265.122721,291.613607 259.51237,287.998047 251.533203,287.998047 L251.533203,287.998047 L213.382812,287.998047 L213.382812,212.445312 L288.935547,212.445312 L288.935547,250.595703 C288.935547,258.57487 292.551107,264.185221 299.782227,267.426758 C307.013346,270.668294 313.621094,269.296875 319.605469,263.3125 L319.605469,263.3125 L378.701172,204.216797 C382.192057,200.725911 383.9375,196.486979 383.9375,191.5 C383.9375,186.513021 382.192057,182.274089 378.701172,178.783203 L378.701172,178.783203 L319.605469,119.6875 C313.621094,114.201823 307.013346,112.955078 299.782227,115.947266 C292.551107,118.939453 288.935547,124.42513 288.935547,132.404297 L288.935547,132.404297 L288.935547,170.554688 L213.382812,170.554688 L213.382812,95.0019531 L251.533203,95.0019531 C259.51237,95.0019531 264.998047,91.3863932 267.990234,84.1552734 C270.982422,76.9241536 269.735677,70.3164062 264.25,64.3320312 L264.25,64.3320312 L205.154297,5.23632812 C201.663411,1.74544271 197.424479,0 192.4375,0 C187.450521,0 183.211589,1.74544271 179.720703,5.23632812 L179.720703,5.23632812 L120.625,64.3320312 C114.640625,70.3164062 113.269206,76.9241536 116.510742,84.1552734 C119.752279,91.3863932 125.36263,95.0019531 133.341797,95.0019531 L133.341797,95.0019531 L171.492188,95.0019531 L171.492188,170.554688 L95.9394531,170.554688 L95.9394531,132.404297 C95.9394531,124.42513 92.3238932,118.814779 85.0927734,115.573242 C77.8616536,112.331706 71.2539062,113.703125 65.2695312,119.6875 L65.2695312,119.6875 L6.17382812,178.783203 C2.68294271,182.274089 0.9375,186.513021 0.9375,191.5 C0.9375,196.486979 2.68294271,200.725911 6.17382812,204.216797 L6.17382812,204.216797 L65.2695312,263.3125 C71.2539062,268.798177 77.8616536,270.044922 85.0927734,267.052734 C92.3238932,264.060547 95.9394531,258.57487 95.9394531,250.595703 L95.9394531,250.595703 L95.9394531,212.445312 L171.492188,212.445312 L171.492188,287.998047 L133.341797,287.998047 C125.36263,287.998047 119.876953,291.613607 116.884766,298.844727 C113.892578,306.075846 115.139323,312.683594 120.625,318.667969 L120.625,318.667969 L179.720703,377.763672 C183.211589,381.254557 187.450521,383 192.4375,383 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 384 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M192.4375,383 C197.424479,383 201.663411,381.254557 205.154297,377.763672 L205.154297,377.763672 L264.25,318.667969 C270.234375,312.683594 271.605794,306.075846 268.364258,298.844727 C265.122721,291.613607 259.51237,287.998047 251.533203,287.998047 L251.533203,287.998047 L213.382812,287.998047 L213.382812,212.445312 L288.935547,212.445312 L288.935547,250.595703 C288.935547,258.57487 292.551107,264.185221 299.782227,267.426758 C307.013346,270.668294 313.621094,269.296875 319.605469,263.3125 L319.605469,263.3125 L378.701172,204.216797 C382.192057,200.725911 383.9375,196.486979 383.9375,191.5 C383.9375,186.513021 382.192057,182.274089 378.701172,178.783203 L378.701172,178.783203 L319.605469,119.6875 C313.621094,114.201823 307.013346,112.955078 299.782227,115.947266 C292.551107,118.939453 288.935547,124.42513 288.935547,132.404297 L288.935547,132.404297 L288.935547,170.554688 L213.382812,170.554688 L213.382812,95.0019531 L251.533203,95.0019531 C259.51237,95.0019531 264.998047,91.3863932 267.990234,84.1552734 C270.982422,76.9241536 269.735677,70.3164062 264.25,64.3320312 L264.25,64.3320312 L205.154297,5.23632812 C201.663411,1.74544271 197.424479,0 192.4375,0 C187.450521,0 183.211589,1.74544271 179.720703,5.23632812 L179.720703,5.23632812 L120.625,64.3320312 C114.640625,70.3164062 113.269206,76.9241536 116.510742,84.1552734 C119.752279,91.3863932 125.36263,95.0019531 133.341797,95.0019531 L133.341797,95.0019531 L171.492188,95.0019531 L171.492188,170.554688 L95.9394531,170.554688 L95.9394531,132.404297 C95.9394531,124.42513 92.3238932,118.814779 85.0927734,115.573242 C77.8616536,112.331706 71.2539062,113.703125 65.2695312,119.6875 L65.2695312,119.6875 L6.17382812,178.783203 C2.68294271,182.274089 0.9375,186.513021 0.9375,191.5 C0.9375,196.486979 2.68294271,200.725911 6.17382812,204.216797 L6.17382812,204.216797 L65.2695312,263.3125 C71.2539062,268.798177 77.8616536,270.044922 85.0927734,267.052734 C92.3238932,264.060547 95.9394531,258.57487 95.9394531,250.595703 L95.9394531,250.595703 L95.9394531,212.445312 L171.492188,212.445312 L171.492188,287.998047 L133.341797,287.998047 C125.36263,287.998047 119.876953,291.613607 116.884766,298.844727 C113.892578,306.075846 115.139323,312.683594 120.625,318.667969 L120.625,318.667969 L179.720703,377.763672 C183.211589,381.254557 187.450521,383 192.4375,383 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");width:11px;height:11px;background-size:cover;background-repeat:no-repeat}.arrow-down{position:absolute;right:5px;top:0}.arrow-down svg{width:8px;margin-top:5px;margin-left:5px;opacity:0.4}.cell-value-wrapper{margin-right:10px;overflow:hidden;text-overflow:ellipsis}.revo-button{position:relative;overflow:hidden;color:#fff;background-color:#6200ee;height:34px;line-height:34px;padding:0 15px;outline:0;border:0;border-radius:7px;box-sizing:border-box;cursor:pointer}.revo-button.green{background-color:#2ee072;border:1px solid #20d565}.revo-button.red{background-color:#E0662E;border:1px solid #d55920}.revo-button:disabled,.revo-button[disabled]{cursor:not-allowed !important;filter:opacity(0.35) !important}.revo-button.light{border:2px solid #cedefa;line-height:32px;background:none;color:#4876ca;box-shadow:none}revogr-filter-panel{position:absolute;display:block;top:0;left:0;z-index:100;opacity:1;transform:none;background-color:#fff;transform-origin:62px 0px;box-shadow:0 5px 18px -2px rgba(0, 0, 0, 0.2);padding:10px;border-radius:4px;min-width:220px;text-align:left}revogr-filter-panel .filter-holder>div{display:flex;flex-direction:column}revogr-filter-panel label{color:gray;font-size:13px;font-weight:600;display:block;padding:8px 0}revogr-filter-panel select{width:100%}revogr-filter-panel input[type=text]{border:0;min-height:34px;margin:5px 0;background:#f3f3f3;border-radius:5px;padding:0 10px;box-sizing:border-box;width:100%}revogr-filter-panel button{margin-top:10px;margin-right:5px}revogr-filter-panel .filter-actions{text-align:right;margin-right:-5px}.rgHeaderCell:hover .rv-filter{transition:opacity 267ms cubic-bezier(0.4, 0, 0.2, 1) 0ms, transform 178ms cubic-bezier(0.4, 0, 0.2, 1) 0ms}.rgHeaderCell:hover .rv-filter,.rgHeaderCell .rv-filter.active{opacity:1}.rgHeaderCell .rv-filter{height:24px;width:24px;background:none;border:0;opacity:0;visibility:visible;cursor:pointer;border-radius:4px}.rgHeaderCell .rv-filter.active{color:#10224a}.rgHeaderCell .rv-filter .filter-img{color:gray;width:11px}.select-css{display:block;font-family:sans-serif;font-weight:600;color:#444;line-height:1.3;padding:0.6em 1.4em 0.5em 0.8em;width:100%;max-width:100%;box-sizing:border-box;margin:0;border:1px solid #f1f1f1;box-shadow:transparent;border-radius:0.5em;appearance:none;background-color:#fff;background-image:url(\"data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23007CB2%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E\"), linear-gradient(to bottom, #ffffff 0%, #ffffff 100%);background-repeat:no-repeat, repeat;background-position:right 0.7em top 50%, 0 0;background-size:0.65em auto, 100%;}.select-css::-ms-expand{display:none}.select-css:hover{border-color:#c5c5c5}.select-css:focus{border-color:#f1f1f1;box-shadow:0 0 1px 3px rgba(59, 153, 252, 0.7);box-shadow:0 0 0 3px -moz-mac-focusring;color:#222;outline:none}.select-css option{font-weight:normal}.select-css:disabled,.select-css[aria-disabled=true]{color:gray;background-image:url(\"data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22graytext%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E\"), linear-gradient(to bottom, #ffffff 0%, #ffffff 100%)}.select-css:disabled:hover,.select-css[aria-disabled=true]{border-color:#f1f1f1}.multi-filter-list{margin-top:5px;margin-bottom:5px}.multi-filter-list div{white-space:nowrap}.multi-filter-list .multi-filter-list-action{display:flex;justify-content:space-between;align-items:center}.multi-filter-list .and-or-button{margin:0 0 0 10px;min-width:58px;cursor:pointer}.multi-filter-list .trash-button{margin:0 0 -2px 6px;cursor:pointer;width:22px;height:22px;color:gray;font-size:18px}.multi-filter-list .trash-button .trash-img{width:1em}.add-filter-divider{display:block;margin:0 -10px 10px -10px;border-bottom:1px solid #d9d9d9;height:10px;box-shadow:0 4px 5px rgba(0, 0, 0, 0.05)}.select-input{display:flex;justify-content:space-between;align-items:center}";

const defaultType = 'none';
const FILTER_LIST_CLASS = 'multi-filter-list';
const FILTER_LIST_CLASS_ACTION = 'multi-filter-list-action';
const FilterPanel = /*@__PURE__*/ proxyCustomElement(class extends HTMLElement {
  constructor() {
    super();
    this.__registerHost();
    this.filterChange = createEvent(this, "filterChange", 7);
    this.filterCaptionsInternal = {
      title: 'Filter by condition',
      save: 'Save',
      reset: 'Reset',
      cancel: 'Close',
    };
    this.isFilterIdSet = false;
    this.filterId = 0;
    this.currentFilterId = -1;
    this.currentFilterType = defaultType;
    this.filterItems = {};
    this.filterTypes = {};
    this.filterNames = {};
    this.filterEntities = {};
    this.disableDynamicFiltering = false;
    this.debouncedApplyFilter = debounce_1(() => {
      this.filterChange.emit(this.filterItems);
    }, 400);
  }
  onMouseDown(e) {
    if (this.changes && !e.defaultPrevented) {
      const el = e.target;
      if (this.isOutside(el) && !isFilterBtn(el)) {
        this.changes = undefined;
      }
    }
  }
  async show(newEntity) {
    this.changes = newEntity;
    if (this.changes) {
      this.changes.type = this.changes.type || defaultType;
    }
  }
  async getChanges() {
    return this.changes;
  }
  componentWillRender() {
    if (!this.isFilterIdSet) {
      this.isFilterIdSet = true;
      const filterItems = Object.keys(this.filterItems);
      for (const prop of filterItems) {
        // we set the proper filterId so there won't be any conflict when removing filters
        this.filterId += this.filterItems[prop].length;
      }
    }
  }
  renderSelectOptions(type, isDefaultTypeRemoved = false) {
    var _a;
    const options = [];
    const prop = (_a = this.changes) === null || _a === void 0 ? void 0 : _a.prop;
    if (!isDefaultTypeRemoved) {
      options.push(h("option", { selected: this.currentFilterType === defaultType, value: defaultType }, prop && this.filterItems[prop] && this.filterItems[prop].length > 0 ? 'Add more condition...' : this.filterNames[defaultType]));
    }
    for (let gIndex in this.filterTypes) {
      options.push(...this.filterTypes[gIndex].map(k => (h("option", { value: k, selected: type === k }, this.filterNames[k]))));
      options.push(h("option", { disabled: true }));
    }
    return options;
  }
  renderExtra(prop, index) {
    const currentFilter = this.filterItems[prop];
    if (!currentFilter)
      return '';
    if (this.filterEntities[currentFilter[index].type].extra !== 'input')
      return '';
    return (h("input", { id: `filter-input-${currentFilter[index].id}`, placeholder: "Enter value...", type: "text", value: currentFilter[index].value, onInput: this.onUserInput.bind(this, index, prop), onKeyDown: e => this.onKeyDown(e) }));
  }
  getFilterItemsList() {
    var _a;
    const prop = (_a = this.changes) === null || _a === void 0 ? void 0 : _a.prop;
    if (!(prop || prop === 0))
      return '';
    const propFilters = this.filterItems[prop] || [];
    return (h("div", { key: this.filterId }, propFilters.map((d, index) => {
      let andOrButton;
      // hide toggle button if there is only one filter and the last one
      if (index !== this.filterItems[prop].length - 1) {
        andOrButton = (h("div", { onClick: () => this.toggleFilterAndOr(d.id) }, h(AndOrButton, { isAnd: d.relation === 'and' })));
      }
      return (h("div", { key: d.id, class: FILTER_LIST_CLASS }, h("div", { class: { 'select-input': true } }, h("select", { class: "select-css select-filter", onChange: e => this.onFilterTypeChange(e, prop, index) }, this.renderSelectOptions(this.filterItems[prop][index].type, true)), h("div", { class: FILTER_LIST_CLASS_ACTION }, andOrButton), h("div", { onClick: () => this.onRemoveFilter(d.id) }, h(TrashButton, null))), h("div", null, this.renderExtra(prop, index))));
    }), propFilters.length > 0 ? h("div", { class: "add-filter-divider" }) : ''));
  }
  render() {
    if (!this.changes) {
      return h(Host, { style: { display: 'none' } });
    }
    const style = {
      display: 'block',
      left: `${this.changes.x}px`,
      top: `${this.changes.y}px`,
    };
    const capts = Object.assign(this.filterCaptionsInternal, this.filterCaptions);
    return (h(Host, { style: style }, h("label", null, capts.title), h("div", { class: "filter-holder" }, this.getFilterItemsList()), h("div", { class: "add-filter" }, h("select", { id: "add-filter", class: "select-css", onChange: e => this.onAddNewFilter(e) }, this.renderSelectOptions(this.currentFilterType))), h("div", { class: "filter-actions" }, this.disableDynamicFiltering &&
      h(RevoButton, { class: { red: true, save: true }, onClick: () => this.onSave() }, capts.save), h(RevoButton, { class: { red: true, reset: true }, onClick: () => this.onReset() }, capts.reset), h(RevoButton, { class: { light: true, cancel: true }, onClick: () => this.onCancel() }, capts.cancel))));
  }
  onFilterTypeChange(e, prop, index) {
    const el = e.target;
    const type = el.value;
    this.filterItems[prop][index].type = type;
    // this re-renders the input to know if we need extra input
    this.filterId++;
    // adding setTimeout will wait for the next tick DOM update then focus on input
    setTimeout(() => {
      const input = document.getElementById('filter-input-' + this.filterItems[prop][index].id);
      if (input)
        input.focus();
    }, 0);
    if (!this.disableDynamicFiltering)
      this.debouncedApplyFilter();
  }
  onAddNewFilter(e) {
    const el = e.target;
    const type = el.value;
    this.currentFilterType = type;
    this.addNewFilterToProp();
    // reset value after adding new filter
    const select = document.getElementById('add-filter');
    if (select) {
      select.value = defaultType;
      this.currentFilterType = defaultType;
    }
    if (!this.disableDynamicFiltering)
      this.debouncedApplyFilter();
  }
  addNewFilterToProp() {
    var _a;
    const prop = (_a = this.changes) === null || _a === void 0 ? void 0 : _a.prop;
    if (!(prop || prop === 0))
      return;
    if (!this.filterItems[prop]) {
      this.filterItems[prop] = [];
    }
    if (this.currentFilterType === 'none')
      return;
    this.filterId++;
    this.currentFilterId = this.filterId;
    this.filterItems[prop].push({
      id: this.currentFilterId,
      type: this.currentFilterType,
      value: '',
      relation: 'and',
    });
    // adding setTimeout will wait for the next tick DOM update then focus on input
    setTimeout(() => {
      const input = document.getElementById('filter-input-' + this.currentFilterId);
      if (input)
        input.focus();
    }, 0);
  }
  onUserInput(index, prop, event) {
    // update the value of the filter item
    this.filterItems[prop][index].value = event.target.value;
    if (!this.disableDynamicFiltering)
      this.debouncedApplyFilter();
  }
  onKeyDown(e) {
    if (e.key.toLowerCase() === 'enter') {
      const select = document.getElementById('add-filter');
      if (select) {
        select.value = defaultType;
        this.currentFilterType = defaultType;
        this.addNewFilterToProp();
        select.focus();
      }
      return;
    }
    // keep event local, don't escalate farther to dom
    e.stopPropagation();
  }
  onSave() {
    this.filterChange.emit(this.filterItems);
  }
  onCancel() {
    this.changes = undefined;
  }
  onReset() {
    this.assertChanges();
    delete this.filterItems[this.changes.prop];
    // this updates the DOM which is used by getFilterItemsList() key
    this.filterId++;
    this.filterChange.emit(this.filterItems);
  }
  onRemoveFilter(id) {
    this.assertChanges();
    // this is for reactivity issues for getFilterItemsList()
    this.filterId++;
    const prop = this.changes.prop;
    const items = this.filterItems[prop];
    if (!items)
      return;
    const index = items.findIndex(d => d.id === id);
    if (index === -1)
      return;
    items.splice(index, 1);
    // let's remove the prop if no more filters so the filter icon will be removed
    if (items.length === 0)
      delete this.filterItems[prop];
    if (!this.disableDynamicFiltering)
      this.debouncedApplyFilter();
  }
  toggleFilterAndOr(id) {
    this.assertChanges();
    // this is for reactivity issues for getFilterItemsList()
    this.filterId++;
    const prop = this.changes.prop;
    const items = this.filterItems[prop];
    if (!items)
      return;
    const index = items.findIndex(d => d.id === id);
    if (index === -1)
      return;
    items[index].relation = items[index].relation === 'and' ? 'or' : 'and';
    if (!this.disableDynamicFiltering)
      this.debouncedApplyFilter();
  }
  assertChanges() {
    if (!this.changes) {
      throw new Error('Changes required per edit');
    }
  }
  isOutside(e) {
    const select = document.getElementById('add-filter');
    if (select)
      select.value = defaultType;
    this.currentFilterType = defaultType;
    this.changes.type = defaultType;
    this.currentFilterId = -1;
    if (e.classList.contains(`[uuid="${this.uuid}"]`)) {
      return false;
    }
    return !(e === null || e === void 0 ? void 0 : e.closest(`[uuid="${this.uuid}"]`));
  }
  static get style() { return filterStyleCss; }
}, [0, "revogr-filter-panel", {
    "uuid": [1537],
    "filterItems": [16],
    "filterTypes": [16],
    "filterNames": [16],
    "filterEntities": [16],
    "filterCaptions": [16],
    "disableDynamicFiltering": [4, "disable-dynamic-filtering"],
    "isFilterIdSet": [32],
    "filterId": [32],
    "currentFilterId": [32],
    "currentFilterType": [32],
    "changes": [32],
    "show": [64],
    "getChanges": [64]
  }, [[5, "mousedown", "onMouseDown"]]]);
function defineCustomElement$1() {
  if (typeof customElements === "undefined") {
    return;
  }
  const components = ["revogr-filter-panel"];
  components.forEach(tagName => { switch (tagName) {
    case "revogr-filter-panel":
      if (!customElements.get(tagName)) {
        customElements.define(tagName, FilterPanel);
      }
      break;
  } });
}
defineCustomElement$1();

const RevogrFilterPanel = FilterPanel;
const defineCustomElement = defineCustomElement$1;

export { RevogrFilterPanel, defineCustomElement };
