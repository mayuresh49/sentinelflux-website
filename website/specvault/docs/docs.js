var NAV = [
  {
    section: 'Getting Started',
    pages: [
      { title: 'Overview', href: '/specvault/docs/getting-started/overview.html' },
      { title: 'Quick Start', href: '/specvault/docs/getting-started/quick-start.html' },
      { title: 'Deployment', href: '/specvault/docs/getting-started/deployment.html' },
      { title: 'System Requirements', href: '/specvault/docs/getting-started/system-requirements.html' }
    ]
  },
  {
    section: 'Core Concepts',
    pages: [
      { title: 'Services', href: '/specvault/docs/core-concepts/services.html' },
      { title: 'Spec Versions', href: '/specvault/docs/core-concepts/spec-versions.html' },
      { title: 'Breaking Changes', href: '/specvault/docs/core-concepts/breaking-changes.html' },
      { title: 'Subscriptions & Alerts', href: '/specvault/docs/core-concepts/subscriptions.html' }
    ]
  },
  {
    section: 'Platform',
    pages: [
      { title: 'Dashboard', href: '/specvault/docs/platform/dashboard.html' },
      { title: 'Notifications', href: '/specvault/docs/platform/notifications.html' },
      { title: 'API Tokens', href: '/specvault/docs/platform/api-tokens.html' },
      { title: 'Audit Log', href: '/specvault/docs/platform/audit-log.html' }
    ]
  },
  {
    section: 'CI/CD Integration',
    pages: [
      { title: 'GitHub Actions', href: '/specvault/docs/ci-cd/github-actions.html' },
      { title: 'GitLab CI', href: '/specvault/docs/ci-cd/gitlab-ci.html' },
      { title: 'Other Pipelines', href: '/specvault/docs/ci-cd/other-pipelines.html' }
    ]
  },
  {
    section: 'Troubleshooting',
    pages: [
      { title: 'Common Issues', href: '/specvault/docs/troubleshooting/index.html' }
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
    + '<a href="/specvault/docs/" class="flex items-center gap-2 group">'
    + '<div class="w-7 h-7 bg-violet-600 rounded-md flex items-center justify-center">'
    + '<svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"/></svg>'
    + '</div>'
    + '<div><div class="font-semibold text-slate-900 text-sm leading-tight">SpecVault</div>'
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
        || (page.href === '/specvault/docs/troubleshooting/index.html' && current === '/specvault/docs/troubleshooting/');
      html += '<li><a href="' + page.href + '" class="sidebar-link flex items-center px-2 py-1.5 text-sm rounded-md text-slate-600'
        + (isActive ? ' active' : '') + '">' + page.title + '</a></li>';
    }
    html += '</ul></div>';
  }
  html += '</nav>'
    + '<div class="px-5 py-4 border-t border-slate-200 mt-2">'
    + '<a href="/specvault/" class="text-xs text-slate-400 hover:text-violet-600">← Back to SpecVault</a>'
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
        el.innerHTML = '<a href="/specvault/docs/" class="hover:text-violet-600 transition-colors">Docs</a>'
          + '<span class="mx-1.5">›</span>'
          + '<span class="hover:text-violet-600">' + group.section + '</span>'
          + '<span class="mx-1.5">›</span>'
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
    html += '<a href="' + prev.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-violet-300 hover:bg-violet-50 transition-colors min-w-0 max-w-[45%]">'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-violet-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + prev.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-violet-700 truncate">' + prev.page.title + '</div></div></a>';
  } else {
    html += '<div></div>';
  }
  if (next) {
    html += '<a href="' + next.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-violet-300 hover:bg-violet-50 transition-colors min-w-0 max-w-[45%] text-right ml-auto">'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + next.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-violet-700 truncate">' + next.page.title + '</div></div>'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-violet-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></a>';
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
