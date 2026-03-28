import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Trophy } from 'lucide-react';

import TopBar from './components/TopBar.jsx';
import BottomNav from './components/BottomNav.jsx';
import HomeScreen from './screens/HomeScreen.jsx';
import PlayScreen from './screens/PlayScreen.jsx';
import ExploreScreen from './screens/ExploreScreen.jsx';
import ProfileScreen from './screens/ProfileScreen.jsx';

export default function App() {
  const [screen, setScreen] = useState('home');
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('mozhi-theme');
    return saved || 'dark';
  });
  const [xp, setXp] = useState(() => Number(localStorage.getItem('mozhi-xp')) || 250);
  const [streak, setStreak] = useState(() => Number(localStorage.getItem('mozhi-streak')) || 5);
  const [selectedWord, setSelectedWord] = useState('படி');

  useEffect(() => {
    localStorage.setItem('mozhi-theme', theme);
    document.documentElement.classList.remove('light', 'dark', 'white-green');
    document.documentElement.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('mozhi-xp', xp.toString());
    localStorage.setItem('mozhi-streak', streak.toString());
  }, [xp, streak]);

  const [showLevelUp, setShowLevelUp] = useState(false);

  const addXp = (amount) => {
    const oldLevel = Math.floor(xp / 500) + 1;
    const newXp = xp + amount;
    const newLevel = Math.floor(newXp / 500) + 1;
    
    setXp(newXp);
    
    if (newLevel > oldLevel) {
      setShowLevelUp(true);
      setTimeout(() => setShowLevelUp(false), 3000);
    }
  };

  const renderScreen = () => {
    switch (screen) {
      case 'home': return <HomeScreen setScreen={setScreen} setSelectedWord={setSelectedWord} xp={xp} streak={streak} />;
      case 'play': return <PlayScreen addXp={addXp} streak={streak} setStreak={setStreak} />;
      case 'explore': return <ExploreScreen selectedWord={selectedWord} setSelectedWord={setSelectedWord} />;
      case 'profile': return <ProfileScreen theme={theme} setTheme={setTheme} xp={xp} streak={streak} />;
      default: return <HomeScreen setScreen={setScreen} setSelectedWord={setSelectedWord} xp={xp} streak={streak} />;
    }
  };

  return (
    <div className="min-h-screen bg-background text-text-main pb-32 transition-colors duration-300">
      <TopBar xp={xp} />
      <main className="pt-24 px-6 max-w-2xl mx-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={screen}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {renderScreen()}
          </motion.div>
        </AnimatePresence>
      </main>
      <BottomNav currentScreen={screen} setScreen={setScreen} />
      
      <AnimatePresence>
        {showLevelUp && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.5, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.5, y: 50 }}
            className="fixed top-24 left-1/2 -translate-x-1/2 z-[100] bg-secondary text-on-secondary px-8 py-4 rounded-2xl shadow-2xl flex flex-col items-center gap-2 border-4 border-white/20"
          >
            <Trophy className="w-12 h-12" />
            <div className="text-center">
              <h3 className="font-headline font-black text-3xl uppercase tracking-tighter premium-gradient-text">LEVEL UP!</h3>
              <p className="mono-text text-[10px] font-black tracking-[0.4em] opacity-80">PHASE {Math.floor(xp / 500) + 1} INITIATED</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
