import API_BASE from './config';

const handleResponse = async (res) => {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

// ── WORDS ──────────────────────────────────────────────

export const getAllWords = async () => {
  const res = await fetch(`${API_BASE}/words`);
  return handleResponse(res);
};

export const searchWords = async (query) => {
  const res = await fetch(`${API_BASE}/words/search?q=${encodeURIComponent(query)}`);
  return handleResponse(res);
};

export const getWordSenses = async (word) => {
  const res = await fetch(`${API_BASE}/words/${encodeURIComponent(word)}/senses`);
  return handleResponse(res);
};

// ── CHALLENGES ─────────────────────────────────────────

export const getChallengesByWord = async (word) => {
  const res = await fetch(`${API_BASE}/challenges/${encodeURIComponent(word)}`);
  return handleResponse(res);
};

export const getChallengeBySense = async (word, senseId) => {
  const res = await fetch(
    `${API_BASE}/challenges/${encodeURIComponent(word)}/${senseId}`
  );
  return handleResponse(res);
};

// ── SEMANTIC GRAPH ──────────────────────────────────────

export const getSemanticGraph = async (word) => {
  const res = await fetch(`${API_BASE}/graph/${encodeURIComponent(word)}`);
  return handleResponse(res);
};

// ── SESSIONS ───────────────────────────────────────────

export const recordAttempt = async (userId, word, senseId, isCorrect) => {
  const res = await fetch(`${API_BASE}/sessions/attempt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      word,
      sense_id: senseId,
      correct: isCorrect,
    }),
  });
  return handleResponse(res);
};

export const getSessionStats = async (userId) => {
  const res = await fetch(`${API_BASE}/sessions/${userId}/stats`);
  return handleResponse(res);
};

export const getWeakspots = async (userId) => {
  const res = await fetch(`${API_BASE}/sessions/${userId}/weakspots`);
  return handleResponse(res);
};

// ── VOICE SEARCH HELPER ────────────────────────────────

export const searchByTransliteration = async (spokenText) => {
  const translitMap = {
    'padi': 'படி', 'aaru': 'ஆறு', 'kal': 'கல்',
    'thingal': 'திங்கள்', 'malai': 'மாலை', 'kalai': 'கலை',
    'kan': 'கண்', 'mann': 'மண்', 'pen': 'பெண்',
    'pal': 'பல்', 'sol': 'சொல்', 'vil': 'வில்',
  };
  const mapped = translitMap[spokenText.toLowerCase()] || spokenText;
  return searchWords(mapped);
};
