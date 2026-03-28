import React, { useState, useEffect } from 'react';
import { Mic, Star, BookOpen, Bookmark } from 'lucide-react';
import { motion } from 'motion/react';
import { WORD_DETAILS } from '../data.js';
import { getSemanticGraph, getWordSenses } from '../api/mozhisense.js';

const ExploreScreen = ({ selectedWord, setSelectedWord }) => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const detail = WORD_DETAILS[selectedWord] || WORD_DETAILS['படி'];

  useEffect(() => {
    if (!selectedWord) return;
    setLoading(true);
    getSemanticGraph(selectedWord)
      .then(data => setGraphData(data))
      .catch(err => console.error('Graph load error:', err))
      .finally(() => setLoading(false));
  }, [selectedWord]);

  return (
    <div className="space-y-12 pb-20">
      <section className="relative w-full h-[380px] flex items-center justify-center overflow-hidden hardware-card !p-0 border-none bg-transparent">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(var(--primary),0.05),transparent_70%)]"></div>
        
        {/* Tech Scanline Effect */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-10">
          <motion.div 
            animate={{ y: ['0%', '100%'] }}
            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            className="w-full h-[2px] bg-primary shadow-[0_0_15px_var(--primary)]"
          />
        </div>
        
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30">
          <motion.line 
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            x1="50%" y1="50%" x2="25%" y2="25%" stroke="var(--primary)" strokeWidth="1" strokeDasharray="4 4" 
          />
          <motion.line 
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, delay: 0.3, ease: "easeInOut" }}
            x1="50%" y1="50%" x2="75%" y2="35%" stroke="var(--primary)" strokeWidth="1" strokeDasharray="4 4" 
          />
          <motion.line 
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, delay: 0.6, ease: "easeInOut" }}
            x1="50%" y1="50%" x2="50%" y2="75%" stroke="var(--primary)" strokeWidth="1" strokeDasharray="4 4" 
          />
        </svg>

        <div className="relative z-10 flex flex-col items-center">
          <motion.div 
            layoutId="root-word"
            className="w-24 h-24 md:w-28 md:h-28 rounded-full bg-text-main flex items-center justify-center ring-4 ring-primary/10 shadow-[0_0_30px_rgba(var(--primary),0.2)]"
          >
            <span className="tamil-text text-3xl md:text-4xl font-black text-background">{detail.word}</span>
          </motion.div>
          <div className="mt-4 px-3 py-1 bg-surface-container rounded-lg border border-outline-variant/10 shadow-sm">
            <span className="mono-text text-[8px] tracking-[0.3em] text-text-muted uppercase font-black">Semantic Core</span>
          </div>
        </div>

        {/* Floating Nodes */}
        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
          onClick={() => setSelectedWord('படிக்க')}
          className="absolute left-[18%] top-[20%] flex flex-col items-center group cursor-pointer"
        >
          <div className="w-14 h-14 md:w-16 md:h-16 rounded-xl bg-surface-container-high flex items-center justify-center border border-primary/20 group-hover:scale-110 group-hover:bg-primary/5 transition-all duration-500 shadow-lg">
            <span className="tamil-text text-lg md:text-xl font-black text-primary">படிக்க</span>
          </div>
          <div className="mt-2 px-2 py-0.5 bg-primary/10 rounded-md border border-primary/20">
            <span className="mono-text text-[7px] tracking-[0.2em] text-primary uppercase font-black">VERB</span>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1 }}
          onClick={() => setSelectedWord('ஆறு')}
          className="absolute right-[18%] top-[30%] flex flex-col items-center group cursor-pointer"
        >
          <div className="w-14 h-14 md:w-16 md:h-16 rounded-xl bg-surface-container-high flex items-center justify-center border border-text-muted/20 group-hover:scale-110 group-hover:bg-primary/5 transition-all duration-500 shadow-lg">
            <span className="tamil-text text-lg md:text-xl font-black text-text-main">ஆறு</span>
          </div>
          <div className="mt-2 px-2 py-0.5 bg-surface-container rounded-md border border-outline-variant/10">
            <span className="mono-text text-[7px] tracking-[0.2em] text-text-muted uppercase font-black">DERIVATIVE</span>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-[15%] left-[48%] -translate-x-1/2 flex flex-col items-center group cursor-pointer"
        >
          <div className="w-14 h-14 md:w-16 md:h-16 rounded-xl bg-surface-container-high flex items-center justify-center border border-text-muted/20 group-hover:scale-110 transition-all duration-500 shadow-lg">
            <span className="tamil-text text-lg md:text-xl font-black text-text-main">கல்</span>
          </div>
          <div className="mt-2 px-2 py-0.5 bg-surface-container rounded-md border border-outline-variant/10">
            <span className="mono-text text-[7px] tracking-[0.2em] text-text-muted uppercase font-black">ANALOGY</span>
          </div>
        </motion.div>
      </section>

      <motion.section 
        key={detail.word}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl mx-auto space-y-8"
      >
        <div className="hardware-card relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <BookOpen className="w-32 h-32" />
          </div>
          <div className="flex flex-col gap-10">
            <div className="flex items-baseline gap-6">
              <h2 className="tamil-text text-6xl font-black premium-gradient-text">{detail.word}</h2>
              <span className="mono-text text-sm text-text-muted font-bold tracking-widest">[{detail.transliteration}]</span>
            </div>
            
            <div className="grid grid-cols-1 gap-8">
              <div className="space-y-2">
                <p className="mono-text text-primary uppercase text-[10px] font-black tracking-[0.4em]">Primary Definition</p>
                <p className="text-text-main text-2xl font-black leading-tight">{detail.meaning}</p>
              </div>
              
              <div className="bg-surface-container-high p-8 rounded-2xl border border-outline-variant/10 relative group">
                <div className="absolute top-4 right-4">
                  <Mic className="text-primary/20 w-5 h-5" />
                </div>
                <p className="mono-text text-text-muted uppercase text-[9px] font-black tracking-[0.4em] mb-4">Contextual Application</p>
                <p className="tamil-text text-3xl text-primary font-black leading-relaxed mb-4">{detail.exampleTamil}</p>
                <p className="text-sm text-text-muted font-medium italic border-l-2 border-primary/20 pl-4">{detail.exampleEnglish}</p>
              </div>

              <div className="space-y-4">
                <p className="mono-text text-primary uppercase text-[10px] font-black tracking-[0.4em]">Morphological Architecture</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {detail.morphology.map((form, i) => (
                    <div key={i} className="bg-surface-container p-5 rounded-xl border border-outline-variant/5 hover:border-primary/20 transition-colors group">
                      <p className="mono-text text-[9px] text-text-muted mb-2 uppercase tracking-widest font-black group-hover:text-primary transition-colors">{form.label}</p>
                      <p className="tamil-text text-2xl text-text-main font-black">{form.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
              <button 
                onClick={() => {
                  const utterance = new SpeechSynthesisUtterance(detail.word);
                  utterance.lang = 'ta-IN';
                  window.speechSynthesis.speak(utterance);
                }}
                className="bg-text-main text-background mono-text py-5 rounded-2xl uppercase font-black text-[10px] tracking-[0.3em] flex items-center justify-center gap-3 hover:bg-primary hover:text-on-primary transition-all active:scale-95 shadow-xl"
              >
                AUDITORY GUIDE
                <Mic className="w-5 h-5" />
              </button>
              <button className="border-2 border-text-main/10 text-text-main mono-text py-5 rounded-2xl uppercase font-black text-[10px] tracking-[0.3em] flex items-center justify-center gap-3 hover:bg-surface-container transition-all active:scale-95">
                ARCHIVE WORD
                <Bookmark className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="hardware-card flex flex-col justify-between">
            <h3 className="mono-text text-[10px] text-text-muted font-black tracking-[0.4em] mb-6">USAGE VELOCITY</h3>
            <div className="flex items-end gap-3">
              <span className="text-5xl font-black sora-text text-primary tracking-tighter">{detail.frequency}</span>
              <div className="flex gap-1.5 mb-2">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className={`w-1.5 rounded-full ${i <= (detail.frequency === 'High' ? 3 : 2) ? 'bg-primary' : 'bg-primary/10'}`} style={{ height: `${i * 8}px` }}></div>
                ))}
              </div>
            </div>
          </div>
          <div className="hardware-card flex flex-col justify-between">
            <h3 className="mono-text text-[10px] text-text-muted font-black tracking-[0.4em] mb-6">SEMANTIC RELIANCE</h3>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Star className="text-primary w-6 h-6 fill-current" />
              </div>
              <span className="text-xl font-black sora-text text-text-main tracking-tight">{detail.reliance}</span>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
};

export default ExploreScreen;
