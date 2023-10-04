/*!
 * Built by Revolist
 */
import { h, proxyCustomElement, HTMLElement, createEvent } from '@stencil/core/internal/client';
import { c as _getNative, _ as _baseIteratee } from './_baseIteratee.js';
import { _ as _baseEach } from './each.js';
import { a as isArray_1 } from './keys.js';
import { F as FOCUS_CLASS, H as HEADER_CLASS, d as HEADER_SORTABLE_CLASS, b as DATA_COL, M as MIN_COL_SIZE, e as HEADER_ROW_CLASS, f as HEADER_ACTUAL_ROW_CLASS } from './consts.js';
import { a as FilterButton } from './filter.button.js';
import { C as ColumnService } from './columnService.js';
import { f as findIndex_1 } from './data.store.js';
import { g as getItemByIndex } from './dimension.helpers.js';

/**
 * Dispatch custom event to element
 */
function dispatch(target, eventName, detail) {
  const event = new CustomEvent(eventName, {
    detail,
    cancelable: true,
    bubbles: true,
  });
  target === null || target === void 0 ? void 0 : target.dispatchEvent(event);
  return event;
}

var defineProperty = (function() {
  try {
    var func = _getNative(Object, 'defineProperty');
    func({}, '', {});
    return func;
  } catch (e) {}
}());

var _defineProperty = defineProperty;

/**
 * The base implementation of `assignValue` and `assignMergeValue` without
 * value checks.
 *
 * @private
 * @param {Object} object The object to modify.
 * @param {string} key The key of the property to assign.
 * @param {*} value The value to assign.
 */
function baseAssignValue(object, key, value) {
  if (key == '__proto__' && _defineProperty) {
    _defineProperty(object, key, {
      'configurable': true,
      'enumerable': true,
      'value': value,
      'writable': true
    });
  } else {
    object[key] = value;
  }
}

var _baseAssignValue = baseAssignValue;

/**
 * A specialized version of `baseAggregator` for arrays.
 *
 * @private
 * @param {Array} [array] The array to iterate over.
 * @param {Function} setter The function to set `accumulator` values.
 * @param {Function} iteratee The iteratee to transform keys.
 * @param {Object} accumulator The initial aggregated object.
 * @returns {Function} Returns `accumulator`.
 */
function arrayAggregator(array, setter, iteratee, accumulator) {
  var index = -1,
      length = array == null ? 0 : array.length;

  while (++index < length) {
    var value = array[index];
    setter(accumulator, value, iteratee(value), array);
  }
  return accumulator;
}

var _arrayAggregator = arrayAggregator;

/**
 * Aggregates elements of `collection` on `accumulator` with keys transformed
 * by `iteratee` and values set by `setter`.
 *
 * @private
 * @param {Array|Object} collection The collection to iterate over.
 * @param {Function} setter The function to set `accumulator` values.
 * @param {Function} iteratee The iteratee to transform keys.
 * @param {Object} accumulator The initial aggregated object.
 * @returns {Function} Returns `accumulator`.
 */
function baseAggregator(collection, setter, iteratee, accumulator) {
  _baseEach(collection, function(value, key, collection) {
    setter(accumulator, value, iteratee(value), collection);
  });
  return accumulator;
}

var _baseAggregator = baseAggregator;

/**
 * Creates a function like `_.groupBy`.
 *
 * @private
 * @param {Function} setter The function to set accumulator values.
 * @param {Function} [initializer] The accumulator object initializer.
 * @returns {Function} Returns the new aggregator function.
 */
function createAggregator(setter, initializer) {
  return function(collection, iteratee) {
    var func = isArray_1(collection) ? _arrayAggregator : _baseAggregator,
        accumulator = initializer ? initializer() : {};

    return func(collection, setter, _baseIteratee(iteratee), accumulator);
  };
}

var _createAggregator = createAggregator;

/**
 * Creates an object composed of keys generated from the results of running
 * each element of `collection` thru `iteratee`. The corresponding value of
 * each key is the last element responsible for generating the key. The
 * iteratee is invoked with one argument: (value).
 *
 * @static
 * @memberOf _
 * @since 4.0.0
 * @category Collection
 * @param {Array|Object} collection The collection to iterate over.
 * @param {Function} [iteratee=_.identity] The iteratee to transform keys.
 * @returns {Object} Returns the composed aggregate object.
 * @example
 *
 * var array = [
 *   { 'dir': 'left', 'code': 97 },
 *   { 'dir': 'right', 'code': 100 }
 * ];
 *
 * _.keyBy(array, function(o) {
 *   return String.fromCharCode(o.code);
 * });
 * // => { 'a': { 'dir': 'left', 'code': 97 }, 'd': { 'dir': 'right', 'code': 100 } }
 *
 * _.keyBy(array, 'dir');
 * // => { 'left': { 'dir': 'left', 'code': 97 }, 'right': { 'dir': 'right', 'code': 100 } }
 */
var keyBy = _createAggregator(function(result, value, key) {
  _baseAssignValue(result, key, value);
});

var keyBy_1 = keyBy;

const SortingSign = ({ column }) => {
  return h("i", { class: column.order });
};

var ResizeEvents;
(function (ResizeEvents) {
  ResizeEvents["start"] = "resize:start";
  ResizeEvents["move"] = "resize:move";
  ResizeEvents["end"] = "resize:end";
})(ResizeEvents || (ResizeEvents = {}));
const RESIZE_MASK = {
  'resizable-r': { bit: 0b0001, cursor: 'ew-resize' },
  'resizable-rb': { bit: 0b0011, cursor: 'se-resize' },
  'resizable-b': { bit: 0b0010, cursor: 's-resize' },
  'resizable-lb': { bit: 0b0110, cursor: 'sw-resize' },
  'resizable-l': { bit: 0b0100, cursor: 'w-resize' },
  'resizable-lt': { bit: 0b1100, cursor: 'nw-resize' },
  'resizable-t': { bit: 0b1000, cursor: 'n-resize' },
  'resizable-rt': { bit: 0b1001, cursor: 'ne-resize' },
};
const DISABLE_MASK = {
  l: 0b0001,
  t: 0b0010,
  w: 0b0100,
  h: 0b1000,
};
const defaultProps = (props) => {
  return Object.assign(Object.assign({}, props), { fitParent: props.fitParent || false, active: props.active || [], disableAttributes: props.disableAttributes || [], minWidth: props.minWidth || 0, minHeight: props.minHeight || 0 });
};
class ResizeDirective {
  constructor(initialProps, $event) {
    this.initialProps = initialProps;
    this.$event = $event;
    this.mouseX = 0;
    this.mouseY = 0;
    this.width = 0;
    this.height = 0;
    this.changeX = 0;
    this.changeY = 0;
    this.disableCalcMap = 0b1111;
    this.props = defaultProps(initialProps);
    this.mouseMoveFunc = this.handleMove.bind(this);
    this.mouseUpFunc = this.handleUp.bind(this);
    this.minW = this.props.minWidth;
    this.minH = this.props.minHeight;
    this.maxW = this.props.maxWidth;
    this.maxH = this.props.maxHeight;
    this.parent = { width: 0, height: 0 };
    this.resizeState = 0;
  }
  set($el) {
    this.$el = $el;
    this.props.disableAttributes.forEach(attr => {
      switch (attr) {
        case 'l':
          this.disableCalcMap &= ~DISABLE_MASK.l;
          break;
        case 't':
          this.disableCalcMap &= ~DISABLE_MASK.t;
          break;
        case 'w':
          this.disableCalcMap &= ~DISABLE_MASK.w;
          break;
        case 'h':
          this.disableCalcMap &= ~DISABLE_MASK.h;
      }
    });
  }
  emitEvent(eventName, additionalOptions) {
    if (!this.$event) {
      return;
    }
    this.$event(Object.assign({ eventName, width: this.width + this.changeX, height: this.height + this.changeY, changedX: this.changeX, changedY: this.changeY }, additionalOptions));
  }
  static isTouchEvent(e) {
    var _a;
    const event = e;
    return ((_a = event.touches) === null || _a === void 0 ? void 0 : _a.length) >= 0;
  }
  handleMove(event) {
    if (!this.resizeState) {
      return;
    }
    let eventY, eventX;
    if (ResizeDirective.isTouchEvent(event)) {
      eventY = event.touches[0].clientY;
      eventX = event.touches[0].clientX;
    }
    else {
      eventY = event.clientY;
      eventX = event.clientX;
    }
    let isX = this.resizeState & RESIZE_MASK['resizable-r'].bit || this.resizeState & RESIZE_MASK['resizable-l'].bit;
    let isY = this.resizeState & RESIZE_MASK['resizable-t'].bit || this.resizeState & RESIZE_MASK['resizable-b'].bit;
    if (isY && this.disableCalcMap & DISABLE_MASK.h) {
      let diffY = eventY - this.mouseY;
      let changedY = this.changeY + diffY;
      const newHeight = this.height + changedY;
      // if overcrossed min height
      if (newHeight < this.minH) {
        changedY = -(this.height - this.minH);
      }
      // if overcrossed max heiht
      if (this.maxH && newHeight > this.maxH) {
        changedY = this.maxH - this.height;
      }
      this.changeY = changedY;
      this.mouseY = eventY;
      if (this.activeResizer) {
        this.activeResizer.style.bottom = `${-this.changeY}px`;
      }
    }
    if (isX && this.disableCalcMap & DISABLE_MASK.w) {
      let diffX = eventX - this.mouseX;
      let changedX = this.changeX + diffX;
      const newWidth = this.width + changedX;
      // if overcrossed min width
      if (newWidth < this.minW) {
        changedX = -(this.width - this.minW);
      }
      // if overcrossed max width
      if (this.maxW && newWidth > this.maxW) {
        changedX = this.maxW - this.width;
      }
      this.changeX = changedX;
      this.mouseX = eventX;
      if (this.activeResizer) {
        this.activeResizer.style.right = `${-this.changeX}px`;
      }
    }
    this.emitEvent(ResizeEvents.move);
  }
  handleDown(event) {
    if (event.defaultPrevented) {
      return;
    }
    // stop other events if resize in progress
    event.preventDefault();
    this.dropInitial();
    for (let elClass in RESIZE_MASK) {
      const target = event.target;
      if (this.$el.contains(target) && (target === null || target === void 0 ? void 0 : target.classList.contains(elClass))) {
        document.body.style.cursor = RESIZE_MASK[elClass].cursor;
        if (ResizeDirective.isTouchEvent(event)) {
          this.setInitials(event.touches[0], target);
        }
        else {
          event.preventDefault && event.preventDefault();
          this.setInitials(event, target);
        }
        this.resizeState = RESIZE_MASK[elClass].bit;
        const eventName = ResizeEvents.start;
        this.emitEvent(eventName);
        break;
      }
    }
    this.bindMove();
  }
  handleUp(e) {
    e.preventDefault();
    if (this.resizeState !== 0) {
      this.resizeState = 0;
      document.body.style.cursor = '';
      const eventName = ResizeEvents.end;
      this.emitEvent(eventName);
    }
    this.dropInitial();
    this.unbindMove();
  }
  setInitials({ clientX, clientY }, target) {
    const computedStyle = getComputedStyle(this.$el);
    this.$el.classList.add('active');
    this.activeResizer = target;
    if (this.disableCalcMap & DISABLE_MASK.w) {
      this.mouseX = clientX;
      this.width = this.$el.clientWidth;
      this.parent.width = this.$el.parentElement.clientWidth;
      // min width
      const minPaddingX = parseFloat(computedStyle.paddingLeft) + parseFloat(computedStyle.paddingRight);
      this.minW = Math.max(minPaddingX, this.initialProps.minWidth || 0);
      // max width
      if (this.initialProps.maxWidth) {
        this.maxW = Math.max(this.width, this.initialProps.maxWidth);
      }
    }
    if (this.disableCalcMap & DISABLE_MASK.h) {
      this.mouseY = clientY;
      this.height = this.$el.clientHeight;
      this.parent.height = this.$el.parentElement.clientHeight;
      // min height
      const minPaddingY = parseFloat(computedStyle.paddingTop) + parseFloat(computedStyle.paddingBottom);
      this.minH = Math.max(minPaddingY, this.initialProps.minHeight || 0);
      // max height
      if (this.initialProps.maxHeight) {
        this.maxH = Math.max(this.height, this.initialProps.maxHeight);
      }
    }
  }
  dropInitial() {
    this.changeX = this.changeY = this.minW = this.minH;
    this.width = this.height = 0;
    if (this.activeResizer) {
      this.activeResizer.removeAttribute('style');
    }
    this.$el.classList.remove('active');
    this.activeResizer = null;
  }
  bindMove() {
    document.documentElement.addEventListener('mouseup', this.mouseUpFunc, true);
    document.documentElement.addEventListener('touchend', this.mouseUpFunc, true);
    document.documentElement.addEventListener('mousemove', this.mouseMoveFunc, true);
    document.documentElement.addEventListener('touchmove', this.mouseMoveFunc, true);
    document.documentElement.addEventListener('mouseleave', this.mouseUpFunc);
  }
  unbindMove() {
    document.documentElement.removeEventListener('mouseup', this.mouseUpFunc, true);
    document.documentElement.removeEventListener('touchend', this.mouseUpFunc, true);
    document.documentElement.removeEventListener('mousemove', this.mouseMoveFunc, true);
    document.documentElement.removeEventListener('touchmove', this.mouseMoveFunc, true);
    document.documentElement.removeEventListener('mouseleave', this.mouseUpFunc);
  }
}
const ResizableElement = (props, children) => {
  const resizeEls = [];
  const directive = (props.canResize &&
    new ResizeDirective(props, e => {
      if (e.eventName === ResizeEvents.end) {
        props.onResize && props.onResize(e);
      }
    })) ||
    null;
  if (props.canResize) {
    if (props.active) {
      for (let p in props.active) {
        resizeEls.push(h("div", { onClick: e => e.preventDefault(), onDblClick: e => {
            e.preventDefault();
            props.onDoubleClick && props.onDoubleClick();
          }, onMouseDown: (e) => directive === null || directive === void 0 ? void 0 : directive.handleDown(e), onTouchStart: (e) => directive === null || directive === void 0 ? void 0 : directive.handleDown(e), class: `resizable resizable-${props.active[p]}` }));
      }
    }
  }
  else {
    if (props.active) {
      for (let p in props.active) {
        resizeEls.push(h("div", { onClick: e => e.preventDefault(), onDblClick: e => {
            e.preventDefault();
            props.onDoubleClick && props.onDoubleClick();
          }, class: `no-resize resizable resizable-${props.active[p]}` }));
      }
    }
  }
  return (h("div", Object.assign({}, props, { ref: (e) => directive === null || directive === void 0 ? void 0 : directive.set(e) }),
    children,
    resizeEls));
};

const ON_COLUMN_CLICK = 'column-click';
const HeaderCellRenderer = ({ data, props }, children) => {
  let colTemplate = (data === null || data === void 0 ? void 0 : data.name) || '';
  let cellProps = props;
  if (data === null || data === void 0 ? void 0 : data.columnTemplate) {
    colTemplate = data.columnTemplate(h, data);
  }
  if (data === null || data === void 0 ? void 0 : data.columnProperties) {
    const extra = data.columnProperties(data);
    if (extra && typeof extra === 'object') {
      cellProps = ColumnService.doMerge(props, extra);
    }
  }
  return (h(ResizableElement, Object.assign({}, cellProps, { onMouseDown: (e) => {
      dispatch(e.currentTarget, ON_COLUMN_CLICK, {
        data,
        event: e,
      });
    } }),
    h("div", { class: "header-content" }, colTemplate),
    children));
};

const HeaderRenderer = (p) => {
  var _a, _b, _c, _d, _e, _f;
  const cellClass = {
    [HEADER_CLASS]: true,
    [HEADER_SORTABLE_CLASS]: !!((_a = p.data) === null || _a === void 0 ? void 0 : _a.sortable),
  };
  if ((_b = p.data) === null || _b === void 0 ? void 0 : _b.order) {
    cellClass[p.data.order] = true;
  }
  const dataProps = {
    [DATA_COL]: p.column.itemIndex,
    canResize: p.canResize,
    minWidth: ((_c = p.data) === null || _c === void 0 ? void 0 : _c.minSize) || MIN_COL_SIZE,
    maxWidth: (_d = p.data) === null || _d === void 0 ? void 0 : _d.maxSize,
    active: ['r'],
    class: cellClass,
    style: { width: `${p.column.size}px`, transform: `translateX(${p.column.start}px)` },
    onResize: p.onResize,
    onDoubleClick(originalEvent) {
      p.onDoubleClick({ column: p.data, index: p.column.itemIndex, originalEvent });
    },
    onClick(originalEvent) {
      if (originalEvent.defaultPrevented || !p.onClick) {
        return;
      }
      p.onClick({ column: p.data, index: p.column.itemIndex, originalEvent });
    },
  };
  if (p.range) {
    if (p.column.itemIndex >= p.range.x && p.column.itemIndex <= p.range.x1) {
      if (typeof dataProps.class === 'object') {
        dataProps.class[FOCUS_CLASS] = true;
      }
    }
  }
  return (h(HeaderCellRenderer, { data: p.data, props: dataProps },
    ((_e = p.data) === null || _e === void 0 ? void 0 : _e.order) ? h(SortingSign, { column: p.data }) : '',
    p.canFilter && ((_f = p.data) === null || _f === void 0 ? void 0 : _f.filter) !== false ? h(FilterButton, { column: p.data }) : ''));
};

const GroupHeaderRenderer = (p) => {
  const groupProps = {
    canResize: p.canResize,
    minWidth: p.group.ids.length * MIN_COL_SIZE,
    maxWidth: 0,
    active: ['r'],
    class: {
      [HEADER_CLASS]: true,
    },
    style: {
      transform: `translateX(${p.start}px)`,
      width: `${p.end - p.start}px`,
    },
    onResize: p.onResize,
  };
  return h(HeaderCellRenderer, { data: p.group, props: groupProps });
};

const ColumnGroupsRenderer = ({ depth, groups, visibleProps, dimensionCol, canResize, onResize }) => {
  // render group columns
  const groupRow = [];
  for (let i = 0; i < depth; i++) {
    if (groups[i]) {
      for (let group of groups[i]) {
        // if group in visible range
        // find first visible group prop in visible columns range
        const indexFirstVisibleCol = findIndex_1(group.ids, id => typeof visibleProps[id] === 'number');
        if (indexFirstVisibleCol > -1) {
          const colVisibleIndex = visibleProps[group.ids[indexFirstVisibleCol]]; // get column index
          const groupStartIndex = colVisibleIndex - indexFirstVisibleCol; // first column index in group
          const groupEndIndex = groupStartIndex + group.ids.length - 1; // last column index in group
          // coordinates
          const groupStart = getItemByIndex(dimensionCol, groupStartIndex).start;
          const groupEnd = getItemByIndex(dimensionCol, groupEndIndex).end;
          groupRow.push(h(GroupHeaderRenderer, { start: groupStart, end: groupEnd, group: group, canResize: canResize, onResize: e => onResize(e.changedX, groupStartIndex, groupEndIndex) }));
        }
      }
    }
    groupRow.push(h("div", { class: `${HEADER_ROW_CLASS} group` }));
  }
  return groupRow;
};

const revogrHeaderStyleCss = "@charset \"UTF-8\";.revo-drag-icon{-webkit-mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 438 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M421.875,70.40625 C426.432292,70.40625 430.175781,68.9414062 433.105469,66.0117188 C436.035156,63.0820312 437.5,59.3385417 437.5,54.78125 L437.5,54.78125 L437.5,15.71875 C437.5,11.1614583 436.035156,7.41796875 433.105469,4.48828125 C430.175781,1.55859375 426.432292,0.09375 421.875,0.09375 L421.875,0.09375 L15.625,0.09375 C11.0677083,0.09375 7.32421875,1.55859375 4.39453125,4.48828125 C1.46484375,7.41796875 0,11.1614583 0,15.71875 L0,15.71875 L0,54.78125 C0,59.3385417 1.46484375,63.0820312 4.39453125,66.0117188 C7.32421875,68.9414062 11.0677083,70.40625 15.625,70.40625 L15.625,70.40625 L421.875,70.40625 Z M421.875,226.65625 C426.432292,226.65625 430.175781,225.191406 433.105469,222.261719 C436.035156,219.332031 437.5,215.588542 437.5,211.03125 L437.5,211.03125 L437.5,171.96875 C437.5,167.411458 436.035156,163.667969 433.105469,160.738281 C430.175781,157.808594 426.432292,156.34375 421.875,156.34375 L421.875,156.34375 L15.625,156.34375 C11.0677083,156.34375 7.32421875,157.808594 4.39453125,160.738281 C1.46484375,163.667969 0,167.411458 0,171.96875 L0,171.96875 L0,211.03125 C0,215.588542 1.46484375,219.332031 4.39453125,222.261719 C7.32421875,225.191406 11.0677083,226.65625 15.625,226.65625 L15.625,226.65625 L421.875,226.65625 Z M421.875,382.90625 C426.432292,382.90625 430.175781,381.441406 433.105469,378.511719 C436.035156,375.582031 437.5,371.838542 437.5,367.28125 L437.5,367.28125 L437.5,328.21875 C437.5,323.661458 436.035156,319.917969 433.105469,316.988281 C430.175781,314.058594 426.432292,312.59375 421.875,312.59375 L421.875,312.59375 L15.625,312.59375 C11.0677083,312.59375 7.32421875,314.058594 4.39453125,316.988281 C1.46484375,319.917969 0,323.661458 0,328.21875 L0,328.21875 L0,367.28125 C0,371.838542 1.46484375,375.582031 4.39453125,378.511719 C7.32421875,381.441406 11.0677083,382.90625 15.625,382.90625 L15.625,382.90625 L421.875,382.90625 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 438 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M421.875,70.40625 C426.432292,70.40625 430.175781,68.9414062 433.105469,66.0117188 C436.035156,63.0820312 437.5,59.3385417 437.5,54.78125 L437.5,54.78125 L437.5,15.71875 C437.5,11.1614583 436.035156,7.41796875 433.105469,4.48828125 C430.175781,1.55859375 426.432292,0.09375 421.875,0.09375 L421.875,0.09375 L15.625,0.09375 C11.0677083,0.09375 7.32421875,1.55859375 4.39453125,4.48828125 C1.46484375,7.41796875 0,11.1614583 0,15.71875 L0,15.71875 L0,54.78125 C0,59.3385417 1.46484375,63.0820312 4.39453125,66.0117188 C7.32421875,68.9414062 11.0677083,70.40625 15.625,70.40625 L15.625,70.40625 L421.875,70.40625 Z M421.875,226.65625 C426.432292,226.65625 430.175781,225.191406 433.105469,222.261719 C436.035156,219.332031 437.5,215.588542 437.5,211.03125 L437.5,211.03125 L437.5,171.96875 C437.5,167.411458 436.035156,163.667969 433.105469,160.738281 C430.175781,157.808594 426.432292,156.34375 421.875,156.34375 L421.875,156.34375 L15.625,156.34375 C11.0677083,156.34375 7.32421875,157.808594 4.39453125,160.738281 C1.46484375,163.667969 0,167.411458 0,171.96875 L0,171.96875 L0,211.03125 C0,215.588542 1.46484375,219.332031 4.39453125,222.261719 C7.32421875,225.191406 11.0677083,226.65625 15.625,226.65625 L15.625,226.65625 L421.875,226.65625 Z M421.875,382.90625 C426.432292,382.90625 430.175781,381.441406 433.105469,378.511719 C436.035156,375.582031 437.5,371.838542 437.5,367.28125 L437.5,367.28125 L437.5,328.21875 C437.5,323.661458 436.035156,319.917969 433.105469,316.988281 C430.175781,314.058594 426.432292,312.59375 421.875,312.59375 L421.875,312.59375 L15.625,312.59375 C11.0677083,312.59375 7.32421875,314.058594 4.39453125,316.988281 C1.46484375,319.917969 0,323.661458 0,328.21875 L0,328.21875 L0,367.28125 C0,371.838542 1.46484375,375.582031 4.39453125,378.511719 C7.32421875,381.441406 11.0677083,382.90625 15.625,382.90625 L15.625,382.90625 L421.875,382.90625 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");width:11px;height:7px;background-size:cover;background-repeat:no-repeat}.revo-alt-icon{-webkit-mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 384 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M192.4375,383 C197.424479,383 201.663411,381.254557 205.154297,377.763672 L205.154297,377.763672 L264.25,318.667969 C270.234375,312.683594 271.605794,306.075846 268.364258,298.844727 C265.122721,291.613607 259.51237,287.998047 251.533203,287.998047 L251.533203,287.998047 L213.382812,287.998047 L213.382812,212.445312 L288.935547,212.445312 L288.935547,250.595703 C288.935547,258.57487 292.551107,264.185221 299.782227,267.426758 C307.013346,270.668294 313.621094,269.296875 319.605469,263.3125 L319.605469,263.3125 L378.701172,204.216797 C382.192057,200.725911 383.9375,196.486979 383.9375,191.5 C383.9375,186.513021 382.192057,182.274089 378.701172,178.783203 L378.701172,178.783203 L319.605469,119.6875 C313.621094,114.201823 307.013346,112.955078 299.782227,115.947266 C292.551107,118.939453 288.935547,124.42513 288.935547,132.404297 L288.935547,132.404297 L288.935547,170.554688 L213.382812,170.554688 L213.382812,95.0019531 L251.533203,95.0019531 C259.51237,95.0019531 264.998047,91.3863932 267.990234,84.1552734 C270.982422,76.9241536 269.735677,70.3164062 264.25,64.3320312 L264.25,64.3320312 L205.154297,5.23632812 C201.663411,1.74544271 197.424479,0 192.4375,0 C187.450521,0 183.211589,1.74544271 179.720703,5.23632812 L179.720703,5.23632812 L120.625,64.3320312 C114.640625,70.3164062 113.269206,76.9241536 116.510742,84.1552734 C119.752279,91.3863932 125.36263,95.0019531 133.341797,95.0019531 L133.341797,95.0019531 L171.492188,95.0019531 L171.492188,170.554688 L95.9394531,170.554688 L95.9394531,132.404297 C95.9394531,124.42513 92.3238932,118.814779 85.0927734,115.573242 C77.8616536,112.331706 71.2539062,113.703125 65.2695312,119.6875 L65.2695312,119.6875 L6.17382812,178.783203 C2.68294271,182.274089 0.9375,186.513021 0.9375,191.5 C0.9375,196.486979 2.68294271,200.725911 6.17382812,204.216797 L6.17382812,204.216797 L65.2695312,263.3125 C71.2539062,268.798177 77.8616536,270.044922 85.0927734,267.052734 C92.3238932,264.060547 95.9394531,258.57487 95.9394531,250.595703 L95.9394531,250.595703 L95.9394531,212.445312 L171.492188,212.445312 L171.492188,287.998047 L133.341797,287.998047 C125.36263,287.998047 119.876953,291.613607 116.884766,298.844727 C113.892578,306.075846 115.139323,312.683594 120.625,318.667969 L120.625,318.667969 L179.720703,377.763672 C183.211589,381.254557 187.450521,383 192.4375,383 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");mask-image:url(\"data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg viewBox='0 0 384 383' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Cg%3E%3Cpath d='M192.4375,383 C197.424479,383 201.663411,381.254557 205.154297,377.763672 L205.154297,377.763672 L264.25,318.667969 C270.234375,312.683594 271.605794,306.075846 268.364258,298.844727 C265.122721,291.613607 259.51237,287.998047 251.533203,287.998047 L251.533203,287.998047 L213.382812,287.998047 L213.382812,212.445312 L288.935547,212.445312 L288.935547,250.595703 C288.935547,258.57487 292.551107,264.185221 299.782227,267.426758 C307.013346,270.668294 313.621094,269.296875 319.605469,263.3125 L319.605469,263.3125 L378.701172,204.216797 C382.192057,200.725911 383.9375,196.486979 383.9375,191.5 C383.9375,186.513021 382.192057,182.274089 378.701172,178.783203 L378.701172,178.783203 L319.605469,119.6875 C313.621094,114.201823 307.013346,112.955078 299.782227,115.947266 C292.551107,118.939453 288.935547,124.42513 288.935547,132.404297 L288.935547,132.404297 L288.935547,170.554688 L213.382812,170.554688 L213.382812,95.0019531 L251.533203,95.0019531 C259.51237,95.0019531 264.998047,91.3863932 267.990234,84.1552734 C270.982422,76.9241536 269.735677,70.3164062 264.25,64.3320312 L264.25,64.3320312 L205.154297,5.23632812 C201.663411,1.74544271 197.424479,0 192.4375,0 C187.450521,0 183.211589,1.74544271 179.720703,5.23632812 L179.720703,5.23632812 L120.625,64.3320312 C114.640625,70.3164062 113.269206,76.9241536 116.510742,84.1552734 C119.752279,91.3863932 125.36263,95.0019531 133.341797,95.0019531 L133.341797,95.0019531 L171.492188,95.0019531 L171.492188,170.554688 L95.9394531,170.554688 L95.9394531,132.404297 C95.9394531,124.42513 92.3238932,118.814779 85.0927734,115.573242 C77.8616536,112.331706 71.2539062,113.703125 65.2695312,119.6875 L65.2695312,119.6875 L6.17382812,178.783203 C2.68294271,182.274089 0.9375,186.513021 0.9375,191.5 C0.9375,196.486979 2.68294271,200.725911 6.17382812,204.216797 L6.17382812,204.216797 L65.2695312,263.3125 C71.2539062,268.798177 77.8616536,270.044922 85.0927734,267.052734 C92.3238932,264.060547 95.9394531,258.57487 95.9394531,250.595703 L95.9394531,250.595703 L95.9394531,212.445312 L171.492188,212.445312 L171.492188,287.998047 L133.341797,287.998047 C125.36263,287.998047 119.876953,291.613607 116.884766,298.844727 C113.892578,306.075846 115.139323,312.683594 120.625,318.667969 L120.625,318.667969 L179.720703,377.763672 C183.211589,381.254557 187.450521,383 192.4375,383 Z'%3E%3C/path%3E%3C/g%3E%3C/svg%3E\");width:11px;height:11px;background-size:cover;background-repeat:no-repeat}.arrow-down{position:absolute;right:5px;top:0}.arrow-down svg{width:8px;margin-top:5px;margin-left:5px;opacity:0.4}.cell-value-wrapper{margin-right:10px;overflow:hidden;text-overflow:ellipsis}.revo-button{position:relative;overflow:hidden;color:#fff;background-color:#6200ee;height:34px;line-height:34px;padding:0 15px;outline:0;border:0;border-radius:7px;box-sizing:border-box;cursor:pointer}.revo-button.green{background-color:#2ee072;border:1px solid #20d565}.revo-button.red{background-color:#E0662E;border:1px solid #d55920}.revo-button:disabled,.revo-button[disabled]{cursor:not-allowed !important;filter:opacity(0.35) !important}.revo-button.light{border:2px solid #cedefa;line-height:32px;background:none;color:#4876ca;box-shadow:none}revogr-header{position:relative;z-index:5;display:block}revogr-header .rgHeaderCell{display:flex}revogr-header .rgHeaderCell.align-center{text-align:center}revogr-header .rgHeaderCell.align-left{text-align:left}revogr-header .rgHeaderCell.align-right{text-align:right}revogr-header .rgHeaderCell.sortable{cursor:pointer}revogr-header .rgHeaderCell i.asc:after,revogr-header .rgHeaderCell i.desc:after{font-size:13px}revogr-header .rgHeaderCell i.asc:after{content:\"↑\"}revogr-header .rgHeaderCell i.desc:after{content:\"↓\"}revogr-header .rgHeaderCell,revogr-header .grouped-cell{position:absolute;box-sizing:border-box;height:100%;z-index:1}revogr-header .header-rgRow{display:block;position:relative}revogr-header .header-rgRow.group{z-index:0}revogr-header .group-rgRow{position:relative}revogr-header .rgHeaderCell.active{z-index:10}revogr-header .rgHeaderCell.active .resizable{background-color:deepskyblue}revogr-header .rgHeaderCell .header-content{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex-grow:1}revogr-header .rgHeaderCell .resizable{display:block;position:absolute;z-index:90;touch-action:none;user-select:none}revogr-header .rgHeaderCell .resizable:hover{background-color:deepskyblue}revogr-header .rgHeaderCell>.resizable-r{cursor:ew-resize;width:6px;right:0;top:0;height:100%}revogr-header .rgHeaderCell>.resizable-rb{cursor:se-resize;width:6px;height:6px;right:0;bottom:0}revogr-header .rgHeaderCell>.resizable-b{cursor:s-resize;height:6px;bottom:0;width:100%;left:0}revogr-header .rgHeaderCell>.resizable-lb{cursor:sw-resize;width:6px;height:6px;left:0;bottom:0}revogr-header .rgHeaderCell>.resizable-l{cursor:w-resize;width:6px;left:0;height:100%;top:0}revogr-header .rgHeaderCell>.resizable-lt{cursor:nw-resize;width:6px;height:6px;left:0;top:0}revogr-header .rgHeaderCell>.resizable-t{cursor:n-resize;height:6px;top:0;width:100%;left:0}revogr-header .rgHeaderCell>.resizable-rt{cursor:ne-resize;width:6px;height:6px;right:0;top:0}revogr-header .rv-filter{visibility:hidden}";

const RevogrHeaderComponent = /*@__PURE__*/ proxyCustomElement(class extends HTMLElement {
  constructor() {
    super();
    this.__registerHost();
    this.initialHeaderClick = createEvent(this, "initialHeaderClick", 7);
    this.headerresize = createEvent(this, "headerresize", 7);
    this.headerdblClick = createEvent(this, "headerdblClick", 7);
    this.parent = '';
    this.groupingDepth = 0;
  }
  onResize({ width }, index) {
    this.headerresize.emit({ [index]: width || 0 });
  }
  onResizeGroup(changedX, startIndex, endIndex) {
    const sizes = {};
    const cols = keyBy_1(this.viewportCol.get('items'), 'itemIndex');
    const change = changedX / (endIndex - startIndex + 1);
    for (let i = startIndex; i <= endIndex; i++) {
      const item = cols[i];
      if (item) {
        sizes[i] = item.size + change;
      }
    }
    this.headerresize.emit(sizes);
  }
  render() {
    var _a;
    const cols = this.viewportCol.get('items');
    const range = (_a = this.selectionStore) === null || _a === void 0 ? void 0 : _a.get('range');
    const cells = [];
    const visibleProps = {};
    // render header columns
    for (let rgCol of cols) {
      const colData = this.colData[rgCol.itemIndex];
      cells.push(h(HeaderRenderer, { range: range, column: rgCol, data: colData, canFilter: !!this.columnFilter, canResize: this.canResize, onResize: e => this.onResize(e, rgCol.itemIndex), onDoubleClick: e => this.headerdblClick.emit(e), onClick: e => this.initialHeaderClick.emit(e) }));
      visibleProps[colData === null || colData === void 0 ? void 0 : colData.prop] = rgCol.itemIndex;
    }
    return [
      h("div", { class: "group-rgRow" }, h(ColumnGroupsRenderer, { canResize: this.canResize, visibleProps: visibleProps, groups: this.groups, dimensionCol: this.dimensionCol.state, depth: this.groupingDepth, onResize: (changedX, startIndex, endIndex) => this.onResizeGroup(changedX, startIndex, endIndex) })),
      h("div", { class: `${HEADER_ROW_CLASS} ${HEADER_ACTUAL_ROW_CLASS}` }, cells),
    ];
  }
  get element() { return this; }
  static get style() { return revogrHeaderStyleCss; }
}, [0, "revogr-header", {
    "viewportCol": [16],
    "dimensionCol": [16],
    "selectionStore": [16],
    "parent": [1],
    "groups": [16],
    "groupingDepth": [2, "grouping-depth"],
    "canResize": [4, "can-resize"],
    "colData": [16],
    "columnFilter": [4, "column-filter"]
  }]);
function defineCustomElement() {
  if (typeof customElements === "undefined") {
    return;
  }
  const components = ["revogr-header"];
  components.forEach(tagName => { switch (tagName) {
    case "revogr-header":
      if (!customElements.get(tagName)) {
        customElements.define(tagName, RevogrHeaderComponent);
      }
      break;
  } });
}
defineCustomElement();

export { RevogrHeaderComponent as R, defineCustomElement as a, dispatch as d };
