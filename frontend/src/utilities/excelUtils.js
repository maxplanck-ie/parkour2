import JSZip from "jszip";
import ExcelJS from "exceljs";
import { showNotification } from "./notificationUtils";

export const XLSX_MIME_TYPE =
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
export const XLSM_MIME_TYPE =
  "application/vnd.ms-excel.sheet.macroEnabled.12";
const SUPPORTED_EXCEL_EXTENSIONS = new Set(["xlsx", "xlsm"]);
const SUPPORTED_EXCEL_MIME_TYPES = new Set([
  XLSX_MIME_TYPE,
  XLSM_MIME_TYPE,
  "application/octet-stream"
]);

export function getExcelTemplateExtension(fileName = "") {
  const normalizedName = String(fileName || "").trim().toLowerCase();
  const match = normalizedName.match(/\.([a-z0-9]+)$/i);
  const extension = match?.[1];
  return SUPPORTED_EXCEL_EXTENSIONS.has(extension) ? extension : "xlsx";
}

export function getExcelMimeTypeForExtension(extension = "xlsx") {
  return String(extension).toLowerCase() === "xlsm"
    ? XLSM_MIME_TYPE
    : XLSX_MIME_TYPE;
}

export function isSupportedExcelTemplateFile(fileOrName) {
  if (!fileOrName) return false;
  const fileName =
    typeof fileOrName === "string" ? fileOrName : fileOrName?.name || "";
  if (/\.(xlsx|xlsm)$/i.test(fileName)) {
    return /\.(xlsx|xlsm)$/i.test(fileName);
  }
  const mimeType =
    typeof fileOrName === "object" ? String(fileOrName?.type || "") : "";
  return SUPPORTED_EXCEL_MIME_TYPES.has(mimeType);
}

export function buildExcelExportFilename(baseName, templateFileName = "") {
  const extension = getExcelTemplateExtension(templateFileName);
  const normalizedBase = String(baseName || "").replace(/\.(xlsx|xlsm)$/i, "");
  return `${normalizedBase}.${extension}`;
}

export function buildExcelDownloadFilename(
  baseName,
  fileName = "",
  contentType = ""
) {
  if (fileName && /\.(xlsx|xlsm)$/i.test(fileName)) {
    return fileName;
  }
  const extension =
    String(contentType).toLowerCase() === XLSM_MIME_TYPE.toLowerCase()
      ? "xlsm"
      : "xlsx";
  const normalizedBase = String(baseName || "download").replace(
    /\.(xlsx|xlsm)$/i,
    ""
  );
  return `${normalizedBase}.${extension}`;
}

export async function validateAndFixExcelBuffer(buffer) {
  try {
    const zip = await JSZip.loadAsync(buffer);
    const sheetFiles = Object.keys(zip.files).filter(
      (f) => f.startsWith("xl/worksheets/") && f.endsWith(".xml")
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
      compression: "DEFLATE"
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
    xm: "http://schemas.microsoft.com/office/excel/2006/main"
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
    let addresses;
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
      formulae
    });
  }

  return validations;
}

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

async function extractDataValidationSnippets(buffer) {
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
      kind: "regular"
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
      sheetNamespaces
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
        formulae
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
      }
    );
  });
}

const NUMERIC_EXPORT_KEY_PATTERNS = [
  /volume/i,
  /value/i,
  /concentration/i,
  /percentage/i,
  /percent/i,
  /depth/i,
  /fragment/i,
  /size/i,
  /phix/i,
  /rqn/i
];
const NUMERIC_EXPORT_HEADER_PATTERNS = [
  /volume/i,
  /value/i,
  /concentration/i,
  /^%$/,
  /%/,
  /percent/i,
  /total/i,
  /depth/i,
  /\bbp\b/i,
  /size/i,
  /phix/i,
  /rqn/i
];
const TEXT_EXPORT_KEY_PATTERNS = [
  /barcode/i,
  /(^|_)id$/i,
  /request/i,
  /date/i,
  /time/i,
  /name/i,
  /coordinate/i,
  /index/i,
  /protocol/i,
  /unit/i,
  /comment/i,
  /pool/i,
  /lane/i,
  /type/i
];

function shouldWriteExportValueAsNumber(column = {}) {
  const explicitType = String(column.excelType || "").toLowerCase();
  if (explicitType === "number") {
    return true;
  }
  if (explicitType === "text") {
    return false;
  }

  const key = String(column.key || "");
  const header = String(column.header || "");
  if (TEXT_EXPORT_KEY_PATTERNS.some((pattern) => pattern.test(key))) {
    return false;
  }
  return (
    NUMERIC_EXPORT_KEY_PATTERNS.some((pattern) => pattern.test(key)) ||
    NUMERIC_EXPORT_HEADER_PATTERNS.some((pattern) => pattern.test(header))
  );
}

function parseExportNumber(value) {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const withoutPercent = trimmed.endsWith("%") ? trimmed.slice(0, -1) : trimmed;
  const compact = withoutPercent.replace(/\s+/g, "");
  if (!/^[+-]?(?:\d+|\d{1,3}(?:[.,]\d{3})+)(?:[.,]\d+)?$/.test(compact)) {
    return null;
  }

  let normalized = compact;
  const lastComma = compact.lastIndexOf(",");
  const lastDot = compact.lastIndexOf(".");
  if (lastComma >= 0 && lastDot >= 0) {
    normalized =
      lastComma > lastDot
        ? compact.replace(/\./g, "").replace(",", ".")
        : compact.replace(/,/g, "");
  } else if (lastComma >= 0) {
    normalized = compact.replace(",", ".");
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeExportCellValue(value, column = {}) {
  if (value === null || value === undefined || value === "") return null;
  if (!shouldWriteExportValueAsNumber(column)) return value;
  const parsed = parseExportNumber(value);
  if (parsed === null) return value;

  const decimalPlaces = Number(column.decimalPlaces);
  if (Number.isInteger(decimalPlaces) && decimalPlaces >= 0) {
    return Number(parsed.toFixed(decimalPlaces));
  }

  return parsed;
}

function getExcelNumberFormat(column = {}) {
  const decimalPlaces = Number(column.decimalPlaces);
  if (!Number.isInteger(decimalPlaces) || decimalPlaces < 0) {
    return "";
  }

  return decimalPlaces === 0 ? "0" : `0.${"0".repeat(decimalPlaces)}`;
}

function normalizeExportRows(rows = [], exportColumns = []) {
  return rows.map((row) => {
    const normalizedRow = { ...row };
    exportColumns.forEach((column) => {
      normalizedRow[column.key] = normalizeExportCellValue(
        row?.[column.key],
        column
      );
    });
    return normalizedRow;
  });
}

function buildExportSheetRows(rows = [], exportColumns = []) {
  const headerRow = exportColumns.map((column) => column.header);
  const normalizedRows = normalizeExportRows(rows, exportColumns);
  const dataRows = normalizedRows.map((row) =>
    exportColumns.map((column) => row?.[column.key] ?? null)
  );
  return [headerRow, ...dataRows];
}

function columnNumberToLetters(columnNumber) {
  let current = Number(columnNumber) || 0;
  let output = "";
  while (current > 0) {
    const remainder = (current - 1) % 26;
    output = String.fromCharCode(65 + remainder) + output;
    current = Math.floor((current - 1) / 26);
  }
  return output || "A";
}

function escapeXmlText(value = "") {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function buildTemplateWorksheetXml(rows = [], exportColumns = []) {
  const sheetRows = buildExportSheetRows(rows, exportColumns);
  const lastColumn = Math.max(exportColumns.length, 1);
  const lastRow = Math.max(sheetRows.length, 1);
  const dimensionRef = `A1:${columnNumberToLetters(lastColumn)}${lastRow}`;
  const colsXml = exportColumns.length
    ? `<cols>${exportColumns
        .map((column, index) => {
          const width = Number(column.width) > 0 ? Number(column.width) : 20;
          const colIndex = index + 1;
          return `<col min="${colIndex}" max="${colIndex}" width="${width}" customWidth="1"/>`;
        })
        .join("")}</cols>`
    : "";
  const rowsXml = sheetRows
    .map((rowValues, rowIndex) => {
      const rowNumber = rowIndex + 1;
      const cellsXml = rowValues
        .map((value, colIndex) => {
          if (value === null || value === undefined || value === "") {
            return "";
          }
          const cellRef = `${columnNumberToLetters(colIndex + 1)}${rowNumber}`;
          if (typeof value === "number" && Number.isFinite(value)) {
            return `<c r="${cellRef}"><v>${value}</v></c>`;
          }
          if (typeof value === "boolean") {
            return `<c r="${cellRef}" t="b"><v>${value ? 1 : 0}</v></c>`;
          }
          const escapedText = escapeXmlText(value);
          return `<c r="${cellRef}" t="inlineStr"><is><t xml:space="preserve">${escapedText}</t></is></c>`;
        })
        .join("");
      return `<row r="${rowNumber}">${cellsXml}</row>`;
    })
    .join("");
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="${dimensionRef}"/>
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  ${colsXml}
  <sheetData>${rowsXml}</sheetData>
</worksheet>`;
}

function markWorkbookForFullRecalculation(workbookXml = "") {
  if (!workbookXml) return workbookXml;
  const calcPrRegex = /<calcPr\b[^>]*\/>/i;
  if (calcPrRegex.test(workbookXml)) {
    return workbookXml.replace(
      calcPrRegex,
      '<calcPr calcId="0" fullCalcOnLoad="1" forceFullCalc="1"/>'
    );
  }
  return workbookXml.replace(
    /<\/workbook>\s*$/i,
    '<calcPr calcId="0" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>'
  );
}

async function createTemplateBasedExportBuffer({
  templateBuffer,
  rows = [],
  exportColumns = [],
  targetSheetName = "Parkour"
}) {
  const zip = await JSZip.loadAsync(templateBuffer);
  const sheetPathMap = await getSheetPathMapFromZip(zip);
  const targetSheetPath = sheetPathMap.get(targetSheetName);

  if (!targetSheetPath || !zip.file(targetSheetPath)) {
    throw new Error(
      `Template sheet "${targetSheetName}" was not found in the workbook.`
    );
  }

  zip.file(targetSheetPath, buildTemplateWorksheetXml(rows, exportColumns));

  if (zip.file("xl/calcChain.xml")) {
    zip.remove("xl/calcChain.xml");
  }
  if (zip.file("xl/_rels/workbook.xml.rels")) {
    const workbookRelsXml = await zip
      .file("xl/_rels/workbook.xml.rels")
      .async("string");
    zip.file(
      "xl/_rels/workbook.xml.rels",
      workbookRelsXml.replace(
        /<Relationship[^>]*Target="calcChain\.xml"[^>]*\/>/i,
        ""
      )
    );
  }
  if (zip.file("[Content_Types].xml")) {
    const contentTypesXml = await zip.file("[Content_Types].xml").async("string");
    zip.file(
      "[Content_Types].xml",
      contentTypesXml.replace(
        /<Override[^>]*PartName="\/xl\/calcChain\.xml"[^>]*\/>/i,
        ""
      )
    );
  }
  if (zip.file("xl/workbook.xml")) {
    const workbookXml = await zip.file("xl/workbook.xml").async("string");
    zip.file("xl/workbook.xml", markWorkbookForFullRecalculation(workbookXml));
  }

  return zip.generateAsync({
    type: "arraybuffer",
    compression: "DEFLATE"
  });
}

export async function createExcelExportBlob({
  rows = [],
  exportColumns = [],
  axiosInstance,
  templateDownloadUrl,
  templateFileName = "",
  sheetName = "Parkour",
  minMatchedHeaders = 6
} = {}) {
  const workbook = new ExcelJS.Workbook();
  let validationsBySheet = null;
  let templateBuffer = null;
  const workbookExtension = getExcelTemplateExtension(templateFileName);

  if (templateDownloadUrl) {
    const response = await axiosInstance.get(templateDownloadUrl, {
      responseType: "arraybuffer"
    });
    templateBuffer = response.data;
    if (workbookExtension === "xlsx") {
      validationsBySheet = await extractDataValidationSnippets(templateBuffer);
      const fixedBuffer = await validateAndFixExcelBuffer(templateBuffer);
      await workbook.xlsx.load(fixedBuffer);
    }
  }

  const targetSheetName = sheetName || "Parkour";
  if (templateBuffer && workbookExtension === "xlsm") {
    const buffer = await createTemplateBasedExportBuffer({
      templateBuffer,
      rows,
      exportColumns,
      targetSheetName
    });
    return new Blob([buffer], {
      type: getExcelMimeTypeForExtension(workbookExtension)
    });
  }

  let worksheet = workbook.getWorksheet(targetSheetName);
  const normalizedRows = normalizeExportRows(
    Array.isArray(rows) ? rows : [],
    exportColumns
  );

  if (!worksheet) {
    worksheet = workbook.addWorksheet(targetSheetName);
    worksheet.columns = exportColumns;
    exportColumns.forEach((col, index) => {
      const numFmt = getExcelNumberFormat(col);
      if (numFmt) {
        worksheet.getColumn(index + 1).numFmt = numFmt;
      }
    });
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
        const numFmt = getExcelNumberFormat(col);
        if (numFmt) {
          worksheet.getColumn(colIdx).numFmt = numFmt;
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
        const numFmt = getExcelNumberFormat(col);
        if (numFmt) {
          worksheet.getColumn(colIdx).numFmt = numFmt;
        }
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
        if (cIdx) {
          row.getCell(cIdx).value = normalizeExportCellValue(
            dataRow?.[col.key],
            col
          );
          const numFmt = getExcelNumberFormat(col);
          if (numFmt) {
            row.getCell(cIdx).numFmt = numFmt;
          }
        }
      });
      if (row.commit) row.commit();
      rIndex++;
    });
  }

  const sortedSheets = [...workbook.worksheets].sort(
    (a, b) => a.orderNo - b.orderNo
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
    type: getExcelMimeTypeForExtension(workbookExtension)
  });
}
