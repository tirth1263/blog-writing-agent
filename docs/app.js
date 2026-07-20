const state = { files: [], sourceText: '', profile: null, article: null, library: JSON.parse(localStorage.getItem('inkprint-library') || '[]') };
const $ = (id) => document.getElementById(id);

const sampleText = `The best systems do not ask people to become machines. They make room for better human decisions.

Think about the last workflow that frustrated your team. Was the problem really a lack of effort, or was the next step simply unclear? Most of the time, friction hides in the handoff: a missing owner, an assumption no one wrote down, or a signal that arrives too late to help.

A useful fix starts small. Map one repeated task. Name the moment where context disappears. Then change one thing and watch what happens. For example, a two-minute decision note can prevent an hour of backtracking next week.

Clarity compounds. When the work becomes easier to understand, it becomes easier to improve—and that is where sustainable progress begins.`;

function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 2200); }
function escapeHtml(text) { const d = document.createElement('div'); d.textContent = text; return d.innerHTML; }
function wordCount(text) { return (text.match(/\b[\w’'-]+\b/g) || []).length; }
function slug(text) { return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 70) || 'article'; }
function titleCase(text) { return text.replace(/\b\w/g, c => c.toUpperCase()); }

async function extractFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (['txt', 'md'].includes(ext)) return file.text();
  if (ext === 'docx') {
    if (!window.mammoth) throw new Error('DOCX reader is still loading. Try again in a moment.');
    return (await window.mammoth.extractRawText({ arrayBuffer: await file.arrayBuffer() })).value;
  }
  if (ext === 'pdf') {
    if (!window.pdfjsLib) throw new Error('PDF reader is still loading. Try again in a moment.');
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    const pdf = await window.pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
    const pages = [];
    for (let i = 1; i <= pdf.numPages; i++) pages.push((await (await pdf.getPage(i)).getTextContent()).items.map(x => x.str).join(' '));
    return pages.join('\n\n');
  }
  throw new Error(`${file.name} is not a supported file.`);
}

function renderFiles() {
  $('fileList').innerHTML = state.files.map(f => `<div class="file-item"><b>✓</b>${escapeHtml(f.name)} · ${(f.size / 1024).toFixed(0)} KB</div>`).join('');
  $('analyzeButton').disabled = !state.files.length;
}

async function analyzeFiles(useSample = false) {
  $('analyzeButton').disabled = true; $('analyzeButton').textContent = 'Reading your rhythm…';
  try {
    const texts = useSample ? [sampleText] : await Promise.all(state.files.map(extractFile));
    state.sourceText = texts.join('\n\n');
    if (wordCount(state.sourceText) < 25) throw new Error('Add a writing sample with at least 25 readable words.');
    state.profile = analyzeStyle(state.sourceText);
    renderProfile(); toast('Your style fingerprint is ready');
  } catch (error) { toast(error.message); }
  finally { $('analyzeButton').disabled = !state.files.length; $('analyzeButton').textContent = '✦ Analyze writing style'; }
}

function analyzeStyle(text) {
  const words = (text.match(/\b[A-Za-z][A-Za-z’'-]*\b/g) || []); const lower = words.map(w => w.toLowerCase());
  const sentences = text.split(/(?<=[.!?])\s+/).filter(s => s.trim().split(/\s+/).length > 2);
  const paragraphs = text.split(/\n\s*\n/).filter(Boolean); const avg = words.length / Math.max(sentences.length, 1);
  const contractions = lower.filter(w => w.includes("'") || w.includes('’')).length; const second = lower.filter(w => ['you','your','yours'].includes(w)).length;
  const first = lower.filter(w => ['i','we','my','our','us'].includes(w)).length; const questions = (text.match(/\?/g) || []).length;
  const formal = lower.filter(w => ['therefore','however','moreover','consequently','furthermore'].includes(w)).length;
  const longRatio = lower.filter(w => w.length >= 9).length / Math.max(words.length, 1); const unique = new Set(lower).size / Math.max(words.length, 1);
  const tone = contractions + (text.match(/!/g) || []).length > Math.max(words.length / 90, 2) ? 'Warm and conversational, with an energetic edge' : formal > 2 || avg > 23 ? 'Polished and analytical, with a measured professional tone' : 'Clear and approachable, balancing confidence with friendliness';
  const voice = second > first * 1.3 && second > 2 ? 'Reader-direct and coaching; frequently speaks to “you”' : first > second && first > 2 ? 'Personal and experience-led, using perspective to build trust' : 'Confident and explanatory, with a helpful point of view';
  const paraAvg = words.length / Math.max(paragraphs.length, 1); const structure = paraAvg < 55 ? 'Scannable, compact paragraphs with clear idea breaks' : paraAvg > 110 ? 'Long-form paragraphs that develop arguments in depth' : 'Moderate paragraphs moving from context to action to takeaway';
  const vocabulary = longRatio > .16 ? 'Advanced and domain-aware, with precise terminology' : unique > .48 ? 'Varied but accessible, favoring vivid language over jargon' : 'Plainspoken and accessible, prioritizing clarity';
  const syllables = words.reduce((n, w) => n + Math.max(1, (w.toLowerCase().match(/[aeiouy]+/g) || []).length - (/e$/.test(w) ? 1 : 0)), 0);
  const readability = Math.max(0, Math.min(100, 206.835 - 1.015 * avg - 84.6 * syllables / Math.max(words.length, 1)));
  const traits = []; if (questions > 1) traits.push('Uses questions to create momentum'); if (second > 3) traits.push('Speaks directly to the reader'); if (paraAvg < 80) traits.push('Keeps paragraphs scannable'); if (/for example|for instance|imagine|consider/i.test(text)) traits.push('Makes ideas concrete'); traits.push('Leads with clarity', 'Ends with a usable takeaway');
  return { tone, voice, structure, vocabulary, avg: avg.toFixed(1), readability: readability.toFixed(0), traits: [...new Set(traits)].slice(0, 5) };
}

function renderProfile() {
  const p = state.profile; $('emptyProfile').hidden = true; $('profile').hidden = false;
  $('statSentence').textContent = p.avg; $('statReadability').textContent = p.readability;
  $('toneValue').textContent = p.tone; $('voiceValue').textContent = p.voice; $('structureValue').textContent = p.structure; $('vocabularyValue').textContent = p.vocabulary;
  $('traits').innerHTML = p.traits.map(t => `<span>${escapeHtml(t)}</span>`).join('');
}

function smartTitle(topic) { const clean = topic.trim().replace(/[.?!]+$/, ''); return /^(how|why|what|when)\b/i.test(clean) ? clean[0].toUpperCase() + clean.slice(1) : `A Practical Guide to ${titleCase(clean)}`; }
function makeArticle(topic, audience, keywords, format, direction) {
  const clean = topic.trim().replace(/[.?!]+$/, ''); const title = smartTitle(clean); const keys = keywords.split(',').map(x => x.trim()).filter(Boolean).slice(0, 5);
  const subject = clean.replace(/^(how|why|what|when)\s+/i, '') || clean;
  const traits = state.profile?.traits?.slice(0, 2).map(x => x.toLowerCase()).join(' and ') || 'clear explanations and practical takeaways';
  const keywordLine = keys.length ? ` Along the way, we’ll connect the dots around ${keys.join(', ')}.` : '';
  const markdown = `# ${title}\n\n${clean[0].toUpperCase() + clean.slice(1)} can feel like one of those ideas everyone is discussing and few are turning into a durable practice. This ${format.toLowerCase()} makes it concrete. We’ll focus on ${traits}, so ${audience.toLowerCase()} can move from interest to a plan that works in the real world.${keywordLine}\n\n## Why ${clean} matters now\n\nThe conversation around ${clean} is moving from curiosity to consequence. The useful question is no longer whether it matters, but where it can create meaningful progress—and where thoughtful restraint still belongs.\n\n## Start with the problem, not the novelty\n\nA strong approach begins with a specific friction point. Before choosing a tool, trend, or tactic, write down what success should look like. Identify the people affected, the repeated task that needs improvement, and the signal that will tell you the change is working.\n\nImagine a team that jumps straight to a new solution. They may move quickly for a week, but without a shared outcome, every person is optimizing for something different. A ten-minute conversation about the actual problem would save hours of rework.\n\n## Turn the idea into a repeatable system\n\nSmall experiments beat sweeping transformations. Choose one workflow, establish a baseline, and run a short pilot. Keep the feedback loop visible: observe what happened, capture what surprised you, and adjust one variable at a time.\n\n1. **Define one outcome.** Make it observable and relevant.\n2. **Run a contained pilot.** Learn before you scale.\n3. **Review the evidence.** Include the people doing the work.\n4. **Document the pattern.** Make the next attempt easier than the first.\n\n## Keep human judgment in the loop\n\nThe best results rarely come from automation alone. They come from pairing consistent systems with context, taste, and accountability. Treat ${clean} as a collaborator in the process—not a substitute for the people who understand the audience, the risks, and the goal.\n\n## A practical next step\n\nPick one decision or workflow connected to ${clean} and spend 20 minutes mapping how it works today. Circle the slowest or least clear moment. That is your starting point—not a grand transformation, just one honest opportunity to make the work better.\n\nProgress becomes sustainable when the next move is small enough to begin and meaningful enough to measure. Start there, learn quickly, and let the evidence shape what comes next.${direction ? `\n\n> **Editorial direction:** ${direction}` : ''}`;
  const polishedMarkdown = markdown
    .replace(`## Why ${clean} matters now`, `## Why ${subject} matters now`)
    .replace(`The conversation around ${clean}`, `The conversation around ${subject}`)
    .replace(`Treat ${clean} as a collaborator`, `Treat ${subject} as a collaborator`)
    .replace(`connected to ${clean}`, `connected to ${subject}`);
  return { id: Date.now(), title, markdown: polishedMarkdown, words: wordCount(polishedMarkdown), created: new Date().toISOString() };
}

function markdownToHtml(md) {
  let list = false, html = '';
  md.split('\n').forEach(raw => { const line = raw.trim(); if (!line) { if (list) { html += '</ol>'; list = false; } return; }
    if (line.startsWith('# ')) html += `<h1>${escapeHtml(line.slice(2))}</h1>`;
    else if (line.startsWith('## ')) { if (list) { html += '</ol>'; list = false; } html += `<h2>${escapeHtml(line.slice(3))}</h2>`; }
    else if (/^\d+\.\s/.test(line)) { if (!list) { html += '<ol>'; list = true; } html += `<li>${escapeHtml(line.replace(/^\d+\.\s*/, '')).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</li>`; }
    else if (line.startsWith('> ')) html += `<blockquote>${escapeHtml(line.slice(2)).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</blockquote>`;
    else html += `<p>${escapeHtml(line).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</p>`;
  }); if (list) html += '</ol>'; return html;
}

function renderArticle() { $('emptyDraft').hidden = true; $('draft').hidden = false; $('wordCount').textContent = `${state.article.words} words`; $('articleContent').innerHTML = markdownToHtml(state.article.markdown); $('saveArticle').textContent = '＋ Save to library'; }
function saveLibrary() { localStorage.setItem('inkprint-library', JSON.stringify(state.library)); renderLibrary(); }
function renderLibrary() { $('libraryCount').textContent = state.library.length; $('libraryEmpty').hidden = state.library.length > 0; $('libraryGrid').innerHTML = state.library.map(a => `<article class="library-card"><h3>${escapeHtml(a.title)}</h3><p>${escapeHtml(a.markdown.split('\n\n').find(p => !p.startsWith('#')) || '').slice(0, 170)}…</p><small>${a.words} words · ${a.created.slice(0,10)}</small><div class="library-actions"><button data-open="${a.id}">Open draft</button><button data-delete="${a.id}">Delete</button></div></article>`).join(''); }
function switchTab(name) { document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.tab === name)); document.querySelectorAll('.panel').forEach(x => x.classList.remove('active')); $(`${name}Panel`).classList.add('active'); window.scrollTo({ top: 280, behavior: 'smooth' }); }

$('fileInput').addEventListener('change', e => { state.files = [...e.target.files]; renderFiles(); });
['dragenter','dragover'].forEach(evt => $('uploadZone').addEventListener(evt, e => { e.preventDefault(); $('uploadZone').classList.add('drag'); }));
['dragleave','drop'].forEach(evt => $('uploadZone').addEventListener(evt, e => { e.preventDefault(); $('uploadZone').classList.remove('drag'); }));
$('uploadZone').addEventListener('drop', e => { state.files = [...e.dataTransfer.files].filter(f => /\.(pdf|docx|txt|md)$/i.test(f.name)); renderFiles(); });
$('analyzeButton').addEventListener('click', () => analyzeFiles());
$('sampleButton').addEventListener('click', () => { state.files = [{ name: 'sample_article.txt', size: sampleText.length }]; renderFiles(); analyzeFiles(true); });
document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => { $('topic').value = button.dataset.prompt; $('topic').focus(); }));
$('writingForm').addEventListener('submit', e => { e.preventDefault(); state.article = makeArticle($('topic').value, $('audience').value || 'curious readers', $('keywords').value, $('format').value, $('direction').value); renderArticle(); toast('Your draft is ready'); });
$('topic').addEventListener('keydown', e => { if (e.ctrlKey && e.key === 'Enter') $('writingForm').requestSubmit(); });
$('copyArticle').addEventListener('click', async () => { await navigator.clipboard.writeText(state.article.markdown); toast('Markdown copied'); });
$('downloadArticle').addEventListener('click', () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([state.article.markdown], { type: 'text/markdown' })); a.download = `${slug(state.article.title)}.md`; a.click(); URL.revokeObjectURL(a.href); });
$('saveArticle').addEventListener('click', () => { if (!state.library.some(x => x.id === state.article.id)) state.library.unshift(state.article); saveLibrary(); $('saveArticle').textContent = 'Saved ✓'; toast('Saved to your private library'); });
$('editDraft').addEventListener('click', () => { const editable = $('articleContent').contentEditable !== 'true'; $('articleContent').contentEditable = editable; $('editDraft').textContent = editable ? 'Finish editing' : 'Edit draft'; if (editable) $('articleContent').focus(); });
$('libraryGrid').addEventListener('click', e => { const open = e.target.dataset.open, del = e.target.dataset.delete; if (open) { state.article = state.library.find(x => x.id == open); renderArticle(); switchTab('studio'); } if (del) { state.library = state.library.filter(x => x.id != del); saveLibrary(); toast('Draft removed'); } });
$('menuButton').addEventListener('click', () => { $('sidebar').classList.add('open'); $('overlay').classList.add('show'); });
function closeSide() { $('sidebar').classList.remove('open'); $('overlay').classList.remove('show'); }
$('closeSide').addEventListener('click', closeSide); $('overlay').addEventListener('click', closeSide);

renderLibrary();
