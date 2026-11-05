import { createAxiosObject, urlStringStartsWith } from "../utilities/utilityFunctions";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

/**
 * Fetch available library protocol names from Parkour.
 * Returns an array of protocol names (strings).
 */
export async function getProtocolNames() {
  try {
    const resp = await axiosRef.get(`${urlStringStart}/api/library_sample_shared/libraryprotocols/`, {
      params: { archived: false, ordering: "name" },
    });
    const data = resp.data;
    // Handle both paginated and non-paginated responses
    const results = data.results ?? data;
    return results.map((p) => p.name).filter((n) => n);
  } catch {
    // Fallback to known protocols if API fails
    return [
      "NEBNext UltraExpress DNA Library Prep Kit",
      "NEBNext Ultra II DNA Library Prep Kit for Illumina",
    ];
  }
}