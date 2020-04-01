---
title: Projects List test page
disable_analytics: true
analyticsPageCategory: content page
banner: ""      # see example in config.yml
layout: test
scripts:
  - assets/js/covid-projects.js
---

This page builds a runtime table of projects data from a [projects API proxy](http://cvapi.zognet.net/covid-projects.json)
(since the canonical projects API does not support cross-site scripting).

<table id="covid-projects" class="table table-striped">
<thead>
<tr><th>Project</th><th>Status</th><th>Country</th><th>Amount ($)</th><th>Last Updated</th></tr>
</thead>
</table>

