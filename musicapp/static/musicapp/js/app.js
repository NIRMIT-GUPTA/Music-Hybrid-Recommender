/* jQuery drives the small single-page interactions. */
$(function () {
  // Authentication pages use the same base template but do not need app data.
  if (!$('#song-search').length) return;
  const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
  const escapeHtml = value => $('<div>').text(value ?? '').html();
  let timer;

  $.ajaxSetup({ beforeSend: xhr => xhr.setRequestHeader('X-CSRFToken', csrf()) });
  function message(text, type = 'danger') { $('#message').html(text ? `<div class="alert alert-${type} py-2 mb-0">${escapeHtml(text)}</div>` : ''); }
  function currentMode() { return $('input[name=mode]:checked').val(); }
  function loadGenres() { $.getJSON('/api/genres/', data => $('#genre-select').html('<option value="">Select a genre…</option>' + data.genres.map(g => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join(''))); }
  function loginPrompt() { return 'Log in to save your personal recommendations.'; }
  function loadFavourites() { $.getJSON('/api/favourites/', data => $('#favourites').html(data.requires_login ? loginPrompt() : (data.favourites.length ? data.favourites.map(x => `<div class="favourite-item border-bottom py-2" data-track="${escapeHtml(x.track_id)}"><strong>${escapeHtml(x.track_name)}</strong><br><span class="text-secondary">${escapeHtml(x.artists)} · ${escapeHtml(x.track_genre)}</span></div>`).join('') : 'No saved favourites yet.'))); }
  function loadHistory() { $.getJSON('/api/history/', data => $('#history').html(data.requires_login ? loginPrompt() : (data.history.length ? data.history.map(x => `<button class="history-item btn btn-sm btn-outline-secondary w-100 text-start mb-2" data-mode="${x.mode}" data-track="${escapeHtml(x.track_id || '')}" data-genre="${escapeHtml(x.genre || '')}">${escapeHtml(x.mode === 'song' ? '♫ ' : '⌁ ')}${escapeHtml(x.query_label)}</button>`).join('') : 'No recent searches yet.'))); }
  function showResults(results) { $('#results').html(results.map(x => `<tr><td>${escapeHtml(x.track_name)}</td><td>${escapeHtml(x.artists)}</td><td>${escapeHtml(x.track_genre)}</td><td>${escapeHtml(x.popularity)}</td><td>${Number(x.content_score).toFixed(3)}</td><td>${Number(x.collaborative_score).toFixed(3)}</td><td class="fw-bold">${Number(x.hybrid_score).toFixed(3)}</td><td><button class="btn btn-sm btn-outline-danger result-heart" data-track="${escapeHtml(x.track_id)}" title="Toggle favourite">♡</button></td></tr>`).join('')); }
  function runRecommendation(saved) {
    const mode = saved?.mode || currentMode(); const trackId = saved?.track_id || $('#selected-track-id').val(); const genre = saved?.genre || $('#genre-select').val();
    if ((mode === 'song' && !trackId) || (mode === 'genre' && !genre)) return message(`Please select a ${mode === 'song' ? 'song from the suggestions' : 'genre'}.`);
    $('#recommend-button').prop('disabled', true).find('.spinner-border').removeClass('d-none'); message('');
    $.ajax({ url: '/api/recommend/', method: 'POST', contentType: 'application/json', data: JSON.stringify({ mode, track_id: trackId, genre, alpha: Number($('#alpha').val()) }) }).done(data => { showResults(data.results); loadHistory(); }).fail(xhr => message(xhr.responseJSON?.error || 'Could not create recommendations.')).always(() => $('#recommend-button').prop('disabled', false).find('.spinner-border').addClass('d-none'));
  }
  $('input[name=mode]').change(function () { const song = this.value === 'song'; $('#song-input').toggleClass('d-none', !song); $('#genre-input').toggleClass('d-none', song); $('#alpha').val(song ? .6 : .5).trigger('input'); message(''); });
  $('#alpha').on('input', function () { $('#alpha-value').text(this.value); });
  $('#song-search').on('input', function () {
    const query = this.value.trim();
    $('#selected-track-id').val('');
    clearTimeout(timer);
    if (query.length < 2) return $('#suggestions').empty();
    timer = setTimeout(() => {
      $.getJSON('/api/search/', { q: query }, data => {
        $('#suggestions').html(data.tracks.map(x => `<button type="button" class="list-group-item list-group-item-action" data-id="${escapeHtml(x.track_id)}" data-name="${escapeHtml(x.track_name)}">${escapeHtml(x.track_name)} <small class="text-secondary">— ${escapeHtml(x.artists)} · ${escapeHtml(x.track_genre)}</small></button>`).join(''));
      });
    }, 300);
  });
  $('#suggestions').on('click', 'button', function () { $('#selected-track-id').val($(this).data('id')); $('#song-search').val($(this).data('name')); $('#suggestions').empty(); });
  $('#recommend-button').click(() => runRecommendation());
  $('#results').on('click', '.result-heart', function () { const button = $(this); $.ajax({ url: '/api/favourites/toggle/', method: 'POST', contentType: 'application/json', data: JSON.stringify({ track_id: button.data('track') }) }).done(data => { button.text(data.favourited ? '♥' : '♡'); loadFavourites(); }).fail(xhr => { if (xhr.status === 401) window.location.href = '/accounts/login/?next=/'; else message(xhr.responseJSON?.error || 'Could not save favourite.'); }); });
  $('#history').on('click', '.history-item', function () { const item = $(this); $(`input[name=mode][value=${item.data('mode')}]`).prop('checked', true).trigger('change'); runRecommendation({ mode: item.data('mode'), track_id: item.data('track'), genre: item.data('genre') }); });
  $('#favourites').on('click', '.favourite-item', function () { $('#song-mode').prop('checked', true).trigger('change'); $('#selected-track-id').val($(this).data('track')); runRecommendation(); });
  loadGenres(); loadFavourites(); loadHistory();
});
