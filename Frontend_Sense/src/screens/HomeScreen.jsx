import React, { useState, useEffect, useRef } from 'react';
import { Search, Mic, Flame, Sparkles, Cpu } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { MOCK_USER, FEATURED_LESSON } from '../data.js';
import { getAllWords, searchWords, getChallengesByWord } from '../api/mozhisense.js';

const HomeScreen = ({ setScreen, setSelectedWord, xp, streak }) => {
  const [search, setSearch] = useState('');
  const [words, setWords] = useState(['படி', 'ஆறு', 'கல்', 'திங்கள்', 'வாய்']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPreparingWord, setIsPreparingWord] = useState(false);
  const [showArchitectLoader, setShowArchitectLoader] = useState(false);
  const [loaderStep, setLoaderStep] = useState(0);
  const [isArchitectClosing, setIsArchitectClosing] = useState(false);
  const [showCancelButton, setShowCancelButton] = useState(false);
  const [prepError, setPrepError] = useState(null);
  const requestControllerRef = useRef(null);
  const requestCancelledRef = useRef(false);

  const ARCHITECT_STEPS = [
    'Searching WordNet...',
    'Consulting LLM...',
    'Applying Morphology Rules...',
    'Finalizing Challenge...'
  ];

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAllWords()
      .then(data => setWords(data.words || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);
  
  const beginWordFlow = async (rawWord) => {
    const word = String(rawWord || '').trim();
    if (!word) return;

    setPrepError(null);
    setIsPreparingWord(true);
    setLoaderStep(0);
    setShowCancelButton(false);
    setIsArchitectClosing(false);
    requestCancelledRef.current = false;

    const controller = new AbortController();
    requestControllerRef.current = controller;

    const delayedLoader = setTimeout(() => setShowArchitectLoader(true), 500);
    const stepCycler = setInterval(() => {
      setLoaderStep(prev => (prev + 1) % ARCHITECT_STEPS.length);
    }, 1100);
    const cancelRevealTimer = setTimeout(() => setShowCancelButton(true), 10000);

    try {
      await getChallengesByWord(word, { signal: controller.signal });
      if (requestCancelledRef.current) return;

      if (showArchitectLoader) {
        setIsArchitectClosing(true);
        await new Promise(resolve => setTimeout(resolve, 220));
      }

      setSelectedWord(word);
      setScreen('explore');
    } catch (err) {
      if (requestCancelledRef.current || err?.name === 'AbortError') {
        return;
      }

      const message = err?.message || 'Unable to prepare this word.';
      if (/generation failed|ollama|llm|connection|refused|timeout/i.test(message)) {
        setPrepError('Our AI is currently resting. Try one of our 451 pre-built challenges!');
      } else {
        setPrepError(message);
      }
    } finally {
      clearTimeout(delayedLoader);
      clearInterval(stepCycler);
      clearTimeout(cancelRevealTimer);
      setShowArchitectLoader(false);
      setIsPreparingWord(false);
      setShowCancelButton(false);
      setIsArchitectClosing(false);
      requestControllerRef.current = null;
    }
  };

  const handleCancelAndPlayRandom = () => {
    requestCancelledRef.current = true;
    if (requestControllerRef.current) {
      requestControllerRef.current.abort();
      requestControllerRef.current = null;
    }
    setIsPreparingWord(false);
    setShowArchitectLoader(false);
    setShowCancelButton(false);
    setIsArchitectClosing(false);
    setScreen('play');
  };

  const handleWordClick = (word) => {
    beginWordFlow(word);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) {
      beginWordFlow(search.trim());
    }
  };

  return (
    <div className="space-y-12 pb-12">
      <AnimatePresence>
        {showArchitectLoader && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-xl flex items-center justify-center px-6"
          >
            <motion.section
              initial={{ opacity: 0, y: 24, scale: 0.94 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: isArchitectClosing ? 0.92 : 1,
              }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={{ type: 'spring', stiffness: 220, damping: 18 }}
              className="w-full max-w-xl rounded-3xl border border-primary/30 bg-surface-container-high/60 backdrop-blur-xl p-8 shadow-[0_0_60px_rgba(250,204,21,0.12)]"
            >
              <div className="flex items-center justify-center mb-5">
                <motion.div
                  animate={{ scale: [1, 1.08, 1], opacity: [0.9, 1, 0.9] }}
                  transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
                  className="w-16 h-16 rounded-2xl bg-primary/15 border border-primary/30 flex items-center justify-center"
                >
                  <Cpu className="w-8 h-8 text-yellow-300" />
                </motion.div>
              </div>

              <div className="text-center mb-5">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-yellow-300" />
                  <p className="mono-text text-[10px] tracking-[0.3em] uppercase font-black text-yellow-300">AI Architect</p>
                </div>
                <p className="text-lg font-black text-text-main">Building your challenge for semantic exploration</p>
              </div>

              <AnimatePresence mode="wait">
                <motion.p
                  key={loaderStep}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="text-sm text-text-muted text-center mb-4"
                >
                  {ARCHITECT_STEPS[loaderStep]}
                </motion.p>
              </AnimatePresence>

              <div className="relative h-2 w-full rounded-full bg-surface-container overflow-hidden mb-5">
                <motion.div
                  initial={{ width: '0%' }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 5, ease: 'linear', repeat: Infinity }}
                  className="h-full rounded-full bg-gradient-to-r from-yellow-400/70 via-primary/80 to-yellow-300/70"
                />
                <motion.div
                  initial={{ x: '-100%' }}
                  animate={{ x: '220%' }}
                  transition={{ duration: 1.3, ease: 'linear', repeat: Infinity }}
                  className="absolute top-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                />
              </div>

              <div className="space-y-2">
                <div className="h-4 w-2/3 rounded-md bg-surface-container animate-pulse mx-auto" />
                <div className="h-10 w-full rounded-xl bg-surface-container animate-pulse" />
                <div className="grid grid-cols-2 gap-2">
                  <div className="h-9 rounded-lg bg-surface-container animate-pulse" />
                  <div className="h-9 rounded-lg bg-surface-container animate-pulse" />
                  <div className="h-9 rounded-lg bg-surface-container animate-pulse" />
                  <div className="h-9 rounded-lg bg-surface-container animate-pulse" />
                </div>
              </div>

              {showCancelButton && (
                <div className="pt-5 flex justify-center">
                  <button
                    onClick={handleCancelAndPlayRandom}
                    className="px-5 py-2.5 rounded-xl bg-rose-500/15 border border-rose-400/50 text-rose-200 mono-text text-[10px] font-black tracking-[0.2em] uppercase hover:bg-rose-500/25 transition-all"
                  >
                    Cancel & Play Random
                  </button>
                </div>
              )}
            </motion.section>
          </motion.div>
        )}
      </AnimatePresence>

      {prepError && (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="hardware-card border border-rose-500/40 bg-rose-950/20"
        >
          <p className="text-sm text-rose-200 mb-4">{prepError}</p>
          <button
            onClick={() => setScreen('play')}
            className="px-5 py-2.5 rounded-xl bg-text-main text-background mono-text text-[10px] font-black tracking-[0.25em] hover:bg-primary hover:text-on-primary transition-all"
          >
            TRY RANDOM CHALLENGE
          </button>
        </motion.section>
      )}

      <section className="space-y-3">
        <h2 className="tamil-text text-5xl font-black text-text-main leading-[1.1] tracking-tighter">
          வணக்கம், <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent font-bold">{MOCK_USER.name}</span>! 👋
        </h2>
        <p className="mono-text text-text-muted text-[10px] tracking-[0.4em] uppercase font-bold">The Art of Tamil Semantics</p>
      </section>

      <form onSubmit={handleSearch} className="relative group">
        <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none">
          <Search className="text-text-muted w-5 h-5 group-focus-within:text-primary transition-colors" />
        </div>
        <input 
          className="w-full bg-surface-container border border-outline-variant/10 rounded-2xl py-6 pl-16 pr-14 focus:ring-4 focus:ring-primary/5 focus:border-primary/30 text-text-main placeholder:text-text-muted/40 mono-text text-sm transition-all shadow-sm" 
          placeholder='Search root words...' 
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          disabled={isPreparingWord}
        />
        <div className="absolute inset-y-0 right-4 flex items-center">
          <button type="button" className="w-12 h-12 rounded-xl bg-primary/5 flex items-center justify-center text-primary hover:bg-primary/10 transition-all active:scale-95">
            <Mic className="w-5 h-5" />
          </button>
        </div>
      </form>

      <section className="flex flex-wrap gap-2">
        {words.map(word => (
          <button 
            key={word} 
            onClick={() => handleWordClick(word)}
            disabled={isPreparingWord}
            className="bg-surface-container-high px-5 py-2.5 rounded-xl font-[Noto_Sans_Tamil] text-lg text-text-main hover:text-primary hover:bg-primary/5 border border-outline-variant/5 transition-all cursor-pointer active:scale-95"
          >
            {word}
          </button>
        ))}
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="hardware-card flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
            <Flame className="w-20 h-20 text-primary" />
          </div>
          <div className="flex justify-between items-start">
            <span className="mono-text text-[10px] text-primary font-black tracking-[0.3em] uppercase">Daily Streak</span>
          </div>
          <div className="mt-8 flex items-baseline gap-2">
            <span className="text-6xl font-black text-text-main font-[Sora] tracking-tighter">{streak}</span>
            <span className="text-primary font-mono text-xs font-black tracking-widest uppercase">Days Active</span>
          </div>
        </div>

        <div className="hardware-card space-y-6">
          <div className="flex justify-between items-center">
            <span className="font-mono text-[10px] text-text-muted font-black tracking-[0.3em] uppercase">XP Mastery</span>
            <span className="font-mono text-[10px] text-primary font-black">LVL {Math.floor(xp / 500) + 1}</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black text-text-main font-[Sora]">{xp % 500}</span>
            <span className="text-text-muted text-xs font-mono font-bold">/ 500 XP</span>
          </div>
          <div className="h-2 w-full bg-surface-container-high rounded-full overflow-hidden relative">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${(xp % 500) / 500 * 100}%` }}
              className="h-full bg-primary rounded-full relative shadow-[0_0_15px_var(--primary)]"
            />
          </div>
        </div>
      </div>

      <section className="space-y-8">
        <div className="flex justify-between items-end">
          <h3 className="mono-text text-[10px] text-text-muted font-black tracking-[0.4em] uppercase">Featured Journey</h3>
          <span className="text-primary text-[10px] font-black tracking-widest uppercase cursor-pointer hover:underline">View All</span>
        </div>
        <div className="hardware-card group cursor-pointer hover:scale-[1.01] transition-transform duration-500">
          <div className="flex flex-col md:flex-row gap-10 items-center">
            <div className="relative w-40 h-40 flex items-center justify-center">
              <div className="absolute inset-0 border border-primary/10 rounded-full animate-[spin_10s_linear_infinite]"></div>
              <div className="absolute inset-4 border border-primary/20 rounded-full animate-[spin_6s_linear_infinite_reverse]"></div>
              <div className="w-28 h-28 rounded-full bg-surface-container-high flex items-center justify-center shadow-2xl border border-outline-variant/10">
                <span className="font-[Noto_Sans_Tamil] text-5xl text-primary font-black">{FEATURED_LESSON.word}</span>
              </div>
            </div>
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-3">
                <span className="bg-primary/10 text-primary text-[9px] font-black px-3 py-1 rounded-lg font-mono uppercase tracking-widest">{FEATURED_LESSON.type}</span>
                <span className="text-text-muted text-[10px] font-mono font-bold tracking-widest">{FEATURED_LESSON.duration}</span>
              </div>
              <h4 className="text-3xl font-black text-text-main sora-text leading-tight tracking-tighter">{FEATURED_LESSON.title}</h4>
              <p className="text-text-muted text-sm leading-relaxed font-medium">{FEATURED_LESSON.description}</p>
              <div className="pt-4">
                <button 
                  onClick={() => setScreen('play')}
                  className="bg-text-main text-background font-mono font-black text-[10px] px-10 py-4 rounded-xl uppercase tracking-[0.3em] shadow-xl hover:bg-primary hover:text-on-primary transition-all active:scale-95"
                >
                  Begin Module
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="pt-8">
        <div className="hardware-card !p-0 overflow-hidden rounded-3xl border-none shadow-2xl group">
          <div className="relative h-64 md:h-80 w-full">
            <img 
              src="https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80" 
              alt="Ancient Tamil Temple Architecture" 
              className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
              referrerPolicy="no-referrer"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent opacity-60"></div>
            <div className="absolute bottom-0 left-0 p-8 w-full">
              <p className="font-mono text-[9px] text-primary font-black tracking-[0.4em] uppercase mb-2">Heritage Integration</p>
              <h4 className="font-[Sora] text-2xl font-black text-text-main tracking-tight">Rooted in Tradition</h4>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomeScreen;
