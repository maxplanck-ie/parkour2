<template>
    <div style="margin: 15px; border: 1px solid #006c66;">
<div style="padding: 10px 10px; background: #ecebe5; overflow-y: auto">
    <div style="height: 20px;">
    <div style="display: inline; margin-right:8px"><span style="margin-right: 3px">Search:</span><input type="text"/></div>
    <div style="display: inline">
    <button style="display: inline; float: right; margin-left:8px">Archive</button>
    <button style="display: inline; float: right; margin-left:8px">Unrchive</button>
    <button style="display: inline; float: right; margin-left:8px">Delete</button>
    <button style="display: inline; float: right; margin-left:8px">Add</button>
    </div>
   </div>
    </div>
    <div style="padding: 15px">
        <v-grid theme="material" resize="true" :source="rows" :columns="columns" />
    </div>
</div>
</template>

<script>
import VGrid from "@revolist/vue3-datagrid";
export default {
    name: "App",
    data() {
    return {
        selected: {},
        allSelectedStatus: 0,
        columns: [
        {
            size: 40,
            cellTemplate: (createElement, props) => {
            const input = createElement("input", {
                type: "checkbox",
                checked: props.model["checked"],
                onChange(e) {
                props.model["checked"] = e.target.checked;
                if (input) {
                    input.$attrs$.checked = e.target.checked;
                }
                onSelectItem(props.model);
                }
            });
            return input;
            }
        },
        {
            name: "Responsible Person",
            prop: "resp_person",
            size: 180,
        },
        {
            name: "Backup Person",
            prop: "back_person",
            size: 150,
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
            name: "Comments",
            prop: "comments",
            size: 300,
        },
        {
            name: "Archived",
            prop: "archived",
            size: 100,
        }
        ],
        rows: [
        {
            resp_person: "Saurabh",
            back_person: "Saurabh",
            start_date: "20-20-2023",
            end_date: "30-30-2030",
            facility: "DeepInfo",
            platform: "Parkour",
            comments: "This is a comment."
        },

        {
            resp_person: "Saurabh",
            back_person: "Saurabh",
            start_date: "20-20-2023",
            end_date: "30-30-2030",
            facility: "DeepInfo",
            platform: "Parkour",
            comments: "This is a comment."
        },

        {
            resp_person: "Saurabh",
            back_person: "Saurabh",
            start_date: "20-20-2023",
            end_date: "30-30-2030",
            facility: "DeepInfo",
            platform: "Parkour",
            comments: "This is a comment."
        },
        ],
    };
    },
    watch: {
    isAllSelected(newV, oldV) {
      if (newV !== oldV) {
        this.allSelectedStatus = newV;
      }
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
    },
    },
    components: {
    VGrid,
    },
};
</script>

<style>
revo-grid {
    height: 723px;
}
</style>
