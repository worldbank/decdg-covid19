
$(document).ready(function() {

  url = 'http://cvapi.zognet.net/covid-projects.json';

  $.get(url, function(data) {

    var projects = [];

    prj = data['projects'];
    total = 0;
    for( var id in prj) {
        prj_amount = prj[id]['totalamt'];
        projects.push({
          'id': id,
          'name': prj[id]['project_name'],
          'amount': prj_amount,
          'country': prj[id]['countryshortname'],
          'status': prj[id]['status'],
          'updated': prj[id]['p2a_updated_date'].split(' ')[0].replace(/-/g, '&#8209;')});

        total += parseInt(prj_amount.replace(/,/g, ''));
    }

    projects.sort(function(a,b) { return (a['updated'] > b['updated']) ? -1 : 1 });
    for( var p in projects) {
        $row = $('<tr/>');
        $a = $('<a/>').text(projects[p]['name']).attr('href', 'https://projects.worldbank.org/en/projects-operations/project-detail/' + projects[p]['id']);;
        $row.append($('<td/>').html($a));
        $row.append($('<td/>').text(projects[p]['status']));
        $row.append($('<td/>').text(projects[p]['country']));
        $row.append($('<td/>').text(projects[p]['amount']));
        $row.append($('<td/>').html(projects[p]['updated']));

        $('#covid-projects').append($row);
    }

    // see https://blog.abelotech.com/posts/number-currency-formatting-javascript/
    total = total.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');

    $row = $('<tr/>').addClass('summary');
    $row.append($('<td/>').text('Total (' + projects.length + ' projects)'));
    $row.append($('<td/>'));
    $row.append($('<td/>'));
    $row.append($('<td/>').text(total));
    $row.append($('<td/>'));

    $('#covid-projects').append($row);
  });
});
