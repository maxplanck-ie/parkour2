/*!
 * Built by Revolist
 */
import { proxyCustomElement, HTMLElement, createEvent } from '@stencil/core/internal/client';
import { d as debounce_1 } from './debounce.js';
import { h as setItems } from './data.store.js';
import { g as DRAGG_TEXT } from './consts.js';
import { a as getItemByPosition } from './dimension.helpers.js';

class RowOrderService {
  constructor(config) {
    this.config = config;
    this.currentCell = null;
    this.previousRow = null;
  }
  /** Drag finished, calculate and apply changes */
  endOrder(e, data) {
    if (this.currentCell === null) {
      return;
    }
    const newRow = this.getCell(e, data);
    // if position changed
    if (newRow.y !== this.currentCell.y) {
      // rgRow dragged out table
      if (newRow.y < 0) {
        newRow.y = 0;
      }
      // rgRow dragged to the top
      else if (newRow.y < this.currentCell.y) {
        newRow.y++;
      }
      this.config.positionChanged(this.currentCell.y, newRow.y);
    }
    this.clear();
  }
  /** Drag started, reserve initial cell for farther use */
  startOrder(e, data) {
    this.currentCell = this.getCell(e, data);
    return this.currentCell;
  }
  move(y, data) {
    const rgRow = this.getRow(y, data);
    // if rgRow same as previous or below range (-1 = 0) do nothing
    if (this.previousRow === rgRow.itemIndex || rgRow.itemIndex < -1) {
      return null;
    }
    this.previousRow = rgRow.itemIndex;
    return rgRow;
  }
  /** Drag stopped, probably cursor outside of document area */
  clear() {
    this.currentCell = null;
    this.previousRow = null;
  }
  /** Calculate cell based on x, y position */
  getRow(y, { el, rows }) {
    const { top } = el.getBoundingClientRect();
    const topRelative = y - top;
    const rgRow = getItemByPosition(rows, topRelative);
    const absolutePosition = {
      itemIndex: rgRow.itemIndex,
      start: rgRow.start + top,
      end: rgRow.end + top,
    };
    return absolutePosition;
  }
  /** Calculate cell based on x, y position */
  getCell({ x, y }, { el, rows, cols }) {
    const { top, left } = el.getBoundingClientRect();
    const topRelative = y - top;
    const leftRelative = x - left;
    const rgRow = getItemByPosition(rows, topRelative);
    const rgCol = getItemByPosition(cols, leftRelative);
    return { x: rgCol.itemIndex, y: rgRow.itemIndex };
  }
}

const OrderEditor = /*@__PURE__*/ proxyCustomElement(class extends HTMLElement {
  constructor() {
    super();
    this.__registerHost();
    this.internalRowDragStart = createEvent(this, "internalRowDragStart", 7);
    this.internalRowDragEnd = createEvent(this, "internalRowDragEnd", 7);
    this.internalRowDrag = createEvent(this, "internalRowDrag", 7);
    this.internalRowMouseMove = createEvent(this, "internalRowMouseMove", 7);
    this.initialRowDropped = createEvent(this, "initialRowDropped", 7);
    this.rowMoveFunc = debounce_1((y) => {
      const rgRow = this.rowOrderService.move(y, this.getData());
      if (rgRow !== null) {
        this.internalRowDrag.emit(rgRow);
      }
    }, 5);
  }
  // --------------------------------------------------------------------------
  //
  //  Listeners
  //
  // --------------------------------------------------------------------------
  onMouseOut() {
    this.clearOrder();
  }
  /** Action finished inside of the document */
  onMouseUp(e) {
    this.endOrder(e);
  }
  // --------------------------------------------------------------------------
  //
  //  Methods
  //
  // --------------------------------------------------------------------------
  async dragStart(e) {
    e.preventDefault();
    // extra check if previous ended
    if (this.moveFunc) {
      this.clearOrder();
    }
    const data = this.getData();
    const cell = this.rowOrderService.startOrder(e, data);
    const pos = this.rowOrderService.getRow(e.y, data);
    const dragStartEvent = this.internalRowDragStart.emit({ cell, text: DRAGG_TEXT, pos, event: e });
    if (dragStartEvent.defaultPrevented) {
      return;
    }
    this.moveFunc = (e) => this.move(e);
    document.addEventListener('mousemove', this.moveFunc);
  }
  async endOrder(e) {
    this.rowOrderService.endOrder(e, this.getData());
    this.clearOrder();
  }
  async clearOrder() {
    this.rowOrderService.clear();
    document.removeEventListener('mousemove', this.moveFunc);
    this.moveFunc = null;
    this.internalRowDragEnd.emit();
  }
  // --------------------------------------------------------------------------
  //
  //  Component methods
  //
  // --------------------------------------------------------------------------
  move({ x, y }) {
    this.internalRowMouseMove.emit({ x, y });
    this.rowMoveFunc(y);
  }
  connectedCallback() {
    this.rowOrderService = new RowOrderService({ positionChanged: (f, t) => this.onPositionChanged(f, t) });
  }
  onPositionChanged(from, to) {
    const dropEvent = this.initialRowDropped.emit({ from, to });
    if (dropEvent.defaultPrevented) {
      return;
    }
    const items = [...this.dataStore.get('items')];
    const toMove = items.splice(from, 1);
    items.splice(to, 0, ...toMove);
    setItems(this.dataStore, items);
  }
  getData() {
    return {
      el: this.parent,
      rows: this.dimensionRow.state,
      cols: this.dimensionCol.state,
    };
  }
}, [0, "revogr-order-editor", {
    "parent": [16],
    "dimensionRow": [16],
    "dimensionCol": [16],
    "dataStore": [16],
    "dragStart": [64],
    "endOrder": [64],
    "clearOrder": [64]
  }, [[5, "mouseleave", "onMouseOut"], [5, "mouseup", "onMouseUp"]]]);
function defineCustomElement() {
  if (typeof customElements === "undefined") {
    return;
  }
  const components = ["revogr-order-editor"];
  components.forEach(tagName => { switch (tagName) {
    case "revogr-order-editor":
      if (!customElements.get(tagName)) {
        customElements.define(tagName, OrderEditor);
      }
      break;
  } });
}
defineCustomElement();

export { OrderEditor as O, defineCustomElement as d };
