
<div class="container col-container" style="padding-bottom: 30px">
<h2>Resources</h2>
<div class="row">

{% assign boxes = 'box-left.md,box-middle.md,box-right.md' | split: ',' %}
{% for box in boxes %}
<div class="col-sm-4 lp__card lp__card_wrapper">
<div class="lp__card_content" markdown=1>
{% include {{ box }} %}
</div>
</div>
{% endfor %}

</div>
</div>
