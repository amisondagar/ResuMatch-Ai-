/**
 * static/js/charts.js — Plotly Chart Renderer
 * ResumeMatch.ai
 *
 * Renders the single unified Analytics Dashboard charts.
 * Supports interactive chart clicks that navigate to candidate summary pages.
 */

document.addEventListener('DOMContentLoaded', () => {
  const isDark    = document.documentElement.getAttribute('data-theme') !== 'light';
  const bgColor   = 'rgba(0,0,0,0)';
  const textColor = isDark ? '#94a3b8' : '#334155';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(99,102,241,0.1)';

  const baseLayout = {
    paper_bgcolor: bgColor,
    plot_bgcolor:  bgColor,
    font: { family: 'Inter, sans-serif', color: textColor, size: 12 },
    margin: { t: 20, r: 20, b: 50, l: 50 },
    showlegend: false,
  };

  const config = { responsive: true, displayModeBar: false };

  function readData(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch { return null; }
  }

  // ── 1. Candidate ATS Score Ranking Bar Chart (Sorted High -> Low) ──────
  const candScoresEl = document.getElementById('chartCandidateScores');
  if (candScoresEl) {
    const d = readData('dataCandidateScores');
    if (d && d.names && d.names.length) {
      // Color bars based on score threshold
      const barColors = d.scores.map(s => s >= 70 ? '#34d399' : s >= 40 ? '#fbbf24' : '#f87171');

      Plotly.newPlot(candScoresEl, [{
        type: 'bar',
        x: d.names,
        y: d.scores,
        marker: { color: barColors, borderRadius: 4 },
        text: d.scores.map(s => s + '%'),
        textposition: 'auto',
        hovertemplate: '<b>%{x}</b><br>ATS Score: %{y}%<br><i>Click to view candidate card</i><extra></extra>',
      }], {
        ...baseLayout,
        margin: { t: 20, r: 20, b: 80, l: 50 },
        xaxis: { gridcolor: gridColor, tickfont: { color: textColor, size: 11 }, tickangle: -25 },
        yaxis: { gridcolor: gridColor, tickfont: { color: textColor }, range: [0, 100], title: { text: 'ATS Match %', font: { size: 11 } } },
      }, config);

      // Interactive Click: Navigate to Candidate Summary Detail page
      candScoresEl.on('plotly_click', (eventData) => {
        if (eventData && eventData.points && eventData.points[0]) {
          const idx = eventData.points[0].pointIndex;
          const candId = d.ids[idx];
          if (candId) {
            window.location.href = `/resume/${candId}`;
          }
        }
      });
    }
  }

  // ── 2. Skills Breakdown Bar Chart per Candidate ────────────────────────
  const skillsBreakdownEl = document.getElementById('chartSkillsBreakdown');
  if (skillsBreakdownEl) {
    const d = readData('dataSkillsBreakdown');
    if (d && d.names && d.names.length) {
      Plotly.newPlot(skillsBreakdownEl, [{
        type: 'bar',
        x: d.names,
        y: d.skill_scores,
        marker: { color: '#6366f1', opacity: 0.85 },
        text: d.skill_scores.map(s => Math.round(s) + '%'),
        textposition: 'auto',
        hovertemplate: '<b>%{x}</b><br>Skill Coverage: %{y}%<extra></extra>',
      }], {
        ...baseLayout,
        margin: { t: 10, r: 15, b: 70, l: 45 },
        xaxis: { gridcolor: gridColor, tickfont: { color: textColor, size: 10 }, tickangle: -25 },
        yaxis: { gridcolor: gridColor, tickfont: { color: textColor }, range: [0, 100] },
      }, config);

      skillsBreakdownEl.on('plotly_click', (eventData) => {
        if (eventData && eventData.points && eventData.points[0]) {
          const idx = eventData.points[0].pointIndex;
          const candId = d.ids[idx];
          if (candId) window.location.href = `/resume/${candId}`;
        }
      });
    }
  }

  // ── 3. Shortlisted vs Rejected vs Pending Donut Chart ──────────────────
  const statusDonutEl = document.getElementById('chartStatusDonut');
  if (statusDonutEl) {
    const d = readData('dataStatusDonut');
    if (d && d.labels && d.labels.length) {
      Plotly.newPlot(statusDonutEl, [{
        type: 'pie',
        labels: d.labels,
        values: d.values,
        hole: 0.6,
        marker: { colors: ['#34d399', '#f87171', '#fbbf24'] },
        textinfo: 'label+value',
        textfont: { color: textColor, size: 12 },
        hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Ratio: %{percent}<extra></extra>',
      }], {
        ...baseLayout,
        showlegend: true,
        legend: { font: { color: textColor }, orientation: 'h', y: -0.1 },
      }, config);
    }
  }

  // ── 4. Certifications & Top Skills Talent Pool Overview ────────────────
  const talentPoolEl = document.getElementById('chartTalentPool');
  if (talentPoolEl) {
    const d = readData('dataTalentPool');
    if (d && d.items && d.items.length) {
      Plotly.newPlot(talentPoolEl, [{
        type: 'bar',
        x: d.counts,
        y: d.items,
        orientation: 'h',
        marker: { color: '#06b6d4', opacity: 0.85 },
        text: d.counts,
        textposition: 'auto',
        hovertemplate: '<b>%{y}</b><br>Candidates Count: %{x}<extra></extra>',
      }], {
        ...baseLayout,
        margin: { t: 10, r: 20, b: 30, l: 140 },
        xaxis: { gridcolor: gridColor, tickfont: { color: textColor } },
        yaxis: { tickfont: { color: textColor, size: 11 }, autorange: 'reversed' },
      }, config);
    }
  }
});
