export const REQUEST_FILE_TYPE_OTHER = "Other";

export const REQUEST_FILE_TYPE_OPTIONS = [
  "RNA_FragmentSize_QC",
  "DNA_FragmentSize_QC",
  "Library_FragmentSize_QC",
  "Sample_Barcodes",
  "Experimental_Design",
  REQUEST_FILE_TYPE_OTHER
];

const REQUEST_FILE_TYPE_PATTERN = /^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$/;

export function isValidRequestFileType(value) {
  return REQUEST_FILE_TYPE_PATTERN.test(String(value || ""));
}

export function normaliseRequestFile(file = {}) {
  const storedType = String(file.file_type || REQUEST_FILE_TYPE_OTHER);
  const isKnownType = REQUEST_FILE_TYPE_OPTIONS.includes(storedType);
  return {
    ...file,
    file_type: storedType,
    fileTypeChoice: isKnownType ? storedType : REQUEST_FILE_TYPE_OTHER,
    customFileType: isKnownType ? "" : storedType
  };
}

export function resolveRequestFileType(file = {}) {
  if (file.fileTypeChoice !== REQUEST_FILE_TYPE_OTHER) {
    return file.fileTypeChoice;
  }
  return String(file.customFileType || REQUEST_FILE_TYPE_OTHER).trim();
}

export function requestFileTypesPayload(files = []) {
  return Object.fromEntries(
    files
      .filter((file) => file?.id !== undefined && file?.id !== null)
      .map((file) => [String(file.id), resolveRequestFileType(file)])
  );
}
