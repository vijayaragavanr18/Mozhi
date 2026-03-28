import React, { useState, useRef, useEffect } from 'react';
import { Flame, Zap, BookOpen, Play, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { QUESTIONS } from '../data.js';
import { recordAttempt } from '../api/mozhisense.js';

const PlayScreen = ({ addXp, streak, setStreak }) => {
  const [subTab, setSubTab] = useState('challenge');
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const dropZoneRef = useRef(null);
  
  const currentQuestion = QUESTIONS[currentQuestionIdx];

  const handleDragEnd = (_event, info, idx) => {
    if (showFeedback) return;
    
    const dropZone = dropZoneRef.current;
    if (!dropZone) return;

    const rect = dropZone.getBoundingClientRect();
    const { x, y } = info.point;

    if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
      setSelectedOption(idx);
    }
  };

  const handleCheck = async () => {
    if (selectedOption === null) return;
    const correct = selectedOption === currentQuestion.correctIndex;
    setIsCorrect(correct);
    setShowFeedback(true);
    
    setSubmitting(true);
    try {
      await recordAttempt('user_001', currentQuestion.word || 'test', currentQuestion.id || 'q_' + currentQuestionIdx, correct);
    } catch (err) {
      console.error('Failed to record attempt:', err);
    }
    setSubmitting(false);
    
    if (correct) {
      addXp(10);
    }
  };

  const handleNext = () => {
    setSelectedOption(null);
    setIsCorrect(null);
    setShowFeedback(false);
    setCurrentQuestionIdx((prev) => (prev + 1) % QUESTIONS.length);
  };

  return (
    <div className="max-w-3xl mx-auto pb-24">
      <nav className="flex justify-between items-center mb-12 bg-surface-container p-1.5 rounded-2xl border border-outline-variant/10 shadow-sm overflow-hidden">
        {[
          { id: 'challenge', label: 'CHALLENGE' },
          { id: 'practice', label: 'PRACTICE' },
          { id: 'review', label: 'REVIEW' }
        ].map(tab => (
          <button 
            key={tab.id}
            onClick={() => setSubTab(tab.id)}
            className={`flex-1 py-4 text-center mono-text text-[10px] tracking-[0.3em] font-black rounded-xl transition-all duration-500 ${
              subTab === tab.id 
                ? 'bg-text-main text-background shadow-lg' 
                : 'text-text-muted hover:text-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <AnimatePresence mode="wait">
        {subTab === 'challenge' && (
          <motion.div 
            key="challenge"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-8"
          >
            <div className="flex justify-between items-center mb-10">
              <div className="flex items-center gap-3 px-5 py-2.5 bg-surface-container rounded-xl border border-outline-variant/5">
                <Flame className="text-primary w-4 h-4 fill-current" />
                <span className="mono-text text-xs font-black text-text-main">STREAK: {streak}</span>
              </div>
              <div className="flex items-center gap-3 px-5 py-2.5 bg-primary/5 rounded-xl border border-primary/20">
                <Zap className="text-primary w-4 h-4 fill-current" />
                <span className="mono-text text-xs font-black text-primary">+10 XP</span>
              </div>
            </div>

            <div className="h-1.5 w-full bg-surface-container rounded-full mb-16 overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${((currentQuestionIdx + 1) / QUESTIONS.length) * 100}%` }}
                className="h-full bg-primary shadow-[0_0_10px_var(--primary)]"
              />
            </div>

            <section className="hardware-card relative overflow-hidden mb-12">
              <div className="text-center mb-12">
                <div className="flex flex-col items-center gap-1 mb-6">
                  <span className="mono-text text-[9px] tracking-[0.3em] text-primary uppercase font-black">Challenge</span>
                  <h3 className="sora-text text-base font-black text-text-main tracking-tight">Complete the Sentence</h3>
                </div>
                
                <div className="tamil-text text-2xl md:text-3xl font-black flex flex-wrap justify-center items-center gap-y-6 leading-tight tracking-tighter text-text-main">
                  <span>{currentQuestion.sentenceBefore}</span>
                  <div 
                    ref={dropZoneRef}
                    className={`mx-4 w-48 h-14 border-2 border-dashed rounded-xl flex items-center justify-center transition-all duration-500 ${selectedOption !== null ? 'border-primary bg-primary/5' : 'border-text-muted/20 bg-surface-container-high'}`}
                  >
                    {selectedOption !== null ? (
                      <motion.span 
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="text-primary tamil-text text-2xl"
                      >
                        {currentQuestion.options[selectedOption]}
                      </motion.span>
                    ) : (
                      <span className="text-text-muted/30 text-[9px] mono-text uppercase tracking-[0.3em] font-black">Drop Here</span>
                    )}
                  </div>
                  <span>{currentQuestion.sentenceAfter}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {currentQuestion.options.map((option, idx) => (
                  <motion.div
                    key={idx}
                    drag={!showFeedback}
                    dragSnapToOrigin
                    onDragEnd={(e, info) => handleDragEnd(e, info, idx)}
                    whileDrag={{ scale: 1.05, zIndex: 50 }}
                    className="relative"
                  >
                    <button 
                      onClick={() => !showFeedback && setSelectedOption(idx)}
                      disabled={showFeedback}
                      className={`w-full group p-4 md:p-6 rounded-xl transition-all duration-500 border-2 active:scale-95 flex items-center justify-center md:justify-between ${
                        selectedOption === idx 
                          ? 'bg-primary/5 border-primary shadow-lg shadow-primary/5' 
                          : 'bg-surface-container-high border-transparent hover:border-text-muted/20'
                      } ${showFeedback && idx === currentQuestion.correctIndex ? 'border-primary bg-primary/10' : ''} ${showFeedback && selectedOption === idx && idx !== currentQuestion.correctIndex ? 'border-red-500/50 bg-red-500/5' : ''}`}
                    >
                      <div className={`tamil-text text-sm md:text-base transition-colors text-center md:text-left ${selectedOption === idx ? 'text-primary' : 'text-text-main'}`}>{option}</div>
                      <div className={`hidden md:flex w-5 h-5 rounded-full border-2 items-center justify-center transition-all flex-shrink-0 ${selectedOption === idx ? 'border-primary bg-primary' : 'border-text-muted/20'}`}>
                        {selectedOption === idx && <CheckCircle2 className="w-3 h-3 text-background" />}
                      </div>
                    </button>
                  </motion.div>
                ))}
              </div>
            </section>

            <div className="space-y-6">
              {!showFeedback ? (
                <button 
                  onClick={handleCheck}
                  disabled={selectedOption === null}
                  className="w-full py-6 bg-text-main text-background mono-text font-black tracking-[0.4em] text-xs rounded-2xl shadow-2xl transition-all active:scale-95 disabled:opacity-30 disabled:scale-100 hover:bg-primary hover:text-on-primary"
                >
                  VALIDATE RESPONSE
                </button>
              ) : (
                <button 
                  onClick={handleNext}
                  className="w-full py-6 bg-primary text-on-primary mono-text font-black tracking-[0.4em] text-xs rounded-2xl shadow-2xl transition-all active:scale-95 hover:brightness-110"
                >
                  CONTINUE JOURNEY
                </button>
              )}
              
              <AnimatePresence>
                {showFeedback && (
                  <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`p-6 rounded-2xl flex items-start gap-4 border ${isCorrect ? 'bg-primary/5 border-primary/20 text-primary' : 'bg-red-500/5 border-red-500/20 text-red-500'}`}
                  >
                    <div className="mt-1">
                      {isCorrect ? <CheckCircle2 className="w-6 h-6" /> : <Zap className="w-6 h-6" />}
                    </div>
                    <div>
                      <p className="font-black mono-text text-[10px] uppercase tracking-[0.2em] mb-1">{isCorrect ? 'Precision Achieved' : 'Learning Opportunity'}</p>
                      <p className="font-bold text-sm leading-relaxed">{isCorrect ? 'Excellent semantic alignment. You earned 10 XP.' : currentQuestion.explanation}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}

        {subTab === 'practice' && (
          <motion.div 
            key="practice"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-10"
          >
            <div className="hardware-card bg-primary/5 border-primary/20 p-8">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
                  <BookOpen className="text-on-primary w-6 h-6" />
                </div>
                <div>
                  <h3 className="sora-text font-black text-2xl tracking-tight">Sense Explorer</h3>
                  <p className="mono-text text-[9px] text-primary font-black tracking-[0.3em] uppercase">WordNet Semantic Mapping</p>
                </div>
              </div>
              <p className="text-text-muted text-sm leading-relaxed mb-8">
                Tamil words are polysemous. Practice identifying the correct sense based on morphological cues and sentence structure.
              </p>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center px-4 py-2 bg-surface-container rounded-lg border border-outline-variant/5">
                  <span className="mono-text text-[10px] font-black text-text-muted uppercase tracking-widest">Root Word</span>
                  <span className="tamil-text text-xl font-black text-primary">படி (Padi)</span>
                </div>
                
                <div className="grid grid-cols-1 gap-4">
                  {[
                    { sense: 'To Read / Study', pos: 'Verb', example: 'பாடம் படி' },
                    { sense: 'Staircase / Step', pos: 'Noun', example: 'படி ஏறு' },
                    { sense: 'A Measure', pos: 'Noun', example: 'படி அரிசி' }
                  ].map((item, i) => (
                    <div key={i} className="bg-surface-container-high p-6 rounded-2xl border border-outline-variant/10 group hover:border-primary/30 transition-all cursor-pointer">
                      <div className="flex justify-between items-start mb-4">
                        <span className="bg-primary/10 text-primary text-[8px] font-black px-2 py-1 rounded-md mono-text uppercase tracking-widest">{item.pos}</span>
                        <div className="w-8 h-8 rounded-full border border-outline-variant/20 flex items-center justify-center group-hover:bg-primary group-hover:border-primary transition-all">
                          <Play className="w-3 h-3 text-text-muted group-hover:text-on-primary" />
                        </div>
                      </div>
                      <h4 className="text-xl font-black text-text-main mb-2">{item.sense}</h4>
                      <p className="tamil-text text-lg text-text-muted opacity-60">{item.example}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="hardware-card space-y-4">
                <h4 className="mono-text text-[10px] font-black text-text-muted uppercase tracking-[0.3em]">Morphology Drill</h4>
                <p className="text-xs text-text-muted leading-relaxed">Decompose root words into their inflected forms across tense and gender.</p>
                <button className="w-full py-4 bg-surface-container text-text-main mono-text text-[9px] font-black tracking-[0.3em] rounded-xl border border-outline-variant/10 hover:bg-primary hover:text-on-primary transition-all">START DRILL</button>
              </div>
              <div className="hardware-card space-y-4">
                <h4 className="mono-text text-[10px] font-black text-text-muted uppercase tracking-[0.3em]">POS Verification</h4>
                <p className="text-xs text-text-muted leading-relaxed">Identify the Part-of-Speech category for ambiguous words in complex syntax.</p>
                <button className="w-full py-4 bg-surface-container text-text-main mono-text text-[9px] font-black tracking-[0.3em] rounded-xl border border-outline-variant/10 hover:bg-primary hover:text-on-primary transition-all">START VERIFICATION</button>
              </div>
            </div>
          </motion.div>
        )}

        {subTab === 'review' && (
          <motion.div 
            key="review"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-10"
          >
            <div className="flex justify-between items-end">
              <div>
                <h3 className="sora-text font-black text-3xl tracking-tight">Adaptive Recovery</h3>
                <p className="mono-text text-[9px] text-primary font-black tracking-[0.3em] uppercase">Weak Spot Identification Engine</p>
              </div>
              <div className="bg-primary/10 px-4 py-2 rounded-xl border border-primary/20">
                <span className="mono-text text-xs font-black text-primary">8 WEAK LINKS</span>
              </div>
            </div>

            <div className="space-y-6">
              {[
                { word: 'ஆறு', error: 'Confusion between "River" and "Number 6"', frequency: 3, score: 42 },
                { word: 'கல்', error: 'Incorrect morphological inflection in past tense', frequency: 2, score: 58 }
              ].map((item, i) => (
                <div key={i} className="hardware-card relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-6">
                    <div className="w-12 h-12 rounded-full border-2 border-primary/10 flex items-center justify-center">
                      <span className="mono-text text-[10px] font-black text-primary">{item.score}%</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center border border-outline-variant/10">
                      <span className="tamil-text text-3xl font-black text-text-main">{item.word}</span>
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-lg font-black text-text-main">Semantic Drift Detected</h4>
                      <p className="text-xs text-text-muted max-w-md">{item.error}</p>
                      <div className="flex items-center gap-3 pt-2">
                        <span className="mono-text text-[8px] font-black text-primary uppercase tracking-widest">Retested {item.frequency}x</span>
                        <div className="w-1 h-1 bg-text-muted/30 rounded-full"></div>
                        <span className="mono-text text-[8px] font-black text-text-muted uppercase tracking-widest">Priority: High</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-8 pt-6 border-t border-outline-variant/5 flex gap-4">
                    <button className="flex-1 py-3 bg-text-main text-background mono-text text-[9px] font-black tracking-[0.3em] rounded-xl hover:bg-primary hover:text-on-primary transition-all">RETEST NOW</button>
                    <button className="px-6 py-3 bg-surface-container text-text-muted mono-text text-[9px] font-black tracking-[0.3em] rounded-xl border border-outline-variant/10 hover:text-text-main transition-all">ANALYZE</button>
                  </div>
                </div>
              ))}
            </div>

            <div className="hardware-card bg-surface-container-low border-dashed border-primary/30">
              <div className="flex flex-col items-center text-center space-y-4 py-6">
                <div className="w-16 h-16 rounded-full bg-primary/5 flex items-center justify-center border border-primary/20">
                  <Zap className="text-primary w-8 h-8" />
                </div>
                <h4 className="sora-text font-black text-xl">Perplexity Optimization</h4>
                <p className="text-xs text-text-muted max-w-sm leading-relaxed">
                  Our iNLTK perplexity gate has flagged these semantic anchors for re-validation. Complete these to stabilize your lexical graph.
                </p>
                <button className="px-10 py-4 bg-primary text-on-primary mono-text text-[10px] font-black tracking-[0.4em] rounded-xl shadow-2xl hover:brightness-110 transition-all">
                  STABILIZE GRAPH
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PlayScreen;
