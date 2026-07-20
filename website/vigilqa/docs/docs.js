var NAV = [
  {
    section: 'Getting Started',
    pages: [
      { title: 'Overview', href: '/vigilqa/docs/getting-started/overview.html' },
      { title: 'Quick Start', href: '/vigilqa/docs/getting-started/quick-start.html' },
      { title: 'System Requirements', href: '/vigilqa/docs/getting-started/system-requirements.html' },
      { title: 'Trial & Onboarding', href: '/vigilqa/docs/getting-started/trial-onboarding.html' },
      { title: 'Deployment', href: '/vigilqa/docs/getting-started/deployment.html' }
    ]
  },
  {
    section: 'Core Concepts',
    pages: [
      { title: 'Knowledge Base', href: '/vigilqa/docs/core-concepts/knowledge-base.html' },
      { title: 'Generation Pipeline', href: '/vigilqa/docs/core-concepts/generation-pipeline.html' },
      { title: 'Post-Run Agents', href: '/vigilqa/docs/core-concepts/post-run-agents.html' },
      { title: 'Approvals', href: '/vigilqa/docs/core-concepts/approvals.html' }
    ]
  },
  {
    section: 'Modules',
    pages: [
      { title: 'Overview', href: '/vigilqa/docs/modules/index.html' },
      { title: 'REST / GraphQL API', href: '/vigilqa/docs/modules/rest-graphql-api.html' },
      { title: 'Web UI Testing', href: '/vigilqa/docs/modules/web-ui.html' },
      { title: 'API Contract', href: '/vigilqa/docs/modules/api-contract.html' },
      { title: 'Visual Regression', href: '/vigilqa/docs/modules/visual-regression.html' },
      { title: 'Accessibility', href: '/vigilqa/docs/modules/accessibility.html' },
      { title: 'Security & VAPT', href: '/vigilqa/docs/modules/security-vapt.html' },
      { title: 'Performance', href: '/vigilqa/docs/modules/performance.html' },
      { title: 'AI Agent Testing', href: '/vigilqa/docs/modules/ai-agent-testing.html' },
      { title: 'Model Evals', href: '/vigilqa/docs/modules/model-evals.html' },
      { title: 'Bug Tracker', href: '/vigilqa/docs/modules/bug-tracker.html' }
    ]
  },
  {
    section: 'Agents',
    pages: [
      { title: 'Overview', href: '/vigilqa/docs/agents/index.html' },
      { title: 'ResultAnalyzer', href: '/vigilqa/docs/agents/result-analyzer.html' },
      { title: 'FlakyDetector', href: '/vigilqa/docs/agents/flaky-detector.html' },
      { title: 'RegressionGuard', href: '/vigilqa/docs/agents/regression-guard.html' },
      { title: 'CoverageGap', href: '/vigilqa/docs/agents/coverage-gap.html' },
      { title: 'LocatorHealer', href: '/vigilqa/docs/agents/locator-healer.html' },
      { title: 'Generation Agents', href: '/vigilqa/docs/agents/generation-agents.html' }
    ]
  },
  {
    section: 'Platform',
    pages: [
      { title: 'Test Plans', href: '/vigilqa/docs/platform/test-plans.html' },
      { title: 'Test Runs', href: '/vigilqa/docs/platform/test-runs.html' },
      { title: 'Requirements & Traceability', href: '/vigilqa/docs/platform/traceability.html' },
      { title: 'Release Readiness', href: '/vigilqa/docs/platform/release-readiness.html' },
      { title: 'Agent Activities', href: '/vigilqa/docs/platform/agent-activities.html' },
      { title: 'Approvals', href: '/vigilqa/docs/platform/approvals.html' },
      { title: 'Team & Roles', href: '/vigilqa/docs/platform/team-roles.html' },
      { title: 'Notifications', href: '/vigilqa/docs/platform/notifications.html' },
      { title: 'Test Tools Support', href: '/vigilqa/docs/platform/test-tools.html' },
      { title: 'Integrations', href: '/vigilqa/docs/platform/integrations.html' }
    ]
  },
  {
    section: 'CI/CD Integration',
    pages: [
      { title: 'GitHub Actions', href: '/vigilqa/docs/ci-cd/github-actions.html' },
      { title: 'GitLab CI', href: '/vigilqa/docs/ci-cd/gitlab-ci.html' },
      { title: 'Jenkins & Other', href: '/vigilqa/docs/ci-cd/jenkins.html' }
    ]
  },
  {
    section: 'Configuration',
    pages: [
      { title: 'Config Reference', href: '/vigilqa/docs/configuration/config-reference.html' },
      { title: 'Environments', href: '/vigilqa/docs/configuration/environments.html' },
      { title: 'LLM Configuration', href: '/vigilqa/docs/configuration/llm-configuration.html' },
      { title: 'Quality Bands', href: '/vigilqa/docs/configuration/quality-thresholds.html' },
      { title: 'Service Registry', href: '/vigilqa/docs/configuration/service-registry.html' }
    ]
  },
  {
    section: 'Troubleshooting',
    pages: [
      { title: 'Common Issues', href: '/vigilqa/docs/troubleshooting/index.html' }
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
    + '<a href="/vigilqa/docs/" class="flex items-center gap-2 group">'
    + '<div class="w-7 h-7 bg-indigo-600 rounded-md flex items-center justify-center">'
    + '<svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    + '</div>'
    + '<div><div class="font-semibold text-slate-900 text-sm leading-tight">VigilQA</div>'
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
        || (page.href === '/vigilqa/docs/modules/index.html' && current === '/vigilqa/docs/modules/')
        || (page.href === '/vigilqa/docs/agents/index.html' && current === '/vigilqa/docs/agents/')
        || (page.href === '/vigilqa/docs/troubleshooting/index.html' && current === '/vigilqa/docs/troubleshooting/');
      html += '<li><a href="' + page.href + '" class="sidebar-link flex items-center px-2 py-1.5 text-sm rounded-md text-slate-600'
        + (isActive ? ' active' : '') + '">' + page.title + '</a></li>';
    }
    html += '</ul></div>';
  }
  html += '</nav>'
    + '<div class="px-5 py-4 border-t border-slate-200 mt-2">'
    + '<a href="/vigilqa/" class="text-xs text-slate-400 hover:text-indigo-600">← Back to VigilQA</a>'
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
        el.innerHTML = '<a href="/vigilqa/docs/" class="hover:text-indigo-600 transition-colors">Docs</a>'
          + '<span class="mx-1.5">›</span>'
          + '<span class="hover:text-indigo-600">' + group.section + '</span>'
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
    html += '<a href="' + prev.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors min-w-0 max-w-[45%]">'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-indigo-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + prev.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-indigo-700 truncate">' + prev.page.title + '</div></div></a>';
  } else {
    html += '<div></div>';
  }
  if (next) {
    html += '<a href="' + next.page.href + '" class="group flex items-center gap-3 p-4 rounded-lg border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors min-w-0 max-w-[45%] text-right ml-auto">'
      + '<div class="min-w-0"><div class="text-xs text-slate-400 mb-0.5">' + next.section + '</div>'
      + '<div class="text-sm font-medium text-slate-700 group-hover:text-indigo-700 truncate">' + next.page.title + '</div></div>'
      + '<svg class="w-4 h-4 text-slate-400 group-hover:text-indigo-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></a>';
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
