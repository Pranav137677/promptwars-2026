/**
 * Blind Spot — Client-Side Application Logic
 * WCAG 2.1 AA Accessible, Non-Directive Reasoning Mirror
 * Zero External Framework Dependencies. Strictly XSS-Safe (textContent only).
 */

(function () {
  'use strict';

  // State Management
  const state = {
    decision: '',
    details: '',
    reasons: '',
    unsure: '',
    round1Analysis: null,
    authToken: null,
    user: null,
    firebaseConfig: null,
  };

  // DOM Elements Cache
  const elements = {
    // Theme
    themeToggle: document.getElementById('theme-toggle'),
    themeIcon: document.getElementById('theme-icon'),

    // Alerts
    errorBox: document.getElementById('error-box'),
    errorMessage: document.getElementById('error-message'),
    btnDismissError: document.getElementById('btn-dismiss-error'),
    statusBox: document.getElementById('status-box'),
    statusMessage: document.getElementById('status-message'),

    // Input Form & Controls
    inputSection: document.getElementById('input-section'),
    decisionForm: document.getElementById('decision-form'),
    decisionInput: document.getElementById('decision-input'),
    detailsInput: document.getElementById('details-input'),
    reasonsInput: document.getElementById('reasons-input'),
    unsureInput: document.getElementById('unsure-input'),
    btnInternshipExample: document.getElementById('btn-internship-example'),
    btnClearForm: document.getElementById('btn-clear-form'),
    btnSubmitRound1: document.getElementById('btn-submit-round1'),

    // Character Counters
    countDecision: document.getElementById('count-decision'),
    countDetails: document.getElementById('count-details'),
    countReasons: document.getElementById('count-reasons'),
    countUnsure: document.getElementById('count-unsure'),
    countTotal: document.getElementById('count-total'),

    // Loading State
    loadingState: document.getElementById('loading-state'),
    loadingText: document.getElementById('loading-text'),

    // Results Section
    resultsSection: document.getElementById('results-section'),
    resultsHeading: document.getElementById('results-heading'),
    btnCopySummary: document.getElementById('btn-copy-summary'),
    btnStartOver: document.getElementById('btn-start-over'),
    listTakeaways: document.getElementById('list-takeaways'),
    summaryText: document.getElementById('summary-text'),
    factorGrid: document.getElementById('factor-grid'),
    listConsidered: document.getElementById('list-considered'),
    listAssumptions: document.getElementById('list-assumptions'),
    listOverlooked: document.getElementById('list-overlooked'),
    listConflicts: document.getElementById('list-conflicts'),
    listRisks: document.getElementById('list-risks'),
    perspectiveText: document.getElementById('perspective-text'),
    perspectiveAheadText: document.getElementById('perspective-ahead-text'),
    perspectiveBackText: document.getElementById('perspective-back-text'),
    footerModelName: document.getElementById('footer-model-name'),


    // Round 2
    round2Section: document.getElementById('round2-section'),
    reflectionForm: document.getElementById('reflection-form'),
    probingQuestionsContainer: document.getElementById('probing-questions-container'),
    btnSubmitRound2: document.getElementById('btn-submit-round2'),
    round2Results: document.getElementById('round2-results'),
    listAnswersReveal: document.getElementById('list-answers-reveal'),
    listAnswersTensions: document.getElementById('list-answers-tensions'),
    listAnswersBlindspots: document.getElementById('list-answers-blindspots'),
    listAnswersPrompts: document.getElementById('list-answers-prompts'),

    // Auth & History
    authArea: document.getElementById('auth-area'),
    btnLogin: document.getElementById('btn-login'),
    userProfile: document.getElementById('user-profile'),
    userEmail: document.getElementById('user-email'),
    btnHistory: document.getElementById('btn-history'),
    btnLogout: document.getElementById('btn-logout'),
    historyModal: document.getElementById('history-modal'),
    historyList: document.getElementById('history-list'),
    btnCloseHistory: document.getElementById('btn-close-history'),
  };

  // Official Example Fixture
  const INTERNSHIP_EXAMPLE = {
    decision: "Whether to accept an offer for a 6-month software engineering internship",
    details: "Stipend: ₹25,000/month. Hours: 40 hours/week (Monday to Friday, 9am - 6pm). Location: In-person office, 45-minute commute each way. Role: Full-stack developer at a mid-stage tech startup. College context: Final year B.Tech, 75% attendance officially required, major capstone project due in 4 months.",
    reasons: "Good stipend to cover personal expenses and savings, office is relatively close to home, and gives valuable industry engineering experience to strengthen my resume before graduating.",
    unsure: "Unsure whether I can realistically maintain required college attendance and finish the capstone project on time while working full-time 40-hour weeks."
  };

  // =========================================================
  // Theme Management
  // =========================================================
  function initTheme() {
    const savedTheme = localStorage.getItem('blindspot_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    applyTheme(initialTheme);

    elements.themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      applyTheme(newTheme);
      localStorage.setItem('blindspot_theme', newTheme);
    });
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
      elements.themeIcon.textContent = '🌙';
      elements.themeToggle.setAttribute('aria-label', 'Switch to dark theme');
    } else {
      document.documentElement.removeAttribute('data-theme');
      elements.themeIcon.textContent = '☀️';
      elements.themeToggle.setAttribute('aria-label', 'Switch to light theme');
    }
  }

  // =========================================================
  // Alert & Notification Utilities
  // =========================================================
  function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorBox.style.display = 'flex';
    elements.errorBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function clearError() {
    elements.errorMessage.textContent = '';
    elements.errorBox.style.display = 'none';
  }

  function showStatus(message, durationMs = 4000) {
    elements.statusMessage.textContent = message;
    elements.statusBox.style.display = 'flex';
    if (durationMs > 0) {
      setTimeout(() => {
        elements.statusBox.style.display = 'none';
        elements.statusMessage.textContent = '';
      }, durationMs);
    }
  }

  // =========================================================
  // Character Counting & Validation
  // =========================================================
  function updateCounters() {
    const decLen = elements.decisionInput.value.length;
    const detLen = elements.detailsInput.value.length;
    const reaLen = elements.reasonsInput.value.length;
    const unsLen = elements.unsureInput.value.length;
    const total = decLen + detLen + reaLen + unsLen;

    updateCounterElement(elements.countDecision, decLen, 2000);
    updateCounterElement(elements.countDetails, detLen, 2000);
    updateCounterElement(elements.countReasons, reaLen, 2000);
    updateCounterElement(elements.countUnsure, unsLen, 2000);

    elements.countTotal.textContent = `${total} / 4000`;
    if (total > 4000) {
      elements.countTotal.classList.add('over-limit');
      elements.btnSubmitRound1.disabled = true;
    } else {
      elements.countTotal.classList.remove('over-limit');
      elements.btnSubmitRound1.disabled = false;
    }
  }

  function updateCounterElement(el, current, max) {
    el.textContent = `${current} / ${max}`;
    if (current > max) {
      el.className = 'char-count over-limit';
    } else if (current > max * 0.9) {
      el.className = 'char-count near-limit';
    } else {
      el.className = 'char-count';
    }
  }

  function fillInternshipExample() {
    clearError();
    elements.decisionInput.value = INTERNSHIP_EXAMPLE.decision;
    elements.detailsInput.value = INTERNSHIP_EXAMPLE.details;
    elements.reasonsInput.value = INTERNSHIP_EXAMPLE.reasons;
    elements.unsureInput.value = INTERNSHIP_EXAMPLE.unsure;
    updateCounters();
    elements.decisionInput.focus();
    showStatus("Filled form with the student internship scenario.");
  }

  function clearForm() {
    elements.decisionInput.value = '';
    elements.detailsInput.value = '';
    elements.reasonsInput.value = '';
    elements.unsureInput.value = '';
    updateCounters();
    clearError();
    elements.decisionInput.focus();
  }

  // =========================================================
  // Safe DOM Node Builders (Strictly XSS Prevention)
  // =========================================================
  function createTextElement(tag, text, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text || '';
    return el;
  }

  function populateSimpleList(ulElement, items) {
    ulElement.replaceChildren();
    if (!items || items.length === 0) {
      const li = createTextElement('li', 'None noted.', 'text-subtle');
      ulElement.appendChild(li);
      return;
    }
    items.forEach(text => {
      const li = createTextElement('li', text);
      ulElement.appendChild(li);
    });
  }

  function renderFactorGrid(coverageItems) {
    elements.factorGrid.replaceChildren();
    if (!coverageItems || coverageItems.length === 0) return;

    coverageItems.forEach(item => {
      const badge = document.createElement('div');
      const statusClass = `status-${item.status}`;
      badge.className = `factor-badge ${statusClass}`;
      badge.setAttribute('role', 'listitem');

      const nameEl = createTextElement('span', item.category, 'factor-name');

      const statusRow = document.createElement('div');
      statusRow.className = 'factor-status-row';

      let icon = '○';
      let label = 'Not Mentioned';
      if (item.status === 'covered') {
        icon = '✓';
        label = 'Covered';
      } else if (item.status === 'partly') {
        icon = '◐';
        label = 'Partly Covered';
      }

      const iconEl = createTextElement('span', icon, 'factor-status-icon');
      iconEl.setAttribute('aria-hidden', 'true');
      const labelEl = createTextElement('span', label, 'factor-status-label');

      statusRow.appendChild(iconEl);
      statusRow.appendChild(labelEl);
      badge.appendChild(nameEl);
      badge.appendChild(statusRow);

      elements.factorGrid.appendChild(badge);
    });
  }

  function renderComplexList(ulElement, items, renderFn) {
    ulElement.replaceChildren();
    if (!items || items.length === 0) {
      const li = createTextElement('li', 'None identified.', 'text-subtle');
      ulElement.appendChild(li);
      return;
    }
    items.forEach(item => {
      const li = document.createElement('li');
      li.appendChild(renderFn(item));
      ulElement.appendChild(li);
    });
  }

  // =========================================================
  // Round 1 Submission & Render
  // =========================================================
  async function submitRound1(e) {
    e.preventDefault();
    clearError();

    const decision = elements.decisionInput.value.trim();
    const details = elements.detailsInput.value.trim();
    const reasons = elements.reasonsInput.value.trim();
    const unsure = elements.unsureInput.value.trim();

    if (decision.length < 3) {
      showError("Please describe the decision you are considering (at least 3 characters).");
      elements.decisionInput.focus();
      return;
    }
    if (reasons.length < 3) {
      showError("Please state the main reasons you are leaning this way (at least 3 characters).");
      elements.reasonsInput.focus();
      return;
    }

    const totalLen = decision.length + details.length + reasons.length + unsure.length;
    if (totalLen > 4000) {
      showError(`Total length (${totalLen} chars) exceeds 4000 characters.`);
      return;
    }

    state.decision = decision;
    state.details = details;
    state.reasons = reasons;
    state.unsure = unsure;

    setLoading(true, "Analyzing your decision context for unstated assumptions and blind spots...");

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (state.authToken) {
        headers['Authorization'] = `Bearer ${state.authToken}`;
      }

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ decision, details, reasons, unsure }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Server returned an error during analysis.');
      }

      state.round1Analysis = data.analysis;
      renderRound1Results(data.analysis);
      setLoading(false);

      // Accessibility: Move focus to the results heading
      elements.resultsSection.style.display = 'block';
      elements.resultsHeading.focus();
    } catch (err) {
      setLoading(false);
      showError(err.message || 'Unable to complete analysis. Please try again.');
    }
  }

  function renderRound1Results(analysis) {
    // Key Takeaways (3 bullets)
    if (analysis.key_takeaways && Array.isArray(analysis.key_takeaways) && elements.listTakeaways) {
      populateSimpleList(elements.listTakeaways, analysis.key_takeaways);
    }

    // Summary
    elements.summaryText.textContent = analysis.summary || '';

    // Factor Coverage
    renderFactorGrid(analysis.factor_coverage || []);

    // What You Covered Well
    populateSimpleList(elements.listConsidered, analysis.what_you_considered);

    // Unstated Assumptions
    renderComplexList(elements.listAssumptions, analysis.unstated_assumptions, item => {
      const wrap = document.createElement('div');
      wrap.className = 'complex-item';
      wrap.appendChild(createTextElement('div', item.assumption, 'complex-main'));
      wrap.appendChild(createTextElement('div', `Test question: ${item.question_to_test_it}`, 'complex-sub'));
      return wrap;
    });

    // Overlooked Factors
    renderComplexList(elements.listOverlooked, analysis.overlooked_factors, item => {
      const wrap = document.createElement('div');
      wrap.className = 'complex-item';
      wrap.appendChild(createTextElement('span', item.category, 'complex-meta'));
      wrap.appendChild(createTextElement('div', item.factor, 'complex-main'));
      wrap.appendChild(createTextElement('div', item.why_it_may_matter, 'complex-sub'));
      return wrap;
    });

    // Conflicts in Reasoning
    renderComplexList(elements.listConflicts, analysis.conflicts_in_reasoning, item => {
      const wrap = document.createElement('div');
      wrap.className = 'complex-item';
      wrap.appendChild(createTextElement('div', item.tension, 'complex-main'));
      wrap.appendChild(createTextElement('div', item.explanation, 'complex-sub'));
      return wrap;
    });

    // Risks and Unknowns
    renderComplexList(elements.listRisks, analysis.risks_and_unknowns, item => {
      const wrap = document.createElement('div');
      wrap.className = 'complex-item';
      wrap.appendChild(createTextElement('div', item.item, 'complex-main'));
      wrap.appendChild(createTextElement('div', item.why_it_matters, 'complex-sub'));
      return wrap;
    });

    // Balanced Perspectives (One Steelman for EACH side)
    if (analysis.another_perspective && typeof analysis.another_perspective === 'object') {
      if (elements.perspectiveAheadText) {
        elements.perspectiveAheadText.textContent = analysis.another_perspective.perspective_favouring_going_ahead || '';
      }
      if (elements.perspectiveBackText) {
        elements.perspectiveBackText.textContent = analysis.another_perspective.perspective_favouring_holding_back || '';
      }
      if (elements.perspectiveText) {
        elements.perspectiveText.style.display = 'none';
      }
    } else if (typeof analysis.another_perspective === 'string') {
      if (elements.perspectiveText) {
        elements.perspectiveText.textContent = analysis.another_perspective;
        elements.perspectiveText.style.display = 'block';
      }
    }

    // Probing Questions (Round 2 Prep)
    renderProbingQuestions(analysis.probing_questions || []);
  }

  function renderProbingQuestions(questions) {
    elements.probingQuestionsContainer.replaceChildren();
    elements.round2Results.style.display = 'none';

    if (!questions || questions.length === 0) {
      elements.probingQuestionsContainer.appendChild(
        createTextElement('p', 'No probing questions generated.', 'text-muted')
      );
      return;
    }

    questions.forEach((q, idx) => {
      const card = document.createElement('div');
      card.className = 'question-card';

      const qLabel = createTextElement('label', `${idx + 1}. ${q}`, 'question-text');
      qLabel.setAttribute('for', `q-answer-${idx}`);

      const textarea = document.createElement('textarea');
      textarea.id = `q-answer-${idx}`;
      textarea.className = 'form-control';
      textarea.rows = 2;
      textarea.maxLength = 1500;
      textarea.placeholder = 'Your reflection or response to this question...';
      textarea.dataset.questionText = q;

      card.appendChild(qLabel);
      card.appendChild(textarea);
      elements.probingQuestionsContainer.appendChild(card);
    });
  }

  // =========================================================
  // Round 2 Reflection Submission & Render
  // =========================================================
  async function submitRound2(e) {
    e.preventDefault();
    clearError();

    const textareas = elements.probingQuestionsContainer.querySelectorAll('textarea');
    const answers = [];

    textareas.forEach(ta => {
      const ans = ta.value.trim();
      if (ans) {
        answers.push({
          question: ta.dataset.questionText,
          answer: ans,
        });
      }
    });

    if (answers.length === 0) {
      showError("Please answer at least one probing question to deepen your reflection.");
      const firstTa = textareas[0];
      if (firstTa) firstTa.focus();
      return;
    }

    const btnText = elements.btnSubmitRound2.querySelector('.btn-text');
    const spinner = elements.btnSubmitRound2.querySelector('.spinner');
    elements.btnSubmitRound2.disabled = true;
    btnText.textContent = 'Reflecting...';
    spinner.style.display = 'inline-block';

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (state.authToken) {
        headers['Authorization'] = `Bearer ${state.authToken}`;
      }

      const response = await fetch('/api/reflect', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          decision: state.decision,
          summary: state.round1Analysis ? state.round1Analysis.summary : '',
          answers: answers,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Server error during reflection.');
      }

      renderRound2Results(data.reflection);
      elements.round2Results.style.display = 'block';
      elements.round2Results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      showError(err.message || 'Unable to process reflection.');
    } finally {
      elements.btnSubmitRound2.disabled = false;
      btnText.textContent = 'Reflect on Answers';
      spinner.style.display = 'none';
    }
  }

  function renderRound2Results(reflection) {
    populateSimpleList(elements.listAnswersReveal, reflection.what_your_answers_reveal);
    populateSimpleList(elements.listAnswersTensions, reflection.tensions_or_contradictions);
    populateSimpleList(elements.listAnswersBlindspots, reflection.remaining_blind_spots);
    populateSimpleList(elements.listAnswersPrompts, reflection.reflection_prompts);
  }

  // =========================================================
  // Loading & Action Handlers
  // =========================================================
  function setLoading(isLoading, text = "Analyzing...") {
    if (isLoading) {
      elements.loadingText.textContent = text;
      elements.loadingState.style.display = 'flex';
      elements.btnSubmitRound1.disabled = true;
      elements.btnSubmitRound1.querySelector('.btn-text').textContent = 'Analyzing...';
      elements.btnSubmitRound1.querySelector('.spinner').style.display = 'inline-block';
      elements.loadingState.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      elements.loadingState.style.display = 'none';
      elements.btnSubmitRound1.disabled = false;
      elements.btnSubmitRound1.querySelector('.btn-text').textContent = 'Analyze Blind Spots';
      elements.btnSubmitRound1.querySelector('.spinner').style.display = 'none';
    }
  }

  function copySummaryToClipboard() {
    if (!state.round1Analysis) return;

    const a = state.round1Analysis;
    let md = `# Blind Spot Analysis: ${state.decision}\n\n`;

    if (a.key_takeaways && Array.isArray(a.key_takeaways) && a.key_takeaways.length > 0) {
      md += `## Key Takeaways\n`;
      a.key_takeaways.forEach(k => { md += `- ${k}\n`; });
      md += `\n`;
    }

    md += `## Objective Summary\n${a.summary}\n\n`;

    md += `## Factor Coverage\n`;
    (a.factor_coverage || []).forEach(f => {
      md += `- ${f.category}: ${f.status.toUpperCase()}\n`;
    });
    md += `\n`;

    md += `## What You Considered Well\n`;
    (a.what_you_considered || []).forEach(c => { md += `- ${c}\n`; });
    md += `\n`;

    md += `## Unstated Assumptions\n`;
    (a.unstated_assumptions || []).forEach(u => {
      md += `- Assumption: ${u.assumption}\n  Test: ${u.question_to_test_it}\n`;
    });
    md += `\n`;

    md += `## Overlooked Factors\n`;
    (a.overlooked_factors || []).forEach(o => {
      md += `- [${o.category}] ${o.factor}: ${o.why_it_may_matter}\n`;
    });
    md += `\n`;

    md += `## Reasoning Conflicts\n`;
    (a.conflicts_in_reasoning || []).forEach(cf => {
      md += `- ${cf.tension}: ${cf.explanation}\n`;
    });
    md += `\n`;

    md += `## Risks & Unknowns\n`;
    (a.risks_and_unknowns || []).forEach(r => {
      md += `- ${r.item}: ${r.why_it_matters}\n`;
    });
    md += `\n`;

    md += `## Alternative Perspectives\n`;
    if (a.another_perspective && typeof a.another_perspective === 'object') {
      md += `### A Perspective Favouring Going Ahead\n${a.another_perspective.perspective_favouring_going_ahead || ''}\n\n`;
      md += `### A Perspective Favouring Holding Back\n${a.another_perspective.perspective_favouring_holding_back || ''}\n\n`;
    } else {
      md += `${a.another_perspective || ''}\n\n`;
    }
    md += `---\nGenerated by Blind Spot — Non-directive AI Reasoning Mirror\n`;

    navigator.clipboard.writeText(md).then(() => {
      showStatus("Analysis summary copied to clipboard in markdown format!");
    }).catch(() => {
      showError("Could not automatically copy to clipboard. Please copy manually.");
    });
  }

  function startOver() {
    clearForm();
    elements.resultsSection.style.display = 'none';
    state.round1Analysis = null;
    elements.decisionInput.focus();
    showStatus("Ready for your next decision context.");
  }

  // =========================================================
  // Optional Firebase Auth & History
  // =========================================================
  async function initAuth() {
    try {
      const res = await fetch('/config');
      if (!res.ok) return;
      const cfg = await res.json();
      state.firebaseConfig = cfg;

      if (cfg.model && elements.footerModelName) {
        elements.footerModelName.textContent = cfg.model;
      }

      if (!cfg.enabled || !cfg.apiKey) {
        return; // Firebase is disabled, app works fully anonymously
      }

      // Load Firebase SDK via official Google CDN
      await loadScript('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
      await loadScript('https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js');

      window.firebase.initializeApp({
        apiKey: cfg.apiKey,
        authDomain: cfg.authDomain,
        projectId: cfg.projectId,
      });

      const auth = window.firebase.auth();

      auth.onAuthStateChanged(async user => {
        if (user) {
          state.user = user;
          state.authToken = await user.getIdToken();
          elements.btnLogin.style.display = 'none';
          elements.userProfile.style.display = 'flex';
          elements.userEmail.textContent = user.email || 'User';
        } else {
          state.user = null;
          state.authToken = null;
          elements.btnLogin.style.display = 'inline-block';
          elements.userProfile.style.display = 'none';
        }
      });

      elements.btnLogin.addEventListener('click', () => {
        const provider = new window.firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider).catch(err => {
          showError(`Sign-in failed: ${err.message}`);
        });
      });

      elements.btnLogout.addEventListener('click', () => {
        auth.signOut();
      });

      elements.btnHistory.addEventListener('click', openHistoryModal);
      elements.btnCloseHistory.addEventListener('click', () => {
        elements.historyModal.style.display = 'none';
      });
    } catch (err) {
      console.warn("Firebase Auth initialization skipped:", err);
    }
  }

  async function openHistoryModal() {
    if (!state.authToken) return;
    elements.historyList.replaceChildren();
    elements.historyList.appendChild(createTextElement('p', 'Loading reflections...', 'text-muted'));
    elements.historyModal.style.display = 'flex';

    try {
      const res = await fetch('/api/history', {
        headers: { 'Authorization': `Bearer ${state.authToken}` }
      });
      const data = await res.json();
      elements.historyList.replaceChildren();

      if (!data.reflections || data.reflections.length === 0) {
        elements.historyList.appendChild(createTextElement('p', 'No saved reflections found.', 'text-muted'));
        return;
      }

      data.reflections.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-item';

        const head = document.createElement('div');
        head.className = 'history-header';

        const title = createTextElement('span', item.decision, 'history-title');
        const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString() : '';
        const dateEl = createTextElement('span', dateStr, 'history-date');
        head.appendChild(title);
        head.appendChild(dateEl);

        const summary = createTextElement('p', item.summary, 'complex-sub');

        const actRow = document.createElement('div');
        actRow.className = 'history-actions';

        const btnLoad = createTextElement('button', 'View in Mirror', 'btn btn-secondary btn-sm');
        btnLoad.type = 'button';
        btnLoad.addEventListener('click', () => {
          elements.historyModal.style.display = 'none';
          if (item.round1) {
            state.decision = item.decision;
            state.round1Analysis = item.round1;
            renderRound1Results(item.round1);
            elements.resultsSection.style.display = 'block';
            elements.resultsHeading.focus();
          }
        });

        const btnDel = createTextElement('button', 'Delete', 'btn btn-outline btn-sm');
        btnDel.type = 'button';
        btnDel.addEventListener('click', async () => {
          if (confirm('Delete this saved reflection?')) {
            await fetch(`/api/history/${item.id}`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${state.authToken}` }
            });
            card.remove();
          }
        });

        actRow.appendChild(btnLoad);
        actRow.appendChild(btnDel);

        card.appendChild(head);
        card.appendChild(summary);
        card.appendChild(actRow);
        elements.historyList.appendChild(card);
      });
    } catch (err) {
      elements.historyList.replaceChildren();
      elements.historyList.appendChild(createTextElement('p', 'Failed to load history.', 'text-danger'));
    }
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  // =========================================================
  // Initialization & Event Binding
  // =========================================================
  function init() {
    initTheme();

    // Input listeners for char counts
    [
      elements.decisionInput,
      elements.detailsInput,
      elements.reasonsInput,
      elements.unsureInput
    ].forEach(input => {
      input.addEventListener('input', updateCounters);
    });

    // Buttons
    elements.btnInternshipExample.addEventListener('click', fillInternshipExample);
    elements.btnClearForm.addEventListener('click', clearForm);
    elements.btnDismissError.addEventListener('click', clearError);
    elements.decisionForm.addEventListener('submit', submitRound1);
    elements.reflectionForm.addEventListener('submit', submitRound2);
    elements.btnCopySummary.addEventListener('click', copySummaryToClipboard);
    elements.btnStartOver.addEventListener('click', startOver);

    // Initial counter setup
    updateCounters();

    // Initialize Optional Firebase Auth
    initAuth();
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
