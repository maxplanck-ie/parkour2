export function buildRequestGroupSummary(data = []) {
  const uniqueTypes = [
    ...new Set(
      data
        .map((item) =>
          String(item?.type || "")
            .trim()
            .toUpperCase()
        )
        .filter((type) => type === "L" || type === "S")
    )
  ];

  const countLabel =
    uniqueTypes.length === 1
      ? uniqueTypes[0] === "L"
        ? "Libraries"
        : "Samples"
      : "Libraries/Samples";

  const samplesSubmitted = data.some(
    (item) => item?.samples_submitted === true
  );
  const gmo = data.some((item) => item?.gmo === true);

  const totalDepth = Number(
    data
      .reduce((sum, row) => sum + Number(row?.sequencing_depth || 0), 0)
      .toFixed(1)
  );

  const readLengthLabels = [
    ...new Set(
      data
        .map((row) =>
          row?.read_length_name !== undefined
            ? row.read_length_name
            : row?.read_length
        )
        .filter((value) => {
          if (value === null || value === undefined) {
            return false;
          }
          return String(value).trim().length > 0;
        })
        .map((value) => String(value).trim())
    )
  ];

  const readLengthDisplay = readLengthLabels.length
    ? readLengthLabels.join(", ")
    : "No Read Length";

  const biosafetyLabels = [
    ...new Set(
      data
        .map((item) => item?.biosafety_level)
        .filter(
          (value) =>
            value !== null &&
            value !== undefined &&
            String(value).trim().length > 0
        )
        .map((value) => String(value).trim().toUpperCase())
    )
  ];

  const biosafetyLevel = biosafetyLabels.length
    ? biosafetyLabels.join(" and ")
    : "No BSL";

  return {
    countLabel,
    samplesSubmitted,
    gmo,
    totalDepth,
    readLengthDisplay,
    biosafetyLevel
  };
}
