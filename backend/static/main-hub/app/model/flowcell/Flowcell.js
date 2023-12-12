Ext.define("MainHub.model.flowcell.Flowcell", {
  extend: "MainHub.model.Base",

  fields: [
    {
      name: "pk",
      type: "int",
    },
    {
      name: "name",
      type: "string",
    },
    {
      name: "flowcell_id",
      type: "string",
    },
    {
      name: "flowcell",
      type: "int",
    },
    {
      name: "pool",
      type: "int",
    },
    {
      name: "pool_name",
      type: "string",
    },
    {
      name: "create_time",
      type: "date",
    },
    {
      name: "read_length_name",
      type: "string",
    },
    {
      name: "sequencer",
      type: "int",
    },
    {
      name: "pool_size_name",
      type: "string",
    },
    {
      name: "index_i7_show",
      type: "string",
    },
    {
      name: "index_i5_show",
      type: "string",
    },
    {
      name: "equal_representation",
      type: "bool",
    },
    {
      name: "loading_concentration",
      type: "float",
      allowNull: true,
    },
    {
      name: "phix",
      type: "float",
      allowNull: true,
    },
    {
      name: "request",
      type: "string",
    },
    {
      name: "protocol",
      type: "string",
    },
    {
      name: "read1_cycles",
      type: "int",
    },
    {
      name: "read2_cycles",
      type: "int",
    },
    {
      name: "index1_cycles",
      type: "int",
    },
    {
      name: "index2_cycles",
      type: "int",
    },
    {
      name: "run_name",
      type: "string",
    },
    {
      name: "library_prep_kits",
      type: "string",
    },
  ],
});
