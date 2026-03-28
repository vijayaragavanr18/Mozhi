import React, { useState, useEffect } from 'react';
import { Search, Mic, Flame } from 'lucide-react';
import { motion } from 'motion/react';
import { MOCK_USER, FEATURED_LESSON } from '../data.js';
import { getAllWords, searchWords } from '../api/mozhisense.js';

const HomeScreen = ({ setScreen, setSelectedWord, xp, streak }) => {
  const [search, setSearch] = useState('');
  const [words, setWords] = useState(['படி', 'ஆறு', 'கல்', 'திங்கள்', 'வாய்']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAllWords()
      .then(data => setWords(data.words || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);
  
  const handleWordClick = (word) => {
    setSelectedWord(word);
    setScreen('explore');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) {
      handleWordClick(search.trim());
    }
  };

  return (
    <div className="space-y-12 pb-12">
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
