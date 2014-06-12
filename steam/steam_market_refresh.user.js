// ==UserScript==
// @name        Steam Community Market Refresh Button
// @namespace   DarkStarSword
// @include     http://steamcommunity.com/market/listings/*
// @version     1
// @grant       none
// ==/UserScript==

document.getElementById('market_buynow_dialog_accept_ssa').checked = true;

//refresh_url = 'javascript:s=g_oSearchResults;s.m_iCurrentPage=1;s.GoToPage(0)'
// refresh_url = 'javascript:document.getElementsByClassName("market_listing_right_cell market_listing_action_buttons")[0].innerHTML="Refreshing...";s=g_oSearchResults;s.m_iCurrentPage=1;s.GoToPage(0)';
refresh_url = 'javascript:document.getElementById("searchResultsTable").scrollIntoView(true); document.getElementsByClassName("market_listing_right_cell market_listing_action_buttons")[0].innerHTML="Refreshing...";s=g_oSearchResults;s.m_iCurrentPage=1;s.GoToPage(0); jQuery.noop()';

elem_new = document.createElement('a');
elem_new.href = refresh_url;
elem_new.appendChild(document.createTextNode('REFRESH!!!'));

elem_div = document.createElement('div');
elem_div.align = 'right';
elem_div.appendChild(elem_new);

elem_after = document.getElementById('searchResultsRows');
elem_after.parentNode.insertBefore(elem_div, elem_after);

elem_div.scrollIntoView(true); // someone scrolls after us :(