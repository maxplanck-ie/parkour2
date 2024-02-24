Ext.define("MainHub.model.invoicing.BillingPeriod", {
  extend: "MainHub.model.Base",

  fields: [
    {
      name: "name",
      type: "string"
    },
    {
      name: "value",
      type: "auto"
    },
  ],

  hasMany: {
    model: "ReportUrl",
    name: "report_urls",
  },
});

Ext.define("ReportUrl", {
  extend: "Ext.data.Model",
  fields: [
    {
      name: "organization_id",
      type: "int",
    },
    {
      name: "url",
      type: "string",
    },
  ],
  belongsTo: "MainHub.model.invoicing.BillingPeriod",
});
