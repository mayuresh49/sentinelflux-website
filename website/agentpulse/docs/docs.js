var NAV = [
  {
    section: 'Getting Started',
    pages: [
      { title: 'Overview', href: '/agentpulse/docs/getting-started/overview.html' },
      { title: 'Quick Start', href: '/agentpulse/docs/getting-started/quick-start.html' },
      { title: 'Plans & Limits', href: '/agentpulse/docs/getting-started/plans.html' }
    ]
  },
  {
    section: 'Core Concepts',
    pages: [
      { title: 'Products & Agents', href: '/agentpulse/docs/core-concepts/products-agents.html' },
      { title: 'Execution Traces', href: '/agentpulse/docs/core-concepts/execution-traces.html' },
      { title: 'Alert Rules', href: '/agentpulse/docs/core-concepts/alert-rules.html' },
      { title: 'Cost by Product', href: '/agentpulse/docs/core-concepts/cost-by-product.html' }
    ]
  },
  {
    section: 'API Reference',
    pages: [
      { title: 'Ingestion API', href: '/agentpulse/docs/api/ingestion-api.html' }
    ]
  },
  {
    section: 'Platform',
    pages: [
      { title: 'Notifications', href: '/agentpulse/docs/platform/notifications.html' }
    ]
  },
  {
    section: 'Troubleshooting',
    pages: [
      { title: 'Common Issues', href: '/agentpulse/docs/troubleshooting/index.html' }
    ]
  }
];

function getCurrentPath() {
  var p = window.location.pathname;
  if (p.endsWith('/')) p = p + 'index.html';
  return p;
}

function buildSidebar() {
  var current = getCurrentPath();
  var html = '<div class="px-5 py-4 border-b border-slate-200">'
    + '<a href="/agentpulse/docs/" class="flex items-center gap-2 group">'
    + '<div class="w-7 h-7 bg-emerald-600 rounded-md flex items-center justify-center">'
    + '<svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>'
    + '</div>'
    + '<div><div class="font-semibold text-slate-900 text-sm leading-tight">AgentPulse</div>'
    + '<div class="text-xs text-slate-400 leading-tight">Documentation</div></div>'
    + '</a></div>'
    + '<nav class="px-3 py-4 space-y-5">';
  for (var i = 0; i < NAV.length; i++) {
    var group = NAV[i];
    html += '<div>'
      + '<p class="px-2 mb-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">' + group.section + '</p>'
      + '<ul class="space-y-0.5">';
    for (var j = 0; j < group.pages.length; j++) {
      var page = group.pages[j];
      var isActive = current === page.href
        || current === page.href.replace('.html', '')
        || (page.href === '/agentpulse/docs/troubleshooting/index.html' && current === '/agentpulse/docs/troubleshooting/');
      html += '<li><a href="' + page.href + '" class="sidebar-link flex items-center px-2 py-1.5 text-sm rounded-md text-slate-600'
        + (isActive ? ' active' : '') + '">' + page.title + '</a></li>';
    }
    html += '</ul></div>';
  }
  html += '</nav>'
    + '<div class="px-5 py-4 border-t border-slate-200 mt-2">'
    + '<a href="/agentpulse/" class="text-xs text-slate-400 hover:text-emerald-600">← Back to AgentPulse</a>'
    + '</div>';
  var el = document.getElementById('sidebar');
  if (el) el.innerHTML = html;
}

function buildBreadcrumb() {
  var current = getCurrentPath();
  var el = document.getElementById('breadcrumb');
  if (!el) return;
  for (var i = 0; i < NAV.length; i++) {
    var group = NAV[i];
    for (var j = 0; j < group.pages.length; j++) {
      var page = group.pages[j];
      if (current === page.href || current === page.href.replace('.html', '')) {
        el.innerHTML = '<a href="/agentpulse/docs/" class="hover:text-emerald-600 transition-colors">Docs</a>'
          + '<span class="mx-1.5">\u203a</span>'
          + '<span class="hover:text-emerald-600">' + group.section + '</span>'
          + '<span class="mx-1.5">\u203a</span>'
          + '<span class="text-slate-700 font-medium">' + page.title + '</span>';
        return;
      }
    }
  }
}

function buildPrevNext() {
  var current = getCurrentPath();
  var el = document.getElementById('prev-next');
  if (!el) return;
  var allPages = [];
  for (var i = 0; i < NAV.length; i++) {
    for (var j = 0; j < NAV[i].pages.length; j++) {
      allPages.push({ page: NAV[i].pages[j], section: NAV[i].section });
    }
  }
  var idx = -1;
  for (var k = 0; k < allPages.length; k++) {
    if (current === allPages[k].page.href || current === allPages[k].page.href.replace('.html', '')) {
      idx = k; break;
    }
  }
  if (idx === -1) return;
  var prev = idx > 0 ? allPages[idx - 1] : null;
  var next = idx < allPages.length - 1 ? allPages[idx + 1] : null;
  var html = '<div class="flex w-full justify-between">';
  if (prev) {
    html += '<a href="' + prev.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50 transition-colors min-w-0 max-w-[45%]">'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + prev.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-emerald-700 truncate">' + prev.page.title + '</div></div></a>';
  } else { html += '<div></div>'; }
  if (next) {
    html += '<a href="' + next.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50 transition-colors min-w-0 max-w-[45%] text-right ml-auto">'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + next.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-emerald-700 truncate">' + next.page.title + '</div></div>'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></a>';
  }
  html += '</div>';
  el.innerHTML = html;
}

function initMobileMenu() {
  var btn = document.getElementById('menu-btn');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('overlay');
  if (!btn) return;
  btn.addEventListener('click', function () {
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
  });
  if (overlay) {
    overlay.addEventListener('click', function () {
      sidebar.classList.add('-translate-x-full');
      overlay.classList.add('hidden');
    });
  }
}

window.addEventListener('DOMContentLoaded', function () {
  buildSidebar();
  buildBreadcrumb();
  buildPrevNext();
  initMobileMenu();
});
