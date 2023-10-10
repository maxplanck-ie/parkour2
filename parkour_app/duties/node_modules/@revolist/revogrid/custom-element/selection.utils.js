/*!
 * Built by Revolist
 */
import { a as getItemByPosition, g as getItemByIndex } from './dimension.helpers.js';

/** Calculate cell based on x, y position */
function getCurrentCell({ x, y }, { el, rows, cols }) {
  const { top, left, height, width } = el.getBoundingClientRect();
  let cellY = y - top;
  // limit to element height
  if (cellY >= height) {
    cellY = height - 1;
  }
  let cellX = x - left;
  // limit to element width
  if (cellX >= width) {
    cellX = width - 1;
  }
  const rgRow = getItemByPosition(rows, cellY);
  const rgCol = getItemByPosition(cols, cellX);
  // before first
  if (rgCol.itemIndex < 0) {
    rgCol.itemIndex = 0;
  }
  // before first
  if (rgRow.itemIndex < 0) {
    rgRow.itemIndex = 0;
  }
  return { x: rgCol.itemIndex, y: rgRow.itemIndex };
}
function getCoordinate(range, focus, changes, isMulti = false) {
  const updateCoordinate = (c) => {
    const start = { x: range.x, y: range.y };
    const end = isMulti ? { x: range.x1, y: range.y1 } : start;
    const point = end[c] > focus[c] ? end : start;
    point[c] += changes[c];
    return { start, end };
  };
  if (changes.x) {
    return updateCoordinate('x');
  }
  if (changes.y) {
    return updateCoordinate('y');
  }
  return null;
}
/** check if out of range */
function isAfterLast({ x, y }, { lastCell }) {
  return x >= lastCell.x || y >= lastCell.y;
}
/** check if out of range */
function isBeforeFirst({ x, y }) {
  return x < 0 || y < 0;
}
function styleByCellProps(styles) {
  return {
    left: `${styles.left}px`,
    top: `${styles.top}px`,
    width: `${styles.width}px`,
    height: `${styles.height}px`,
  };
}
function getCell({ x, y, x1, y1 }, dimensionRow, dimensionCol) {
  const top = getItemByIndex(dimensionRow, y).start;
  const left = getItemByIndex(dimensionCol, x).start;
  const bottom = getItemByIndex(dimensionRow, y1).end;
  const right = getItemByIndex(dimensionCol, x1).end;
  return {
    left,
    right,
    top,
    bottom,
    width: right - left,
    height: bottom - top,
  };
}
function getElStyle(range, dimensionRow, dimensionCol) {
  const styles = getCell(range, dimensionRow, dimensionCol);
  return styleByCellProps(styles);
}

export { getCoordinate as a, isBeforeFirst as b, getCell as c, getCurrentCell as d, getElStyle as g, isAfterLast as i };
