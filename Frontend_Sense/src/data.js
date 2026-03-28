// Converted from data.ts to data.js (JavaScript, no types)
// All type annotations and imports removed

// If you need runtime validation, use PropTypes or JSDoc.

export const MOCK_USER = {
  name: "Selvan",
  tamilName: "செல்வன்",
  level: 12,
  xp: 2500,
  streak: 5,
  accuracy: 94,
  days: 15,
  avatar: "https://picsum.photos/seed/linguist/200/200"
};

export const WORD_MASTERY = [
  { word: "படி", transliteration: "Padi", percentage: 100, color: 'primary' },
  { word: "ஆறு", transliteration: "Aaru", percentage: 85, color: 'primary' },
  { word: "கல்", transliteration: "Kal", percentage: 60, color: 'secondary' }
];

export const RECENT_ACTIVITY = [
  { id: '1', type: 'game', title: 'Solved word game', detail: 'padi', time: '2 hours ago', xp: 15 },
  { id: '2', type: 'badge', title: 'Earned Weekly Badge', detail: 'Polyglot', time: 'Yesterday' }
];

export const FEATURED_LESSON = {
  id: 'padi-masterclass',
  title: 'The Geometry of "Padi"',
  description: 'Explore 4 distinct meanings: To read, a step, a measure, and a command to settle.',
  duration: '12 MINS',
  word: 'படி',
  type: 'Master Class'
};

export const QUESTIONS = [
  {
    id: '1',
    sentenceBefore: 'அமைதியாக ஓடும்',
    sentenceAfter: 'மீனவர்கள் மீன் பிடிப்பதற்காக வலைகளை வீசினர்.',
    options: ['ஆற்றில்', 'ஏறினார்', 'அளக்கிறார்', 'படிந்தார்'],
    correctIndex: 0,
    explanation: 'Fishermen cast nets to catch fish in the quietly flowing river (ஆற்றில்).'
  },
  {
    id: '2',
    sentenceBefore: 'நாளை தேர்வு நடைபெற உள்ளதால் அந்த மாணவன் மிகவும் கவனமாக பாடம்',
    sentenceAfter: '.',
    options: ['படிக்கிறான்', 'ஆடுகிறான்', 'ஓடுகிறான்', 'பாடுகிறான்'],
    correctIndex: 0,
    explanation: 'Since the exam is tomorrow, the student is studying (படிக்கிறான்) very carefully.'
  },
  {
    id: '3',
    sentenceBefore: 'மதிய உணவிற்காக சமையலறையில் அம்மா கொதிக்கும் உலையில் அரிசி',
    sentenceAfter: '.',
    options: ['போட்டார்', 'எடுத்தார்', 'கழுவினார்', 'வடித்தார்'],
    correctIndex: 0,
    explanation: 'In the kitchen, mother put (போட்டார்) rice in the boiling pot for lunch.'
  }
];

export const WORD_DETAILS = {
  'படி': {
    word: 'படி',
    transliteration: 'padi',
    meaning: 'To read or study; a step; a measure.',
    exampleTamil: 'அவன் தேர்வுக்காகப் பாடம் படிக்கிறான்.',
    exampleEnglish: 'He is studying lessons for the exam.',
    morphology: [
      { label: 'PRESENT TENSE', value: 'படிக்கிறான்' },
      { label: 'PAST TENSE', value: 'படித்தான்' }
    ],
    frequency: 'High',
    reliance: 'Level 4 Essential'
  },
  'ஆறு': {
    word: 'ஆறு',
    transliteration: 'aaru',
    meaning: 'River; the number six; to cool down.',
    exampleTamil: 'காவிரி ஆறு தமிழ்நாட்டின் உயிர்நாடி.',
    exampleEnglish: 'The Kaveri river is the lifeline of Tamil Nadu.',
    morphology: [
      { label: 'NOUN', value: 'ஆறு' },
      { label: 'VERB (COOL)', value: 'ஆறுதல்' }
    ],
    frequency: 'High',
    reliance: 'Level 2 Essential'
  }
};
