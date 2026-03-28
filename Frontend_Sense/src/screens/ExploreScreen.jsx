import React, { useState, useEffect } from 'react';
import { Mic, Star, BookOpen, Bookmark, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { getSemanticGraph, getWordSenses, getChallengesByWord } from '../api/mozhisense.js';

const ExploreScreen = ({ selectedWord, setSelectedWord, setScreen }) => {
  const [graphData, setGraphData] = useState(null);
  const [senses, setSenses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showArchitectLoader, setShowArchitectLoader] = useState(false);
  const [loaderStep, setLoaderStep] = useState(0);
  const [freshlyMinted, setFreshlyMinted] = useState(false);
  const [generationFailed, setGenerationFailed] = useState(false);

  const ARCHITECT_STEPS = [
    'Searching WordNet...',
    'Consulting LLM...',
    'Applying Morphology Rules...',
    'Finalizing Challenge...'
  ];

  const rootWord = selectedWord || 'படி';
  const senseNodes = (graphData?.nodes || []).filter(node => String(node.id).startsWith('root:') === false);

  useEffect(() => {
    if (!rootWord) return;

    let isMounted = true;
    const startedAt = Date.now();

    setLoading(true);
    setError(null);
    setGenerationFailed(false);
    setFreshlyMinted(false);

    const delayedLoader = setTimeout(() => {
      if (isMounted) {
        setShowArchitectLoader(true);
      }
    }, 500);

    const stepCycler = setInterval(() => {
      if (isMounted) {
        setLoaderStep((prev) => (prev + 1) % ARCHITECT_STEPS.length);
      }
    }, 1100);

    (async () => {
      try {
        const challengeList = await getChallengesByWord(rootWord);
        const wasGenerated = Boolean(challengeList?.[0]?.generated);
        const [graph, senseList] = await Promise.all([getSemanticGraph(rootWord), getWordSenses(rootWord)]);
        if (!isMounted) return;
        setGraphData(graph);
        setSenses(Array.isArray(senseList) ? senseList : []);
        setFreshlyMinted(wasGenerated || Date.now() - startedAt > 500);
      } catch (err) {
        if (!isMounted) return;
        const message = err?.message || 'Failed to load semantic data';
        console.error('Graph load error:', err);
        setError(message);
        setGraphData(null);
        setSenses([]);

        const isGenerationError = /generation failed|ollama|llm|connection|refused|timeout/i.test(message);
        setGenerationFailed(isGenerationError);
      } finally {
        if (!isMounted) return;
        setLoading(false);
        setShowArchitectLoader(false);
        setLoaderStep(0);
      }
    })();

    return () => {
      isMounted = false;
      clearTimeout(delayedLoader);
      clearInterval(stepCycler);
    };
  }, [rootWord]);

  if (generationFailed) {
    return (
      <div className="space-y-8 pb-20">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="hardware-card backdrop-blur-md bg-surface-container-high/60 border border-outline-variant/20 drop-shadow-lg"
        >
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-5 h-5 text-yellow-400" />
            <p className="mono-text text-[10px] tracking-[0.3em] uppercase font-black text-yellow-400">AI Architect</p>
          </div>
          <h3 className="text-xl font-black mb-3">Our AI is currently resting.</h3>
          <p className="text-sm text-text-muted mb-6">Try one of our 451 pre-built challenges!</p>
          <button
            onClick={() => setScreen && setScreen('play')}
            className="px-6 py-3 rounded-xl bg-text-main text-background mono-text text-[10px] font-black tracking-[0.3em] hover:bg-primary hover:text-on-primary transition-all"
          >
            GO TO RANDOM CHALLENGE
          </button>
        </motion.section>
      </div>
    );
  }

  if (loading && showArchitectLoader) {
    return (
      <div className="space-y-8 pb-20">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="hardware-card backdrop-blur-md bg-surface-container-high/60 border border-outline-variant/20 drop-shadow-lg"
        >
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse" />
            <p className="mono-text text-[10px] tracking-[0.3em] uppercase font-black text-yellow-400">AI Architect</p>
          </div>
          <p className="text-lg font-black text-text-main mb-2">Building semantic challenge for “{rootWord}”</p>
          <p className="text-sm text-text-muted mb-5">{ARCHITECT_STEPS[loaderStep]}</p>

          <div className="space-y-3">
            <div className="h-5 w-2/3 rounded-md bg-surface-container animate-pulse" />
            <div className="h-14 w-full rounded-xl bg-surface-container animate-pulse" />
            <div className="grid grid-cols-2 gap-3">
              <div className="h-12 rounded-xl bg-surface-container animate-pulse" />
              <div className="h-12 rounded-xl bg-surface-container animate-pulse" />
              <div className="h-12 rounded-xl bg-surface-container animate-pulse" />
              <div className="h-12 rounded-xl bg-surface-container animate-pulse" />
            </div>
          </div>
        </motion.section>
      </div>
    );
  }

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
            <span className="tamil-text text-3xl md:text-4xl font-black text-background">{rootWord}</span>
          </motion.div>
          <div className="mt-4 px-3 py-1 bg-surface-container rounded-lg border border-outline-variant/10 shadow-sm">
            <span className="mono-text text-[8px] tracking-[0.3em] text-text-muted uppercase font-black">Semantic Core</span>
          </div>
        </div>

        {/* Dynamic sense nodes from graph data */}
        {senseNodes.slice(0, 3).map((node, index) => {
          const positions = [
            'absolute left-[18%] top-[20%] flex flex-col items-center group',
            'absolute right-[18%] top-[30%] flex flex-col items-center group',
            'absolute bottom-[15%] left-[48%] -translate-x-1/2 flex flex-col items-center group',
          ];
          const label = String(node.meaning_ta || node.label || '').slice(0, 14);
          return (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.8 + index * 0.2 }}
              className={positions[index]}
            >
              <div className="w-16 h-16 rounded-xl bg-surface-container-high flex items-center justify-center border border-primary/20 shadow-lg">
                <span className="tamil-text text-sm font-black text-primary text-center px-1 line-clamp-2">{label || rootWord}</span>
              </div>
              <div className="mt-2 px-2 py-0.5 bg-primary/10 rounded-md border border-primary/20">
                <span className="mono-text text-[7px] tracking-[0.2em] text-primary uppercase font-black">{String(node.pos || 'Sense')}</span>
              </div>
            </motion.div>
          );
        })}
      </section>

      <motion.section 
        key={rootWord}
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
              <h2 className="tamil-text text-6xl font-black premium-gradient-text">{rootWord}</h2>
              <span className="mono-text text-sm text-text-muted font-bold tracking-widest">[{rootWord}]</span>
              {freshlyMinted && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-yellow-400/50 bg-yellow-400/10 text-yellow-300 text-[10px] mono-text font-black tracking-[0.18em] uppercase">
                  <Sparkles className="w-3 h-3" /> Freshly Minted
                </span>
              )}
            </div>
            
            <div className="grid grid-cols-1 gap-8">
              <div className="space-y-2">
                <p className="mono-text text-primary uppercase text-[10px] font-black tracking-[0.4em]">Primary Definition</p>
                <p className="text-text-main text-2xl font-black leading-tight">
                  {loading ? 'Loading...' : (senses[0]?.meaning_ta || 'No meaning available for this word')}
                </p>
              </div>
              
              <div className="bg-surface-container-high p-8 rounded-2xl border border-outline-variant/10 relative group">
                <div className="absolute top-4 right-4">
                  <Mic className="text-primary/20 w-5 h-5" />
                </div>
                <p className="mono-text text-text-muted uppercase text-[9px] font-black tracking-[0.4em] mb-4">Contextual Application</p>
                <p className="tamil-text text-xl text-primary font-black leading-relaxed mb-4">
                  {loading ? 'Loading semantic context...' : (graphData?.nodes?.[1]?.meaning_ta || senses[0]?.meaning_ta || rootWord)}
                </p>
                <p className="text-sm text-text-muted font-medium italic border-l-2 border-primary/20 pl-4">
                  {loading ? 'Loading...' : (senses[0]?.meaning_en || 'Semantic sense loaded from dataset')}
                </p>
              </div>

              <div className="space-y-4">
                <p className="mono-text text-primary uppercase text-[10px] font-black tracking-[0.4em]">Morphological Architecture</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {senses.slice(0, 6).map((sense, i) => (
                    <div key={sense.id || i} className="bg-surface-container p-5 rounded-xl border border-outline-variant/5 hover:border-primary/20 transition-colors group">
                      <p className="mono-text text-[9px] text-text-muted mb-2 uppercase tracking-widest font-black group-hover:text-primary transition-colors">{sense.pos || 'Sense'}</p>
                      <p className="tamil-text text-base text-text-main font-black leading-snug">{sense.meaning_ta}</p>
                    </div>
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/5 text-red-500 text-sm">
                  {error}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
              <button 
                onClick={() => {
                  const utterance = new SpeechSynthesisUtterance(rootWord);
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
              <span className="text-5xl font-black sora-text text-primary tracking-tighter">{senses.length}</span>
              <div className="flex gap-1.5 mb-2">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className={`w-1.5 rounded-full ${i <= Math.min(4, Math.max(1, Math.ceil(senses.length / 2))) ? 'bg-primary' : 'bg-primary/10'}`} style={{ height: `${i * 8}px` }}></div>
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
              <span className="text-xl font-black sora-text text-text-main tracking-tight">{senses.length > 6 ? 'Level 4 Essential' : senses.length > 2 ? 'Level 3 Active' : 'Level 2 Emerging'}</span>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
};

export default ExploreScreen;
