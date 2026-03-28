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
  const res = await fetch(`${API_BASE}/api/words`);
  const data = await handleResponse(res);
  const words = Array.isArray(data)
    ? data.map(item => (typeof item === 'string' ? item : item.word)).filter(Boolean)
    : [];
  return { words };
};

export const searchWords = async (query) => {
  const all = await getAllWords();
  const q = (query || '').trim().toLowerCase();
  if (!q) return { words: all.words };
  return { words: all.words.filter(w => String(w).toLowerCase().includes(q)) };
};

export const getWordSenses = async (word) => {
  const res = await fetch(`${API_BASE}/api/word/${encodeURIComponent(word)}/senses`);
  return handleResponse(res);
};

// ── CHALLENGES ─────────────────────────────────────────

export const getChallengesByWord = async (word) => {
  const res = await fetch(`${API_BASE}/api/challenge/${encodeURIComponent(word)}`);
  const challenge = await handleResponse(res);
  return [challenge];
};

export const getRandomChallenge = async () => {
  const res = await fetch(`${API_BASE}/api/random-challenge`);
  return handleResponse(res);
};

export const getChallengeBySense = async (word, senseId) => {
  const res = await fetch(`${API_BASE}/api/challenge/${encodeURIComponent(word)}`);
  const challenge = await handleResponse(res);
  if (String(challenge.sense_id) === String(senseId)) {
    return challenge;
  }
  return challenge;
};

// ── SEMANTIC GRAPH ──────────────────────────────────────

export const getSemanticGraph = async (word) => {
  const res = await fetch(`${API_BASE}/api/graph/${encodeURIComponent(word)}`);
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
      sense_id: String(senseId),
      correct: Boolean(isCorrect),
    }),
  });
  return handleResponse(res);
};

export const getSessionStats = async (userId) => {
  return {
    user_id: userId,
    total_attempts: 0,
    correct_attempts: 0,
    accuracy: 0,
    streak: 0,
  };
};

export const getWeakspots = async (userId) => {
  return { user_id: userId, weakspots: [] };
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
