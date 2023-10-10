<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="header" style="padding: 5px, margin: 5px">Manage Duties</div>
  <nav>
    <RouterLink to="/list">Duties List</RouterLink>
    <RouterLink to="/gantt">Gantt View</RouterLink>
  </nav>
  <div style="padding: 15px">
    <div style="float: left; width: 78%">
      <RouterView />
    </div>
    <div
      style="
        margin: 15px;
        float: right;
        background: #ecebe5;
        width: 18%;
        height: 800px;
        border: 1px solid #006c66;
      "
    >
      <div
        style="
          background: #006c66;
          padding: 10px;
          color: white;
          margin-bottom: 8px;
          height: 42px;
        "
      >
        Filter
      </div>
      <div style="padding-top: 4px">
        <div style="padding-left: 8px; font-weight: bold">
          Responsible Person
        </div>
        <div style="padding-left: 30px">Rs</div>
      </div>
      <div style="padding-top: 4px">
        <div style="padding-left: 8px; font-weight: bold">Backup Person</div>
        <div style="padding-left: 30px">Rs</div>
      </div>
      <div style="padding-top: 4px">
        <div style="padding-left: 8px; font-weight: bold">Facility</div>
        <div style="padding-left: 30px">Rs</div>
      </div>
      <div style="padding-top: 4px">
        <div style="padding-left: 8px; font-weight: bold">Platform</div>
        <div style="padding-left: 30px">Rs</div>
      </div>
      <div style="padding-top: 4px">
        <div style="padding-left: 8px; font-weight: bold">Archived</div>
        <div style="padding-left: 30px">No</div>
        <div style="padding-left: 30px">Yes</div>
        <div style="padding-left: 30px">All</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  color: white;
  font-size: 20px;
  font-weight: bold;
  background: #006c66;
  padding: 16px 20px;
  max-height: 100vh;
}

nav {
  font-size: 14px;
  padding: 8px 4px;
  background: #ecebe5;
}

nav a.router-link-exact-active {
  color: #006c66;
  transition: 0.4s;
}

nav a {
  font-weight: bold;
  color: var(--color-text);
  text-decoration: none;
  display: inline-block;
  padding: 0 1rem;
  border-left: 2px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}
</style>
