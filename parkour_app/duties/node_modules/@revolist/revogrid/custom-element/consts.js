/*!
 * Built by Revolist
 */
/**
 * A specialized version of `_.map` for arrays without support for iteratee
 * shorthands.
 *
 * @private
 * @param {Array} [array] The array to iterate over.
 * @param {Function} iteratee The function invoked per iteration.
 * @returns {Array} Returns the new mapped array.
 */
function arrayMap(array, iteratee) {
  var index = -1,
      length = array == null ? 0 : array.length,
      result = Array(length);

  while (++index < length) {
    result[index] = iteratee(array[index], index, array);
  }
  return result;
}

var _arrayMap = arrayMap;

const MIN_COL_SIZE = 30;
const DATA_COL = 'data-rgCol';
const DATA_ROW = 'data-rgRow';
const UUID = 'grid-uuid';
const DISABLED_CLASS = 'disabled';
const CELL_CLASS = 'rgCell';
const HEADER_CLASS = 'rgHeaderCell';
const HEADER_SORTABLE_CLASS = 'sortable';
const HEADER_ROW_CLASS = 'header-rgRow';
const HEADER_ACTUAL_ROW_CLASS = 'actual-rgRow';
const DRAG_ICON_CLASS = 'revo-drag-icon';
const DRAGGABLE_CLASS = 'revo-draggable';
const FOCUS_CLASS = 'focused-cell';
const SELECTION_BORDER_CLASS = 'selection-border-range';
const TMP_SELECTION_BG_CLASS = 'temp-bg-range';
const CELL_HANDLER_CLASS = 'autofill-handle';
const EDIT_INPUT_WR = 'edit-input-wrapper';
const DRAGG_TEXT = 'Draggable item';
const GRID_INTERNALS = '__rvgr';

export { CELL_HANDLER_CLASS as C, DRAGGABLE_CLASS as D, EDIT_INPUT_WR as E, FOCUS_CLASS as F, GRID_INTERNALS as G, HEADER_CLASS as H, MIN_COL_SIZE as M, SELECTION_BORDER_CLASS as S, TMP_SELECTION_BG_CLASS as T, UUID as U, _arrayMap as _, DRAG_ICON_CLASS as a, DATA_COL as b, DATA_ROW as c, HEADER_SORTABLE_CLASS as d, HEADER_ROW_CLASS as e, HEADER_ACTUAL_ROW_CLASS as f, DRAGG_TEXT as g, CELL_CLASS as h, DISABLED_CLASS as i };
