export * from "./notificationUtils";
export * from "./apiUtils";
export * from "./dateUtils";
export * from "./excelUtils";

export function getProp(object, keys, defaultVal) {
  keys = Array.isArray(keys) ? keys : keys.split(".");
  object = object[keys[0]];
  if (object && keys.length > 1) {
    return getProp(object, keys.slice(1), defaultVal);
  }
  return object === undefined ? defaultVal : object;
}

export function ellipsisContainer(text, boldText) {
  return `<div title='${text}' style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 12px 8px 12px 12px; font-weight: ${
    boldText === true ? "bold" : "normal"
  }">
                ${text}
              </div>`;
}

export function cellContextMenu(
  allowCopy,
  allowEdit,
  allowApplyToAll,
  getTabulatorInstance,
  options = {}
) {
  const shouldBlockDisabledCells = options.blockActionsOnDisabledCells === true;
  const menuCell = options.cell || null;
  const onApplyToAll =
    typeof options.onApplyToAll === "function" ? options.onApplyToAll : null;
  const onCut = typeof options.onCut === "function" ? options.onCut : null;
  const onClear =
    typeof options.onClear === "function" ? options.onClear : null;
  const allowCut =
    options.allowCut === undefined ? allowEdit : options.allowCut === true;
  const allowClear =
    options.allowClear === undefined ? allowEdit : options.allowClear === true;
  const tabulatorInstance = getTabulatorInstance();
  const tableRef =
    typeof tabulatorInstance?.getTable === "function"
      ? tabulatorInstance.getTable()
      : tabulatorInstance;
  const isCellEditable = (cell) => {
    if (!cell) return false;
    const cellEl = cell.getElement?.();
    if (
      shouldBlockDisabledCells &&
      cellEl?.classList?.contains("disable-editing")
    ) {
      return false;
    }
    const columnDef = cell.getColumn?.().getDefinition?.() || {};
    if (columnDef.editor === false) return false;
    if (typeof columnDef.editable === "function") {
      const rowData = cell.getRow?.().getData?.() || {};
      return columnDef.editable({
        getRow: () => ({ getData: () => rowData })
      });
    }
    if (typeof columnDef.editable === "boolean") {
      return columnDef.editable;
    }
    return true;
  };
  const ranges = tableRef?.getRanges?.() || [];
  const hasSelection = ranges.length > 0;
  let hasEditableSelection = false;
  let singleCellSelected = false;
  if (hasSelection) {
    const cells = ranges[0]?.getCells?.() || [];
    singleCellSelected = cells.length === 1 && (cells[0]?.length || 0) === 1;
    cells.forEach((row) => {
      row.forEach((cell) => {
        if (isCellEditable(cell)) {
          hasEditableSelection = true;
        }
      });
    });
  }
  const menuCellEditable = isCellEditable(menuCell);
  if (!hasSelection && menuCell) {
    singleCellSelected = true;
  }
  const operations = [];
  const ensureRangeSelection = (cell) => {
    if (!tableRef || !cell) return;
    const ranges = tableRef.getRanges?.() || [];
    if (!ranges.length && typeof tableRef.addRange === "function") {
      tableRef.addRange(cell, cell);
    }
  };
  if (shouldBlockDisabledCells && menuCell) {
    if (!menuCellEditable && !hasEditableSelection) {
      if (allowCopy) {
        return [
          {
            label: "Copy",
            action: (e, cell) => {
              const targetCell = cell || menuCell;
              ensureRangeSelection(targetCell);
              tableRef?.copyToClipboard?.();
            }
          }
        ];
      }
      return [];
    }
  }
  const restoreFocus = () => {
    if (typeof tabulatorInstance?.restoreLastFocusedCell === "function") {
      tabulatorInstance.restoreLastFocusedCell();
      return;
    }
    tableRef?.element?.focus?.();
  };

  if (allowApplyToAll && menuCellEditable && singleCellSelected) {
    operations.push({
      label: "Apply to All",
      action: (e, cell) => {
        if (onApplyToAll) {
          onApplyToAll({
            cell,
            field: cell?.getField?.(),
            value: cell?.getValue?.(),
            tableRef,
            tabulatorInstance,
            blockActionsOnDisabledCells: shouldBlockDisabledCells
          });
          restoreFocus();
          return;
        }
        const fakeLoadingStart =
          tabulatorInstance?.tableOptions?.fakeLoadingStart;
        const fakeLoadingStop =
          tabulatorInstance?.tableOptions?.fakeLoadingStop;
        if (typeof fakeLoadingStart === "function") {
          fakeLoadingStart();
        }
        applyValueToAllRows(cell, getTabulatorInstance, {
          blockActionsOnDisabledCells: shouldBlockDisabledCells
        });
        if (typeof fakeLoadingStop === "function") {
          setTimeout(() => fakeLoadingStop(), 0);
        }
        restoreFocus();
      }
    });
  }

  if (allowCut && (menuCellEditable || hasEditableSelection)) {
    operations.push({
      label: "Cut",
      action: (e, cell) => {
        const targetCell = cell || menuCell;
        ensureRangeSelection(targetCell);
        if (onCut) {
          onCut({ cell: targetCell, tableRef, tabulatorInstance });
          restoreFocus();
          return;
        }
        tableRef?.copyToClipboard?.();
        const keyEvent = new KeyboardEvent("keydown", {
          key: "Delete",
          bubbles: true
        });
        tableRef?.element?.dispatchEvent?.(keyEvent);
        restoreFocus();
      }
    });
  }

  if (allowCopy) {
    operations.push({
      label: "Copy",
      action: (e, cell) => {
        ensureRangeSelection(cell);
        tableRef?.copyToClipboard?.();
        restoreFocus();
      }
    });
  }

  if (allowEdit && (menuCellEditable || hasEditableSelection)) {
    operations.push({
      label: "Paste",
      action: (e, cell) => {
        ensureRangeSelection(cell);
        if (typeof tabulatorInstance?.triggerClipboardPaste === "function") {
          tabulatorInstance.triggerClipboardPaste();
        } else {
          tableRef?.pasteFromClipboard?.();
        }
        restoreFocus();
      }
    });
  }

  if (allowClear && (menuCellEditable || hasEditableSelection)) {
    operations.push({
      label: "Clear",
      action: (e, cell) => {
        const targetCell = cell || menuCell;
        ensureRangeSelection(targetCell);
        if (onClear) {
          onClear({ cell: targetCell, tableRef, tabulatorInstance });
          restoreFocus();
          return;
        }
        const keyEvent = new KeyboardEvent("keydown", {
          key: "Delete",
          bubbles: true
        });
        tableRef?.element?.dispatchEvent?.(keyEvent);
        restoreFocus();
      }
    });
  }

  return operations.length ? operations : [];
}

export function applyContextMenuToColumns(
  columns = [],
  getTabulatorInstance,
  options = {}
) {
  const {
    allowCopy = true,
    allowEdit = false,
    allowApplyToAll = false,
    blockActionsOnDisabledCells = false,
    overrideExisting = false,
    skipFields = new Set(),
    onApplyToAll = null,
    allowCut,
    allowClear,
    onCut = null,
    onClear = null
  } = options;
  const resolvedAllowCut = allowCut === undefined ? allowEdit : allowCut;
  const resolvedAllowClear = allowClear === undefined ? allowEdit : allowClear;

  const applyToColumn = (column) => {
    if (!column || typeof column !== "object") return;
    if (Array.isArray(column.columns)) {
      column.columns.forEach(applyToColumn);
      return;
    }
    if (column.field && skipFields.has(column.field)) return;
    if (!overrideExisting && column.contextMenu) return;
    column.contextMenu = (e, cell) =>
      cellContextMenu(
        allowCopy,
        allowEdit,
        allowApplyToAll,
        getTabulatorInstance,
        {
          blockActionsOnDisabledCells,
          cell,
          onApplyToAll,
          allowCut: resolvedAllowCut,
          allowClear: resolvedAllowClear,
          onCut,
          onClear
        }
      );
  };

  columns.forEach(applyToColumn);
  return columns;
}

export function applyPreserveOnEmptyPasteToColumns(columns = [], options = {}) {
  const {
    editorTypes = new Set(["number", "list"]),
    skipFields = new Set(),
    overrideExisting = false
  } = options;

  const applyToColumn = (column) => {
    if (!column || typeof column !== "object") return;
    if (Array.isArray(column.columns)) {
      column.columns.forEach(applyToColumn);
      return;
    }
    if (column.field && skipFields.has(column.field)) return;
    if (column.preserveOnEmptyPaste && !overrideExisting) return;
    if (editorTypes.has(column.editor)) {
      column.preserveOnEmptyPaste = true;
    }
  };

  columns.forEach(applyToColumn);
  return columns;
}

export function applyValueToAllRows(cell, getTabulatorInstance, options = {}) {
  const tabulatorInstance = getTabulatorInstance?.();
  const tableRef =
    typeof tabulatorInstance?.getTable === "function"
      ? tabulatorInstance.getTable()
      : tabulatorInstance;
  if (!cell || !tableRef) return;
  const value = cell.getValue?.();
  const field = cell.getField?.();
  if (!field) return;
  const rowData = cell.getRow?.().getData?.() || {};
  const groupByField =
    tabulatorInstance?.tableGroupsConfig?.groupBy ||
    tabulatorInstance?.groupBy ||
    null;
  const requestId = rowData.request_id;
  const requestName = rowData.request_name;
  const protocolName = rowData.library_protocol_name;
  const applyToAllRows =
    !groupByField && !requestId && !requestName && !protocolName;
  const shouldBlockDisabledCells = options.blockActionsOnDisabledCells === true;
  const tableRows = tableRef?.getRows?.() || [];
  tableRows.forEach((row) => {
    const data = row.getData();
    let sameGroup = false;
    if (groupByField === "request_name") {
      sameGroup =
        (requestId && data.request_id === requestId) ||
        (!requestId && data.request_name === requestName);
    } else if (groupByField === "library_protocol_name") {
      sameGroup = data.library_protocol_name === protocolName;
    } else if (groupByField) {
      sameGroup = data[groupByField] === rowData[groupByField];
    } else {
      sameGroup =
        (requestId && data.request_id === requestId) ||
        (protocolName && data.library_protocol_name === protocolName) ||
        data.request_name === requestName;
    }
    if (applyToAllRows) {
      sameGroup = true;
    }
    if (!sameGroup) return;
    const targetCell = row.getCell(field);
    if (!targetCell) return;
    const targetCellEl = targetCell.getElement?.();
    if (
      shouldBlockDisabledCells &&
      targetCellEl?.classList?.contains("disable-editing")
    ) {
      return;
    }
    const columnDef = targetCell.getColumn().getDefinition();
    const targetRowData = targetCell.getRow().getData();
    const isEditable = (() => {
      if (columnDef.editor === false) return false;
      if (typeof columnDef.editable === "function") {
        return columnDef.editable({
          getRow: () => ({ getData: () => targetRowData })
        });
      }
      if (typeof columnDef.editable === "boolean") {
        return columnDef.editable;
      }
      return true;
    })();
    if (!isEditable) return;
    row.update({ [field]: value });
  });
}

const FOCUSABLE_DIALOG_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])'
].join(",");

function getFocusableDialogElements(container) {
  if (!container) return [];
  return Array.from(
    container.querySelectorAll(FOCUSABLE_DIALOG_SELECTOR)
  ).filter(
    (element) =>
      !element.hidden && element.getAttribute("aria-hidden") !== "true"
  );
}

export function focusFirstElement(container) {
  const [first] = getFocusableDialogElements(container);
  (first || container)?.focus?.();
}

export function trapFocus(event, container) {
  if (event.key !== "Tab" || !container) return false;

  const focusable = getFocusableDialogElements(container);
  if (!focusable.length) {
    event.preventDefault();
    container.focus?.();
    return true;
  }

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
  return true;
}
