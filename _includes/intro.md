
*New:* latest [blog posts](#blogs) and [high-frequency impact monitoring](#features).
{: .newfeatures :}

Data is critical to support countries in managing the global coronavirus (COVID-19) pandemic.
This site was introduced in the early stages of the pandemic to provide
an array of relevant real-time data, statistical indicators, and knowledge
drawn from the World Bank and other authoritative sources.

Please see the World Bank's [COVID-19 page][wb-covid] for the latest efforts
to monitor and address the crisis and transition to recovery.


<div id="dg-dashboard">
{% if page.under_construction %}
<p class="construction">{{ page.under_construction }}</p>
{% else %}
<iframe src="{{ page.dash_url }}"></iframe>
<p><a target="_new" href="{{ page.dash_url }}">Click here</a> to access the dashboard in a separate window.</p>
{% endif %}
</div>

*Sources: [Johns Hopkins University Center for Systems Science and Engineering][jhu1] via [Github][jhu2]; [World Development Indicators][wb1]*

[wb-covid]: https://www.worldbank.org/en/who-we-are/news/coronavirus-covid19
[jhu1]: https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6
[jhu2]: https://github.com/CSSEGISandData/2019-nCoV
[wb1]: https://data.worldbank.org
