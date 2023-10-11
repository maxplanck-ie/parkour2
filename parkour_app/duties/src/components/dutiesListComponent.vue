<template>
  <div style="margin: 15px; border: 1px solid #006c66">
    <div style="padding: 10px 10px; background: #ecebe5; overflow-y: auto">
      <div style="height: 20px">
        <div style="display: inline; margin-right: 8px">
          <span style="margin-right: 3px">Search:</span><input type="text" />
        </div>
        <div style="display: inline">
          <button style="display: inline; float: right; margin-left: 8px">
            Archive
          </button>
          <button style="display: inline; float: right; margin-left: 8px">
            Unarchive
          </button>
          <button style="display: inline; float: right; margin-left: 8px">
            Delete
          </button>
          <button style="display: inline; float: right; margin-left: 8px">
            Add
          </button>
        </div>
      </div>
    </div>
    <div style="padding: 15px">
      <v-grid
        class="duties-grid"
        theme="material"
        :resize="true"
        :source="rows"
        :columns="columns"
      />
    </div>
  </div>
</template>

<script>
import VGrid from "@revolist/vue3-datagrid";
import axios from 'axios';

export default {
  name: "App",
  components: {
    VGrid,
  },
  data() {
    return {
      selected: {},
      allSelectedStatus: 0,
      rows: [
        {
          id: 1,
          resp_person: "Saurabh",
          back_person: "Saurabh",
          start_date: "20-20-2023",
          end_date: "30-30-2030",
          facility: "DeepInfo",
          platform: "Parkour",
          comments: "This is a comment.",
          archived: "No",
        },

        {
          id: 2,
          resp_person: "Saurabh",
          back_person: "Saurabh",
          start_date: "20-20-2023",
          end_date: "30-30-2030",
          facility: "DeepInfo",
          platform: "Parkour",
          comments: "This is a comment.",
          archived: "No",
        },

        {
          id: 3,
          resp_person: "Saurabh",
          back_person: "Saurabh",
          start_date: "20-20-2023",
          end_date: "30-30-2030",
          facility: "DeepInfo",
          platform: "Parkour",
          comments: "This is a comment.",
          archived: "No",
        },
      ],
    };
  },
  created() {
    try {
      axios.get("http://localhost:9980/duty")
      .then(response => 
        console.log(response.data))
      } catch (error) {
        console.log(error);
      }
  },
  watch: {
    isAllSelected(newV, oldV) {
      if (newV !== oldV) {
        this.allSelectedStatus = newV;
      }
    },
  },
  computed: {
    isAllSelected() {
      const selected = Object.keys(this.selected).length;
      if (selected === this.rows.length) {
        return 2;
      }
      if (selected) {
        return 1;
      }
      return 0;
    },
    columns() {
      const status = this.allSelectedStatus;
      const columnTemplate = (h) => {
        let inputVNode = h("input", {
          type: "checkbox",
          indeterminate: status === 1,
          checked: status > 1 || undefined,
          onChange: (e) => {
            this.selectAll(e.target.checked);
            this.doChange(inputVNode, e.target.checked);
          },
        });
        return [inputVNode, "Responsible Person"];
      };
      const cellTemplate = (h, { model, prop }) => {
        let inputVNode = h("input", {
          type: "checkbox",
          checked: model.selected || undefined,
          onChange: (e) => {
            this.selectSingle(model, e.target.checked);
            this.doChange(inputVNode, e.target.checked);
          },
        });
        return h("label", undefined, inputVNode, model[prop]);
      };
      return [
        {
          columnTemplate,
          cellTemplate,
          prop: "resp_person",
          size: 200,
          editor: "select",
        },
        {
          name: "Backup Person",
          prop: "back_person",
          size: 150,
          editor: "select",
        },
        {
          name: "Start Date",
          prop: "start_date",
          type: "date",
          size: 120,
        },
        {
          name: "End Date",
          prop: "end_date",
          type: "date",
          size: 120,
        },
        {
          name: "Facility",
          prop: "facility",
          size: 150,
        },
        {
          name: "Platform",
          prop: "platform",
          size: 150,
        },
        {
          name: "Archived",
          prop: "archived",
          size: 100,
        },
        {
          name: "Comments",
          prop: "comments",
          size: 300,
        },
      ];
    },
  },
  methods: {
    selectAll(ckecked = false) {
      this.rows.forEach((r) => this.updateSelectedRow(r, ckecked));
      this.selected = { ...this.selected };
      this.rows = [...this.rows];
    },
    selectSingle(row, checked) {
      this.updateSelectedRow(row, checked);
      this.selected = { ...this.selected };
    },
    updateSelectedRow(row, checked) {
      row.selected = checked;
      if (checked) {
        this.selected[row.id] = true;
      } else {
        delete this.selected[row.id];
      }
    },
    doChange(vNode, isChecked) {
      if (vNode) {
        vNode.$attrs$.checked = isChecked;
      }
    }
  },
};
</script>

<style>
revo-grid {
  height: 723px;
}
input[type="checkbox"] {
  margin-right: 15px;
}
.edit-input-wrapper > input {
  outline: none;
  background-color: #29485d2f !important;
  border: none;
  padding-left: 12px;
}
.header-wrapper,
.rowHeaders {
  background-color: #29485d54 !important;
}
</style>
