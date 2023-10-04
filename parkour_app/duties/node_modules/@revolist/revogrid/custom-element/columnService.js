/*!
 * Built by Revolist
 */
import { h } from '@stencil/core/internal/client';
import { c as createStore, d as setStore, b as getVisibleSourceItem, g as getSourceItem, s as setSourceByVirtualIndex } from './data.store.js';
import { G as GRID_INTERNALS, h as CELL_CLASS, i as DISABLED_CLASS } from './consts.js';

const GROUP_DEPTH = `${GRID_INTERNALS}-depth`;
const PSEUDO_GROUP_ITEM = `${GRID_INTERNALS}-name`;
const PSEUDO_GROUP_ITEM_ID = `${GRID_INTERNALS}-id`;
const PSEUDO_GROUP_ITEM_VALUE = `${GRID_INTERNALS}-value`;
const PSEUDO_GROUP_COLUMN = `${GRID_INTERNALS}-column`;
const GROUP_EXPANDED = `${GRID_INTERNALS}-expanded`;
const GROUP_ORIGINAL_INDEX = `${GRID_INTERNALS}-original-index`;
const GROUP_EXPAND_BTN = `group-expand`;
const GROUP_EXPAND_EVENT = `groupExpandClick`;
const GROUPING_ROW_TYPE = 'rgRow';

/**
 * Gather data for grouping
 * @param array - flat data array
 * @param groupIds - ids of groups
 * @param expanded - potentially expanded items if present
 */
function gatherGrouping(array, groupIds, { prevExpanded, expandedAll }) {
  const groupedItems = new Map();
  array.forEach((item, originalIndex) => {
    const groupLevelValues = groupIds.map((groupId) => item[groupId] || null);
    const lastLevelValue = groupLevelValues.pop();
    let currentGroupLevel = groupedItems;
    groupLevelValues.forEach((value) => {
      if (!currentGroupLevel.has(value)) {
        currentGroupLevel.set(value, new Map());
      }
      currentGroupLevel = currentGroupLevel.get(value);
    });
    if (!currentGroupLevel.has(lastLevelValue)) {
      currentGroupLevel.set(lastLevelValue, []);
    }
    item[GROUP_ORIGINAL_INDEX] = originalIndex;
    const lastLevelItems = currentGroupLevel.get(lastLevelValue);
    lastLevelItems.push(item);
  });
  let itemIndex = -1;
  const groupingDepth = groupIds.length;
  // collapse all groups in the beginning
  const trimmed = {};
  // index mapping
  const oldNewIndexMap = {};
  // check if group header exists
  const pseudoGroupTest = {};
  const sourceWithGroups = [];
  function flattenGroupMaps(groupedValues, parentIds, isExpanded) {
    const depth = parentIds.length;
    groupedValues.forEach((innerGroupedValues, groupId) => {
      const levelIds = [...parentIds, groupId];
      const mergedIds = levelIds.join(',');
      const isGroupExpanded = isExpanded && (!!expandedAll || !!(prevExpanded === null || prevExpanded === void 0 ? void 0 : prevExpanded[mergedIds]));
      sourceWithGroups.push({
        [PSEUDO_GROUP_ITEM]: groupId,
        [GROUP_DEPTH]: depth,
        [PSEUDO_GROUP_ITEM_ID]: JSON.stringify(levelIds),
        [PSEUDO_GROUP_ITEM_VALUE]: mergedIds,
        [GROUP_EXPANDED]: isGroupExpanded,
      });
      itemIndex += 1;
      if (!isGroupExpanded && depth) {
        trimmed[itemIndex] = true;
      }
      if (Array.isArray(innerGroupedValues)) {
        innerGroupedValues.forEach((value) => {
          itemIndex += 1;
          if (!isGroupExpanded) {
            trimmed[itemIndex] = true;
          }
          oldNewIndexMap[value[GROUP_ORIGINAL_INDEX]] = itemIndex;
          const pseudoGroupTestIds = levelIds.map((_value, index) => levelIds.slice(0, index + 1).join(','));
          pseudoGroupTestIds.forEach((pseudoGroupTestId) => {
            if (!pseudoGroupTest[pseudoGroupTestId]) {
              pseudoGroupTest[pseudoGroupTestId] = [];
            }
            pseudoGroupTest[pseudoGroupTestId].push(itemIndex);
          });
        });
        sourceWithGroups.push(...innerGroupedValues);
      }
      else {
        flattenGroupMaps(innerGroupedValues, levelIds, isGroupExpanded);
      }
    });
  }
  flattenGroupMaps(groupedItems, [], true);
  return {
    sourceWithGroups,
    depth: groupingDepth,
    trimmed,
    oldNewIndexMap,
    childrenByGroup: pseudoGroupTest, // used to get child items in group
  };
}
function getGroupingName(rgRow) {
  return rgRow && rgRow[PSEUDO_GROUP_ITEM];
}
function isGrouping(rgRow) {
  return rgRow && typeof rgRow[PSEUDO_GROUP_ITEM] !== 'undefined';
}
function isGroupingColumn(column) {
  return column && typeof column[PSEUDO_GROUP_COLUMN] !== 'undefined';
}
function measureEqualDepth(groupA, groupB) {
  const ln = groupA.length;
  let i = 0;
  for (; i < ln; i++) {
    if (groupA[i] !== groupB[i]) {
      return i;
    }
  }
  return i;
}
function getParsedGroup(id) {
  const parseGroup = JSON.parse(id);
  // extra precaution and type safe guard
  if (!Array.isArray(parseGroup)) {
    return null;
  }
  return parseGroup;
}
// check if items is child of current clicked group
function isSameGroup(currentGroup, currentModel, nextModel) {
  const nextGroup = getParsedGroup(nextModel[PSEUDO_GROUP_ITEM_ID]);
  if (!nextGroup) {
    return false;
  }
  const depth = measureEqualDepth(currentGroup, nextGroup);
  return currentModel[GROUP_DEPTH] < depth;
}

function isHiddenStore(pos) {
  return pos === EMPTY_INDEX;
}
function nextCell(cell, lastCell) {
  const nextItem = {};
  let types = ['x', 'y'];
  // previous item check
  for (let t of types) {
    if (cell[t] < 0) {
      nextItem[t] = cell[t];
      return nextItem;
    }
  }
  // next item check
  for (let t of types) {
    if (cell[t] >= lastCell[t]) {
      nextItem[t] = cell[t] - lastCell[t];
      return nextItem;
    }
  }
  return null;
}
function cropCellToMax(cell, lastCell) {
  const newCell = Object.assign({}, cell);
  let types = ['x', 'y'];
  // previous item check
  for (let t of types) {
    if (cell[t] < 0) {
      newCell[t] = 0;
    }
  }
  // next item check
  for (let t of types) {
    if (cell[t] >= lastCell[t]) {
      newCell[t] = lastCell[t] - 1;
    }
  }
  return newCell;
}
function getRange(start, end) {
  return start && end
    ? {
      x: Math.min(start.x, end.x),
      y: Math.min(start.y, end.y),
      x1: Math.max(start.x, end.x),
      y1: Math.max(start.y, end.y),
    }
    : null;
}
function isRangeSingleCell(a) {
  return a.x === a.x1 && a.y === a.y1;
}

function defaultState() {
  return {
    range: null,
    tempRange: null,
    tempRangeType: null,
    focus: null,
    edit: null,
    lastCell: null,
  };
}
class SelectionStore {
  constructor() {
    this.unsubscribe = [];
    this.store = createStore(defaultState());
    this.store.on('set', (key, newVal) => {
      if (key === 'tempRange' && !newVal) {
        this.store.set('tempRangeType', null);
      }
    });
  }
  onChange(propName, cb) {
    this.unsubscribe.push(this.store.onChange(propName, cb));
  }
  clearFocus() {
    setStore(this.store, { focus: null, range: null, edit: null, tempRange: null });
  }
  setFocus(focus, end) {
    setStore(this.store, {
      focus,
      range: getRange(focus, end),
      edit: null,
      tempRange: null,
    });
  }
  setTempArea(range) {
    setStore(this.store, { tempRange: range === null || range === void 0 ? void 0 : range.area, tempRangeType: range === null || range === void 0 ? void 0 : range.type, edit: null });
  }
  clearTemp() {
    setStore(this.store, { tempRange: null });
  }
  /** Can be applied from selection change or from simple keyboard change clicks */
  setRangeArea(range) {
    setStore(this.store, { range, edit: null, tempRange: null });
  }
  setRange(start, end) {
    this.setRangeArea(getRange(start, end));
  }
  setLastCell(lastCell) {
    setStore(this.store, { lastCell });
  }
  setEdit(val) {
    const focus = this.store.get('focus');
    if (focus && typeof val === 'string') {
      setStore(this.store, {
        edit: { x: focus.x, y: focus.y, val },
      });
      return;
    }
    setStore(this.store, { edit: null });
  }
  dispose() {
    this.unsubscribe.forEach(f => f());
    this.store.dispose();
  }
}

const EMPTY_INDEX = -1;
class SelectionStoreConnector {
  constructor() {
    // dirty flag required to cleanup whole store in case visibility of panels changed
    this.dirty = false;
    this.stores = {};
    this.columnStores = {};
    this.rowStores = {};
    this.sections = [];
  }
  get focusedStore() {
    var _a;
    for (let y in this.stores) {
      for (let x in this.stores[y]) {
        const focused = (_a = this.stores[y][x]) === null || _a === void 0 ? void 0 : _a.store.get('focus');
        if (focused) {
          return {
            entity: this.stores[y][x],
            cell: focused,
            position: {
              x: parseInt(x, 10),
              y: parseInt(y, 10)
            }
          };
        }
      }
    }
    return null;
  }
  get edit() {
    var _a;
    return (_a = this.focusedStore) === null || _a === void 0 ? void 0 : _a.entity.store.get('edit');
  }
  get focused() {
    var _a;
    return (_a = this.focusedStore) === null || _a === void 0 ? void 0 : _a.entity.store.get('focus');
  }
  get selectedRange() {
    var _a;
    return (_a = this.focusedStore) === null || _a === void 0 ? void 0 : _a.entity.store.get('range');
  }
  registerSection(e) {
    if (!e) {
      this.sections.length = 0;
      // some elements removed, rebuild stores
      this.dirty = true;
      return;
    }
    if (this.sections.indexOf(e) === -1) {
      this.sections.push(e);
    }
  }
  // check if require to cleanup all stores
  beforeUpdate() {
    if (this.dirty) {
      for (let y in this.stores) {
        for (let x in this.stores[y]) {
          this.stores[y][x].dispose();
        }
      }
      this.dirty = false;
    }
  }
  registerColumn(x) {
    // if hidden just create store
    if (isHiddenStore(x)) {
      return new SelectionStore();
    }
    if (this.columnStores[x]) {
      return this.columnStores[x];
    }
    this.columnStores[x] = new SelectionStore();
    return this.columnStores[x];
  }
  registerRow(y) {
    // if hidden just create store
    if (isHiddenStore(y)) {
      return new SelectionStore();
    }
    if (this.rowStores[y]) {
      return this.rowStores[y];
    }
    this.rowStores[y] = new SelectionStore();
    return this.rowStores[y];
  }
  /**
   * Cross store proxy, based on multiple dimensions
   */
  register({ x, y }) {
    var _a, _b;
    // if hidden just create store
    if (isHiddenStore(x) || isHiddenStore(y)) {
      return new SelectionStore();
    }
    if (!this.stores[y]) {
      this.stores[y] = {};
    }
    if (this.stores[y][x]) {
      // Store already registered. Do not register twice
      return this.stores[y][x];
    }
    this.stores[y][x] = new SelectionStore();
    // proxy update
    (_a = this.stores[y][x]) === null || _a === void 0 ? void 0 : _a.onChange('range', c => {
      this.columnStores[x].setRangeArea(c);
      this.rowStores[y].setRangeArea(c);
    });
    // clean up on remove
    (_b = this.stores[y][x]) === null || _b === void 0 ? void 0 : _b.store.on('dispose', () => {
      var _a, _b;
      (_a = this.columnStores[x]) === null || _a === void 0 ? void 0 : _a.dispose();
      (_b = this.rowStores[y]) === null || _b === void 0 ? void 0 : _b.dispose();
      delete this.rowStores[y];
      delete this.columnStores[x];
      if (this.stores[y]) {
        delete this.stores[y][x];
      }
      // clear empty rows
      if (!Object.keys(this.stores[y] || {}).length) {
        delete this.stores[y];
      }
    });
    return this.stores[y][x];
  }
  setEditByCell({ x, y }, editCell) {
    const store = this.stores[y][x];
    this.focus(store, { focus: editCell, end: editCell });
    this.setEdit('');
  }
  focus(store, { focus, end }) {
    let currentStorePointer;
    // clear all stores focus leave only active one
    for (let y in this.stores) {
      for (let x in this.stores[y]) {
        const s = this.stores[y][x];
        // clear other stores, only one area can be selected
        if (s !== store) {
          s.clearFocus();
        }
        else {
          currentStorePointer = { x: parseInt(x, 10), y: parseInt(y, 10) };
        }
      }
    }
    if (!currentStorePointer) {
      return;
    }
    // check is focus in next store
    const lastCell = store.store.get('lastCell');
    // item in new store
    const nextItem = nextCell(focus, lastCell);
    let nextStore;
    if (nextItem) {
      for (let i in nextItem) {
        let type = i;
        let stores;
        switch (type) {
          case 'x':
            stores = this.getXStores(currentStorePointer.y);
            break;
          case 'y':
            stores = this.getYStores(currentStorePointer.x);
            break;
        }
        if (nextItem[type] >= 0) {
          nextStore = stores[++currentStorePointer[type]];
        }
        else {
          nextStore = stores[--currentStorePointer[type]];
          const nextLastCell = nextStore === null || nextStore === void 0 ? void 0 : nextStore.store.get('lastCell');
          if (nextLastCell) {
            nextItem[type] = nextLastCell[type] + nextItem[type];
          }
        }
      }
    }
    // if next store present - update
    if (nextStore) {
      let item = Object.assign(Object.assign({}, focus), nextItem);
      this.focus(nextStore, { focus: item, end: item });
      return;
    }
    focus = cropCellToMax(focus, lastCell);
    end = cropCellToMax(focus, lastCell);
    store.setFocus(focus, end);
  }
  clearAll() {
    var _a;
    for (let y in this.stores) {
      for (let x in this.stores[y]) {
        (_a = this.stores[y][x]) === null || _a === void 0 ? void 0 : _a.clearFocus();
      }
    }
  }
  setEdit(val) {
    if (!this.focusedStore) {
      return;
    }
    this.focusedStore.entity.setEdit(val);
  }
  getXStores(y) {
    return this.stores[y];
  }
  getYStores(x) {
    const stores = {};
    for (let i in this.stores) {
      stores[i] = this.stores[i][x];
    }
    return stores;
  }
}

class ColumnService {
  constructor(dataStore, source) {
    this.dataStore = dataStore;
    this.source = source;
    this.unsubscribe = [];
    this.hasGrouping = false;
    this.unsubscribe.push(source.onChange('source', s => this.checkGrouping(s)));
    this.checkGrouping(source.get('source'));
  }
  get columns() {
    return getVisibleSourceItem(this.source);
  }
  checkGrouping(cols) {
    for (let rgCol of cols) {
      if (isGroupingColumn(rgCol)) {
        this.hasGrouping = true;
        return;
      }
      this.hasGrouping = false;
    }
  }
  isReadOnly(r, c) {
    var _a;
    const readOnly = (_a = this.columns[c]) === null || _a === void 0 ? void 0 : _a.readonly;
    if (typeof readOnly === 'function') {
      const data = this.rowDataModel(r, c);
      return readOnly(data);
    }
    return readOnly;
  }
  static doMerge(existing, extra) {
    let props = Object.assign(Object.assign({}, extra), existing);
    // extend existing props
    if (extra.class) {
      if (typeof extra.class === 'object' && typeof props.class === 'object') {
        props.class = Object.assign(Object.assign({}, extra.class), props.class);
      }
      else if (typeof extra.class === 'string' && typeof props.class === 'object') {
        props.class[extra.class] = true;
      }
      else if (typeof props.class === 'string') {
        props.class += ' ' + extra.class;
      }
    }
    if (extra.style) {
      props.style = Object.assign(Object.assign({}, extra.style), props.style);
    }
    return props;
  }
  mergeProperties(r, c, defaultProps) {
    var _a;
    const cellClass = {
      [CELL_CLASS]: true,
      [DISABLED_CLASS]: this.isReadOnly(r, c),
    };
    let props = Object.assign(Object.assign({}, defaultProps), { class: cellClass });
    const extraPropsFunc = (_a = this.columns[c]) === null || _a === void 0 ? void 0 : _a.cellProperties;
    if (extraPropsFunc) {
      const data = this.rowDataModel(r, c);
      const extra = extraPropsFunc(data);
      if (!extra) {
        return props;
      }
      return ColumnService.doMerge(props, extra);
    }
    return props;
  }
  customRenderer(_r, c, model) {
    var _a;
    const tpl = (_a = this.columns[c]) === null || _a === void 0 ? void 0 : _a.cellTemplate;
    if (tpl) {
      return tpl(h, model);
    }
    return;
  }
  getRowClass(r, prop) {
    const model = getSourceItem(this.dataStore, r) || {};
    return model[prop] || '';
  }
  getCellData(r, c) {
    const data = this.rowDataModel(r, c);
    return ColumnService.getData(data.model[data.prop]);
  }
  getSaveData(rowIndex, c, val) {
    if (typeof val === 'undefined') {
      val = this.getCellData(rowIndex, c);
    }
    const data = this.rowDataModel(rowIndex, c);
    return {
      prop: data.prop,
      rowIndex,
      val,
      model: data.model,
      type: this.dataStore.get('type'),
    };
  }
  getCellEditor(_r, c, editors) {
    var _a;
    const editor = (_a = this.columns[c]) === null || _a === void 0 ? void 0 : _a.editor;
    if (!editor) {
      return undefined;
    }
    // reference
    if (typeof editor === 'string') {
      return editors[editor];
    }
    return editor;
  }
  rowDataModel(rowIndex, c) {
    const column = this.columns[c];
    const prop = column === null || column === void 0 ? void 0 : column.prop;
    const model = getSourceItem(this.dataStore, rowIndex) || {};
    return {
      prop,
      model,
      data: this.dataStore.get('source'),
      column,
      rowIndex,
    };
  }
  getRangeData(d) {
    const changed = {};
    // get original length sizes
    const copyColLength = d.oldProps.length;
    const copyFrom = this.copyRangeArray(d.oldRange, d.oldProps, this.dataStore);
    const copyRowLength = copyFrom.length;
    // rows
    for (let rowIndex = d.newRange.y, i = 0; rowIndex < d.newRange.y1 + 1; rowIndex++, i++) {
      // copy original data link
      const copyRow = copyFrom[i % copyRowLength];
      // columns
      for (let colIndex = d.newRange.x, j = 0; colIndex < d.newRange.x1 + 1; colIndex++, j++) {
        // check if old range area
        if (rowIndex >= d.oldRange.y && rowIndex <= d.oldRange.y1 && colIndex >= d.oldRange.x && colIndex <= d.oldRange.x1) {
          continue;
        }
        const p = this.columns[colIndex].prop;
        const currentCol = j % copyColLength;
        /** if can write */
        if (!this.isReadOnly(rowIndex, colIndex)) {
          /** to show before save */
          if (!changed[rowIndex]) {
            changed[rowIndex] = {};
          }
          changed[rowIndex][p] = copyRow[currentCol];
        }
      }
    }
    return changed;
  }
  getTransformedDataToApply(start, data) {
    const changed = {};
    const copyRowLength = data.length;
    const colLength = this.columns.length;
    const rowLength = this.dataStore.get('items').length;
    // rows
    let rowIndex = start.y;
    let maxCol = 0;
    for (let i = 0; rowIndex < rowLength && i < copyRowLength; rowIndex++, i++) {
      // copy original data link
      const copyRow = data[i % copyRowLength];
      const copyColLength = (copyRow === null || copyRow === void 0 ? void 0 : copyRow.length) || 0;
      // columns
      let colIndex = start.x;
      for (let j = 0; colIndex < colLength && j < copyColLength; colIndex++, j++) {
        const p = this.columns[colIndex].prop;
        const currentCol = j % colLength;
        /** if can write */
        if (!this.isReadOnly(rowIndex, colIndex)) {
          /** to show before save */
          if (!changed[rowIndex]) {
            changed[rowIndex] = {};
          }
          changed[rowIndex][p] = copyRow[currentCol];
        }
      }
      maxCol = Math.max(maxCol, colIndex - 1);
    }
    const range = getRange(start, {
      y: rowIndex - 1,
      x: maxCol,
    });
    return {
      changed,
      range,
    };
  }
  applyRangeData(data) {
    const items = {};
    for (let rowIndex in data) {
      const oldModel = (items[rowIndex] = getSourceItem(this.dataStore, parseInt(rowIndex, 10)));
      for (let prop in data[rowIndex]) {
        oldModel[prop] = data[rowIndex][prop];
      }
    }
    setSourceByVirtualIndex(this.dataStore, items);
  }
  getRangeStaticData(d, value) {
    const changed = {};
    // rows
    for (let rowIndex = d.y, i = 0; rowIndex < d.y1 + 1; rowIndex++, i++) {
      // columns
      for (let colIndex = d.x, j = 0; colIndex < d.x1 + 1; colIndex++, j++) {
        const p = this.columns[colIndex].prop;
        /** if can write */
        if (!this.isReadOnly(rowIndex, colIndex)) {
          /** to show before save */
          if (!changed[rowIndex]) {
            changed[rowIndex] = {};
          }
          changed[rowIndex][p] = value;
        }
      }
    }
    return changed;
  }
  copyRangeArray(range, rangeProps, store) {
    const toCopy = [];
    for (let i = range.y; i < range.y1 + 1; i++) {
      const rgRow = [];
      for (let prop of rangeProps) {
        const item = getSourceItem(store, i);
        rgRow.push(item[prop]);
      }
      toCopy.push(rgRow);
    }
    return toCopy;
  }
  static getData(val) {
    if (typeof val === 'undefined' || val === null) {
      return '';
    }
    return val.toString();
  }
  destroy() {
    this.unsubscribe.forEach(f => f());
  }
}

export { ColumnService as C, EMPTY_INDEX as E, GROUP_EXPANDED as G, PSEUDO_GROUP_ITEM_VALUE as P, SelectionStoreConnector as S, getParsedGroup as a, isSameGroup as b, GROUP_DEPTH as c, PSEUDO_GROUP_ITEM_ID as d, GROUPING_ROW_TYPE as e, PSEUDO_GROUP_COLUMN as f, getGroupingName as g, GROUP_EXPAND_EVENT as h, isGrouping as i, gatherGrouping as j, isGroupingColumn as k, GROUP_EXPAND_BTN as l, PSEUDO_GROUP_ITEM as m, getRange as n, isRangeSingleCell as o };
