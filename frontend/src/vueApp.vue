<template>
  <AppShell v-if="!isEmbedded" />
  <router-view v-else></router-view>
</template>
<script>
import AppShell from "./components/AppShell.vue";

export default {
  name: "VueApp",
  components: {
    AppShell
  },
  data() {
    return {
      // While the ExtJS main-hub shell still exists, every page keeps
      // loading here inside its <iframe> wrappers -- in that case the
      // ExtJS shell already provides the header/nav, so render only the
      // bare route. AppShell (with its own header/nav) only renders when
      // this app is the top-level page, e.g. reached directly at /vue/.
      isEmbedded: window.self !== window.top
    };
  }
};
</script>
<style></style>
