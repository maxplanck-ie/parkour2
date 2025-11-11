export const statusMap = {
  "-1": "Quality Check Failed",
  "-2": "Quality Check Compromised",
  0: "Pending Submission",
  1: "Submission Completed",
  2: "Quality Check Approved",
  3: "Library Prepared",
  4: "Library Pooled",
  5: "Sequencing",
  6: "Delivered",
};

export function getStatusClass(status) {
  switch (String(status)) {
    case "-1":
      return "quality-check-failed";
    case "-2":
      return "quality-check-compromised";
    case "0":
      return "pending-submission";
    case "1":
      return "submission-completed";
    case "2":
      return "quality-check-approved";
    case "3":
      return "library-prepared";
    case "4":
      return "library-pooled";
    case "5":
      return "sequencing";
    case "6":
      return "delivered";
    default:
      return "";
  }
}
