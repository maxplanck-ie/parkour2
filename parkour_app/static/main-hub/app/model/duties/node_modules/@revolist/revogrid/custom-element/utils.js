/*!
 * Built by Revolist
 */
/* Generate range on size
 */
// (arr1[index1] < arr2[index2])
function simpleCompare(el1, el2) {
  return el1 < el2;
}
function mergeSortedArray(arr1, arr2, compareFn = simpleCompare) {
  const merged = [];
  let index1 = 0;
  let index2 = 0;
  let current = 0;
  while (current < arr1.length + arr2.length) {
    let isArr1Depleted = index1 >= arr1.length;
    let isArr2Depleted = index2 >= arr2.length;
    if (!isArr1Depleted && (isArr2Depleted || compareFn(arr1[index1], arr2[index2]))) {
      merged[current] = arr1[index1];
      index1++;
    }
    else {
      merged[current] = arr2[index2];
      index2++;
    }
    current++;
  }
  return merged;
}
/* Calculate system scrollbar width */
function getScrollbarWidth(doc) {
  // Creating invisible container
  const outer = doc.createElement('div');
  const styles = outer.style;
  styles.visibility = 'hidden';
  styles.overflow = 'scroll'; // forcing scrollbar to appear
  styles.msOverflowStyle = 'scrollbar'; // needed for WinJS apps
  doc.body.appendChild(outer);
  // Creating inner element and placing it in the container
  const inner = doc.createElement('div');
  outer.appendChild(inner);
  // Calculating difference between container's full width and the child width
  const scrollbarWidth = outer.offsetWidth - inner.offsetWidth;
  // Removing temporary elements from the DOM
  outer.parentNode.removeChild(outer);
  return scrollbarWidth;
}
/* Scale a value between 2 ranges
 *
 * Sample:
 * // 55 from a 0-100 range to a 0-1000 range (Ranges don't have to be positive)
 * const n = scaleValue(55, [0,100], [0,1000]);
 *
 * Ranges of two values
 * @from
 * @to
 *
 * ~~ return value does the equivalent of Math.floor but faster.
 */
function scaleValue(value, from, to) {
  return ((to[1] - to[0]) * (value - from[0])) / (from[1] - from[0]) + to[0];
}
async function timeout(delay = 0) {
  await new Promise((r) => {
    setTimeout(() => r(), delay);
  });
}

export { getScrollbarWidth as g, mergeSortedArray as m, scaleValue as s, timeout as t };
