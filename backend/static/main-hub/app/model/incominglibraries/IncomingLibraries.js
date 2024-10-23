Ext.define("MainHub.model.incominglibraries.IncomingLibraries", {
  extend: "MainHub.model.Record",
  fields: [
    {
      name: "dilution_factor",
      type: "int"
    },
    {
      name: "selected",
      type: "bool"
    },
    {
      name: "concentration_facility",
      type: "float",
      allowNull: true
    },
    {
      name: "concentration_method_facility",
      type: "int"
    },
    {
      name: "sample_volume_facility",
      type: "int",
      allowNull: true
    },
    {
      name: "amount_facility",
      type: "float",
      allowNull: true
    },
    {
      name: "size_distribution_facility",
      type: "float",
      allowNull: true
    },
    {
      name: "measuring_unit_facility",
      type: "string"
    },
    {
      name: "measured_value_facility",
      type: "float",
      allowNull: true,
      defaultValue: null
    },
    {
      name: "samples_submitted",
      type: "bool"
    },
    {
      name: "quality_check",
      type: "string",
      allowNull: true
    }
  ]
});
