
Data is critical to support countries in managing the global coronavirus (COVID-19) pandemic.
This site provides an array of real-time data, statistical indicators, and other
types of data that are relevant to the coronavirus pandemic. These data are 
drawn from the World Bank's data catalog and other authoritative sources.

This page will be updated frequently as more data
and research becomes available, particularly on the economic and social impacts of the
pandemic and the [World Bank's efforts to address them][wb-covid].

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
