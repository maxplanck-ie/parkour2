import { useToast } from "vue-toastification";
import axios from "axios";
import Cookies from "js-cookie";
import JSZip from "jszip";
import ExcelJS from "exceljs";

const toast = useToast();

export function showNotification(content, type) {
  let options = {
    timeout: 5000,
    position: "top-left",
  };

  if (type === "info") toast.info(content, options);
  else if (type === "success") toast.success(content, options);
  else if (type === "error") toast.error(content, options);
  else if (type === "warning") toast.warning(content, options);
}

function notifyParentAuthRequired() {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(
        {
          source: "mainhub-vue",
          type: "auth-required",
        },
        window.location.origin,
      );
    }
  } catch (error) {
    // No-op: notification is a best-effort signal.
  }
}

export function handleError(error) {
  if (
    error.response &&
    error.response.status &&
    error.response.status === 403
  ) {
    let slices = window.location.href.split("/vue/");
    notifyParentAuthRequired();
    window.location.href =
      urlStringStartsWith() + "/login/?next=/vue/" + slices[1];
  } else if (error.message) {
    showNotification("Error: " + error.message, "error");
  } else {
    showNotification(
      "An error occurred while processing your request.\nPlease contact the BioInfo department for assistance.",
      "error",
    );
  }
}

export function getProp(object, keys, defaultVal) {
  keys = Array.isArray(keys) ? keys : keys.split(".");
  object = object[keys[0]];
  if (object && keys.length > 1) {
    return getProp(object, keys.slice(1), defaultVal);
  }
  return object === undefined ? defaultVal : object;
}

export function urlStringStartsWith() {
  let urlString = window.location.href.split("/vue/");
  if (urlString[0] === "http://localhost:5174") {
    return "http://localhost:9980";
  } else {
    return urlString[0];
  }
}

export function createAxiosObject() {
  return axios.create({
    withCredentials: true,
    headers: {
      "content-type": "application/json",
      "X-CSRFToken": Cookies.get("csrftoken"),
    },
  });
}

export function isValidDate(dateString) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return false;
  const [yearStr, monthStr, dayStr] = dateString.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  if (year < 1000 || year > 9999) return false;
  if (month < 1 || month > 12) return false;
  if (day < 1 || day > 31) return false;
  const date = new Date(dateString);
  return (
    date.getFullYear() === year &&
    date.getMonth() + 1 === month &&
    date.getDate() === day
  );
}

export function formatDateForInput(date) {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDisplayDate(date) {
  if (!date) return "";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}.${month}.${year}`;
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
  allowPaste,
  allowApplyToAll,
  getTabulatorInstance,
  options = {},
) {
  const shouldBlockDisabledCells =
    options.blockActionsOnDisabledCells === true;
  const tabulatorInstance = getTabulatorInstance();
  const tableRef =
    typeof tabulatorInstance?.getTable === "function"
      ? tabulatorInstance.getTable()
      : tabulatorInstance;
  const operations = [];
  let isRangeSelected = false;
  let selectedRangesData = tableRef?.getRangesData?.() || [];
  if (selectedRangesData.length > 0) {
    let firstRangeFields = Object.keys(selectedRangesData[0][0]);
    isRangeSelected =
      selectedRangesData[0].length > 1 || firstRangeFields.length > 1;
  }

  if (isRangeSelected) {
    showNotification(
      "Please use Ctrl+C to copy, and Ctrl+V to paste in a range selection.",
      "info",
    );
  } else {
    if (allowApplyToAll) {
      operations.push({
        label: "Apply to All",
        action: (e, cell) => {
          const value = cell.getValue();
          const field = cell.getField();
          const rowData = cell.getRow().getData();
          const groupByField =
            tabulatorInstance?.tableGroupsConfig?.groupBy ||
            tabulatorInstance?.groupBy ||
            null;
          const requestId = rowData.request_id;
          const requestName = rowData.request_name;
          const protocolName = rowData.library_protocol_name;
          const applyToAllRows =
            !groupByField && !requestId && !requestName && !protocolName;
          const tableRows = tableRef?.getRows?.() || [];

          tableRows.forEach((row) => {
            const data = row.getData();
            let sameGroup = false;

            // Incoming Libraries & Samples: apply within the same request
            if (groupByField === "request_name") {
              sameGroup =
                (requestId && data.request_id === requestId) ||
                (!requestId && data.request_name === requestName);
            }
            // Library Preparation: apply within the same library protocol
            else if (groupByField === "library_protocol_name") {
              sameGroup = data.library_protocol_name === protocolName;
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
                  getRow: () => ({ getData: () => targetRowData }),
                });
              }
              if (typeof columnDef.editable === "boolean") {
                return columnDef.editable;
              }
              return Boolean(columnDef.editor);
            })();
            if (isEditable) {
              targetCell.setValue(value);
            }
          });
        },
      });
    }

    if (allowCopy) {
      operations.push({
        label: "Copy",
        action: (e, cell) => {
          const value = cell.getValue();
          navigator.clipboard.writeText(value);
        },
      });
    }

    if (allowPaste) {
      operations.push({
        label: "Paste",
        action: (e, cell) => {
          const cellEl = cell.getElement?.();
          if (
            shouldBlockDisabledCells &&
            cellEl?.classList?.contains("disable-editing")
          ) {
            return;
          }
          const columnDef = cell.getColumn().getDefinition();
          const rowData = cell.getRow().getData();
          const isEditable = (() => {
            if (columnDef.editor === false) return false;
            if (typeof columnDef.editable === "function") {
              return columnDef.editable({
                getRow: () => ({ getData: () => rowData }),
              });
            }
            if (typeof columnDef.editable === "boolean") {
              return columnDef.editable;
            }
            return Boolean(columnDef.editor);
          })();
          if (!isEditable) {
            return;
          }
          navigator.clipboard.readText().then((text) => {
            try {
              const validatedValue = tabulatorInstance.validateCellValue(
                text,
                columnDef,
                rowData,
              );
              cell.setValue(validatedValue);
            } catch (error) {
              showNotification(error.message, "error");
            }
          });
        },
      });
    }
  }

  return operations.length ? operations : [];
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
  const shouldBlockDisabledCells =
    options.blockActionsOnDisabledCells === true;
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

export async function validateAndFixExcelBuffer(buffer) {
  try {
    const zip = await JSZip.loadAsync(buffer);
    const sheetFiles = Object.keys(zip.files).filter(
      (f) => f.startsWith("xl/worksheets/") && f.endsWith(".xml"),
    );
    for (const file of sheetFiles) {
      let xmlText = await zip.files[file].async("string");
      xmlText = xmlText.replace(/<dimension[^>]*\/>/g, "");
      xmlText = xmlText.replace(/<dimension[^>]*>.*?<\/dimension>/g, "");
      xmlText = xmlText.replace(/sqref="[^"]*"/g, (match) => {
        if (match.includes("XFD1048576")) {
          return 'sqref="A1:Z1000"';
        }
        return match;
      });
      zip.file(file, xmlText);
    }
    if (zip.files["xl/calcChain.xml"]) {
      delete zip.files["xl/calcChain.xml"];
    }
    const fixedBuffer = await zip.generateAsync({
      type: "arraybuffer",
      compression: "DEFLATE",
    });

    return fixedBuffer;
  } catch (error) {
    showNotification("Error in validating the excel file: " + error, "error");
    throw error;
  }
}

function parseDataValidations(snippet, namespaces) {
  if (!snippet) return [];
  const nsMap = new Map(namespaces ? namespaces.entries() : []);
  const KNOWN_NAMESPACE_URIS = {
    main: "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    mc: "http://schemas.openxmlformats.org/markup-compatibility/2006",
    r: "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    x14: "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
    x14ac: "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac",
    x15: "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main",
    x15ac: "http://schemas.microsoft.com/office/spreadsheetml/2010/11/ac",
    x16: "http://schemas.microsoft.com/office/spreadsheetml/2015/09/main",
    x16r2: "http://schemas.microsoft.com/office/spreadsheetml/2015/02/main",
    x16r3: "http://schemas.microsoft.com/office/spreadsheetml/2015/02/revision",
    xr: "http://schemas.microsoft.com/office/spreadsheetml/2014/revision",
    xr2: "http://schemas.microsoft.com/office/spreadsheetml/2015/revision2",
    xr3: "http://schemas.microsoft.com/office/spreadsheetml/2016/revision3",
    xm: "http://schemas.microsoft.com/office/excel/2006/main",
  };
  Object.entries(KNOWN_NAMESPACE_URIS).forEach(([prefix, uri]) => {
    if (prefix === "main") return;
    if (!nsMap.has(prefix) && uri) {
      nsMap.set(prefix, uri);
    }
  });
  const mainNs = KNOWN_NAMESPACE_URIS.main;
  const nsAttrString = Array.from(nsMap.entries())
    .map(([pfx, uri]) => `xmlns:${pfx}="${uri}"`)
    .join(" ");
  const attrWithDefault = nsAttrString
    ? ` ${nsAttrString} xmlns="${mainNs}"`
    : ` xmlns="${mainNs}"`;
  const wrapped = `<root${attrWithDefault}>${snippet}</root>`;
  const parser = new DOMParser();
  const doc = parser.parseFromString(wrapped, "application/xml");
  const errors = doc.getElementsByTagName("parsererror");
  const validations = [];
  const nodes = doc.getElementsByTagNameNS("*", "dataValidation");
  const parseBool = (value) => {
    if (value === null || value === undefined) return undefined;
    const normalized = String(value).toLowerCase();
    if (normalized === "1" || normalized === "true") return true;
    if (normalized === "0" || normalized === "false") return false;
    return undefined;
  };

  const getFirstChildText = (node, localName) => {
    const match = node.getElementsByTagNameNS("*", localName).item(0);
    return match?.textContent?.trim() || undefined;
  };

  for (let i = 0; i < nodes.length; i++) {
    const node = nodes.item(i);
    if (!node) continue;
    const isStandard =
      !node.namespaceURI || node.namespaceURI === mainNs || node.prefix === "";
    let addresses = [];
    let type = node.getAttribute("type") || "list";
    let operator = undefined;
    let allowBlank;
    let showInputMessage;
    let showErrorMessage;
    let promptTitle;
    let prompt;
    let errorTitle;
    let error;
    let errorStyle;
    let formulae;

    if (isStandard) {
      const sqrefAttr = node.getAttribute("sqref") || "";
      addresses = sqrefAttr
        .split(/\s+/)
        .map((part) => part.trim())
        .filter(Boolean);
      type = node.getAttribute("type") || "list";
      operator = node.getAttribute("operator") || undefined;
      allowBlank = parseBool(node.getAttribute("allowBlank"));
      showInputMessage = parseBool(node.getAttribute("showInputMessage"));
      showErrorMessage = parseBool(node.getAttribute("showErrorMessage"));
      promptTitle = node.getAttribute("promptTitle") || undefined;
      prompt = node.getAttribute("prompt") || undefined;
      errorTitle = node.getAttribute("errorTitle") || undefined;
      error = node.getAttribute("error") || undefined;
      errorStyle = node.getAttribute("errorStyle") || undefined;
      const formulas = [];
      ["formula1", "formula2"].forEach((tag) => {
        const text = getFirstChildText(node, tag);
        if (text) formulas.push(text);
      });
      formulae = formulas.length ? formulas : undefined;
    } else {
      const sqrefText = getFirstChildText(node, "sqref");
      if (!sqrefText) continue;
      addresses = sqrefText.split(/\s+/).filter(Boolean);
      if (!addresses.length) continue;
      allowBlank = parseBool(node.getAttribute("allowBlank"));
      showInputMessage = parseBool(node.getAttribute("showInputMessage"));
      showErrorMessage = parseBool(node.getAttribute("showErrorMessage"));
      const formulaText = getFirstChildText(node, "f");
      formulae = formulaText && formulaText.length ? [formulaText] : undefined;
    }

    if (!addresses.length) continue;
    validations.push({
      addresses,
      type,
      operator,
      allowBlank,
      showInputMessage,
      showErrorMessage,
      promptTitle,
      prompt,
      errorTitle,
      error,
      errorStyle,
      formulae,
    });
  }

  return validations;
}

async function extractDataValidationSnippets(buffer) {
  async function getSheetPathMapFromZip(zip) {
    const sheetNameToPath = new Map();
    const workbookFile = zip.file("xl/workbook.xml");
    const relsFile = zip.file("xl/_rels/workbook.xml.rels");
    const relationshipRegex =
      /<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"/g;
    const sheetPathRegex = /<sheet[^>]*name="([^"]+)"[^>]*r:id="([^"]+)"/g;
    const normalizeSheetTargetPath = (target) => {
      if (!target) return null;
      let normalized = target.replace(/\\/g, "/");
      while (normalized.startsWith("../")) {
        normalized = normalized.slice(3);
      }
      normalized = normalized.replace(/^\/+/, "");
      if (!normalized.startsWith("xl/")) {
        normalized = `xl/${normalized}`;
      }
      return normalized;
    };
    if (!workbookFile || !relsFile) return sheetNameToPath;
    const workbookXml = await workbookFile.async("string");
    const relsXml = await relsFile.async("string");
    const sheetToRelId = new Map();
    let sheetMatch;
    while ((sheetMatch = sheetPathRegex.exec(workbookXml)) !== null) {
      sheetToRelId.set(sheetMatch[1], sheetMatch[2]);
    }
    const relIdToTarget = new Map();
    let relMatch;
    while ((relMatch = relationshipRegex.exec(relsXml)) !== null) {
      relIdToTarget.set(relMatch[1], normalizeSheetTargetPath(relMatch[2]));
    }
    sheetToRelId.forEach((relId, sheetName) => {
      const path = relIdToTarget.get(relId);
      if (path) sheetNameToPath.set(sheetName, path);
    });
    return sheetNameToPath;
  }
  const extractSheetNamespaces = (xml) => {
    const namespaces = new Map();
    if (!xml) return namespaces;
    const openingMatch = xml.match(/<worksheet[^>]*>/i);
    if (!openingMatch) return namespaces;
    const attrRegex = /xmlns:([A-Za-z_][\w.-]*)=(?:"([^"]*)"|'([^']*)')/g;
    let attrMatch;
    while ((attrMatch = attrRegex.exec(openingMatch[0])) !== null) {
      const uri = attrMatch[2] !== undefined ? attrMatch[2] : attrMatch[3];
      namespaces.set(attrMatch[1], uri);
    }
    return namespaces;
  };
  const findDataValidationsSnippet = (xml) => {
    if (!xml) return null;
    const extRegex =
      /<ext\b[^>]*>[\s\S]*?<x14:dataValidations\b[\s\S]*?<\/x14:dataValidations>[\s\S]*?<\/ext>/gi;
    let extMatch;
    while ((extMatch = extRegex.exec(xml)) !== null) {
      return { snippet: extMatch[0], kind: "x14-ext" };
    }
    const openRegex = /<([A-Za-z0-9_]+:)?dataValidations\b[^>]*>/i;
    const openMatch = openRegex.exec(xml);
    if (!openMatch) return null;
    const prefix = openMatch[1] || "";
    const searchStart = openMatch.index + openMatch[0].length;
    const rest = xml.slice(searchStart);
    const closeRegex = new RegExp(`</${prefix}dataValidations>`, "i");
    const closeMatch = closeRegex.exec(rest);
    if (!closeMatch) return null;
    const closeIndex = searchStart + closeMatch.index;
    const endIndex = closeIndex + closeMatch[0].length;
    return {
      snippet: xml.slice(openMatch.index, endIndex),
      kind: "regular",
    };
  };
  if (!buffer) return new Map();
  const zip = await JSZip.loadAsync(buffer);
  const sheetNameToPath = await getSheetPathMapFromZip(zip);
  const validationsBySheet = new Map();
  for (const [sheetName, path] of sheetNameToPath.entries()) {
    const sheetFile = zip.file(path);
    if (!sheetFile) continue;
    const sheetXml = await sheetFile.async("string");
    const sheetNamespaces = extractSheetNamespaces(sheetXml);
    const found = findDataValidationsSnippet(sheetXml);
    if (!found?.snippet) {
      continue;
    }
    const parsedValidations = parseDataValidations(
      found.snippet,
      sheetNamespaces,
    );
    if (parsedValidations.length) {
      validationsBySheet.set(sheetName, parsedValidations);
    }
  }
  return validationsBySheet;
}

function applyTemplateValidations(workbook, validationsBySheet) {
  if (!workbook || !validationsBySheet?.size) return;
  validationsBySheet.forEach((validations, sheetName) => {
    if (!validations || !validations.length) return;
    const targetSheet = workbook.getWorksheet(sheetName);
    const dataValidations = targetSheet?.dataValidations;
    if (!targetSheet || !dataValidations) return;
    validations.forEach(
      ({
        addresses,
        type,
        operator,
        allowBlank,
        showInputMessage,
        showErrorMessage,
        promptTitle,
        prompt,
        errorTitle,
        error,
        errorStyle,
        formulae,
      }) => {
        if (!addresses || !addresses.length) return;
        addresses.forEach((address) => {
          const options = { type: type || "list" };
          if (operator) options.operator = operator;
          if (typeof allowBlank === "boolean") options.allowBlank = allowBlank;
          if (typeof showInputMessage === "boolean") {
            options.showInputMessage = showInputMessage;
          }
          if (typeof showErrorMessage === "boolean") {
            options.showErrorMessage = showErrorMessage;
          }
          if (errorStyle) options.errorStyle = errorStyle;
          if (error) options.error = error;
          if (errorTitle) options.errorTitle = errorTitle;
          if (prompt) options.prompt = prompt;
          if (promptTitle) options.promptTitle = promptTitle;
          if (formulae && formulae.length) options.formulae = [...formulae];
          dataValidations.add(address, options);
        });
      },
    );
  });
}

export async function createExcelExportBlob({
  rows = [],
  exportColumns = [],
  axiosInstance,
  templateDownloadUrl,
  sheetName = "Parkour",
  minMatchedHeaders = 6,
} = {}) {
  const workbook = new ExcelJS.Workbook();
  let validationsBySheet = null;

  if (templateDownloadUrl) {
    const response = await axiosInstance.get(templateDownloadUrl, {
      responseType: "arraybuffer",
    });
    const templateBuffer = response.data;
    validationsBySheet = await extractDataValidationSnippets(templateBuffer);
    const fixedBuffer = await validateAndFixExcelBuffer(templateBuffer);
    await workbook.xlsx.load(fixedBuffer);
  }

  const targetSheetName = sheetName || "Parkour";
  let worksheet = workbook.getWorksheet(targetSheetName);
  const normalizedRows = Array.isArray(rows) ? rows : [];

  if (!worksheet) {
    worksheet = workbook.addWorksheet(targetSheetName);
    worksheet.columns = exportColumns;
    if (normalizedRows.length) {
      worksheet.addRows(normalizedRows);
    }
  } else {
    const headerRowIndex = 1;
    const headerRow = worksheet.getRow(headerRowIndex);
    const headerToCol = new Map();
    for (let c = 1; c <= headerRow.cellCount; c++) {
      let value = headerRow.getCell(c).value;
      if (value && typeof value === "object") {
        if (value.richText) {
          value = value.richText.map((t) => t.text).join("");
        } else if (value.text) {
          value = value.text;
        }
      }
      if (typeof value === "string" && value.trim()) {
        headerToCol.set(value.trim(), c);
      }
    }

    const keyToCol = new Map();
    let matchedHeaders = 0;
    exportColumns.forEach((col) => {
      const colIdx = headerToCol.get(col.header);
      if (colIdx) {
        keyToCol.set(col.key, colIdx);
        matchedHeaders++;
        if (col.width) {
          worksheet.getColumn(colIdx).width = col.width;
        }
      }
    });

    const matchThreshold = exportColumns.length
      ? Math.min(minMatchedHeaders, exportColumns.length)
      : 0;

    if (matchedHeaders < matchThreshold) {
      const lastRow = worksheet.rowCount;
      for (let r = 2; r <= lastRow; r++) {
        const row = worksheet.getRow(r);
        row.eachCell((cell) => {
          cell.value = null;
        });
        if (row.commit) row.commit();
      }
      exportColumns.forEach((col, i) => {
        const colIdx = i + 1;
        worksheet.getCell(headerRowIndex, colIdx).value = col.header;
        if (col.width) worksheet.getColumn(colIdx).width = col.width;
        keyToCol.set(col.key, colIdx);
      });
    } else {
      const lastRow = worksheet.rowCount;
      for (let r = headerRowIndex + 1; r <= lastRow; r++) {
        const row = worksheet.getRow(r);
        exportColumns.forEach((col) => {
          const cIdx = keyToCol.get(col.key);
          if (cIdx) row.getCell(cIdx).value = null;
        });
        if (row.commit) row.commit();
      }
    }

    let rIndex = headerRowIndex + 1;
    normalizedRows.forEach((dataRow) => {
      const row = worksheet.getRow(rIndex);
      exportColumns.forEach((col) => {
        const cIdx = keyToCol.get(col.key);
        if (cIdx) row.getCell(cIdx).value = dataRow?.[col.key] ?? null;
      });
      if (row.commit) row.commit();
      rIndex++;
    });
  }

  const sortedSheets = [...workbook.worksheets].sort(
    (a, b) => a.orderNo - b.orderNo,
  );
  const targetSheet = worksheet;
  const otherSheets = sortedSheets.filter((sheet) => sheet !== targetSheet);
  targetSheet.orderNo = 0;
  otherSheets.forEach((sheet, index) => {
    sheet.orderNo = index + 1;
  });
  workbook.views = [{ activeTab: 0, firstSheet: 0 }];

  workbook.worksheets.forEach((sheet) => {
    if (sheet.name === targetSheetName) return;
    sheet.eachRow((row) => {
      row.eachCell((cell) => {
        if (
          cell &&
          (cell.formula ||
            (cell.model && cell.model.formula) ||
            (cell.value && cell.value.formula))
        ) {
          if (cell.model) cell.model.result = undefined;
          if (cell.value && typeof cell.value === "object") {
            cell.value.result = undefined;
          }
        }
      });
    });
  });

  if (validationsBySheet?.size) {
    applyTemplateValidations(workbook, validationsBySheet);
  }

  const buffer = await workbook.xlsx.writeBuffer();
  return new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}
