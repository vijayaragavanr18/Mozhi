import React, { useState, useEffect } from 'react';
import { Flame, Zap, Trophy, Sun, Moon, Gamepad2, Star, ChevronRight } from 'lucide-react';
import { motion } from 'motion/react';
import { MOCK_USER, WORD_MASTERY, RECENT_ACTIVITY } from '../data.js';
import { getSessionStats, getWeakspots } from '../api/mozhisense.js';

const ProfileScreen = ({ theme, setTheme, xp, streak }) => {
  const [stats, setStats] = useState(null);
  const [weakspots, setWeakspots] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-12 pb-20">
      <section className="flex flex-col items-center text-center space-y-6">
      <div className="relative group">
        <div className="w-40 h-40 rounded-3xl overflow-hidden ring-8 ring-primary/5 p-1 transition-transform duration-700 group-hover:rotate-3">
          <img 
            alt="User profile" 
            className="w-full h-full object-cover rounded-2xl" 
            src={MOCK_USER.avatar}
            referrerPolicy="no-referrer"
          />
        </div>
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -bottom-3 -right-3 bg-text-main text-background px-5 py-2 rounded-xl text-[10px] font-black tracking-[0.2em] mono-text shadow-2xl border border-white/10"
        >
          LVL {Math.floor(xp / 500) + 1}
        </motion.div>
      </div>
      <div className="space-y-2">
        <h1 className="sora-text font-black text-4xl tracking-tighter tamil-text text-text-main">{MOCK_USER.tamilName}</h1>
        <p className="mono-text text-primary text-[10px] tracking-[0.4em] uppercase font-black opacity-80">{MOCK_USER.name} · Senior Linguist</p>
      </div>
      
      <div className="flex flex-wrap justify-center gap-3">
        {[
          { id: 'dark', label: 'Lunar (Gold)', icon: Moon },
          { id: 'light', label: 'Solar (Green)', icon: Sun },
          { id: 'white-green', label: 'White with Green', icon: Sun }
        ].map((t) => (
          <button 
            key={t.id}
            onClick={() => setTheme(t.id)}
            className={`flex items-center gap-3 px-5 py-3 rounded-2xl border transition-all active:scale-95 shadow-lg group ${
              theme === t.id 
                ? 'bg-primary text-on-primary border-primary' 
                : 'bg-surface-container border-outline-variant/10 hover:border-primary/30'
            }`}
          >
            <t.icon className={`w-4 h-4 ${theme === t.id ? 'text-on-primary' : 'text-primary'}`} />
            <span className="mono-text text-[9px] font-black uppercase tracking-[0.2em]">
              {t.label}
            </span>
          </button>
        ))}
      </div>
    </section>

    <section className="grid grid-cols-3 gap-4">
      {[
        { icon: Flame, value: streak, label: 'Streak', color: 'text-primary' },
        { icon: Trophy, value: xp.toLocaleString(), label: 'Total XP', color: 'text-primary' },
        { icon: Zap, value: `${MOCK_USER.accuracy}%`, label: 'Accuracy', color: 'text-primary' }
      ].map((stat, i) => (
        <div key={i} className="hardware-card !p-6 flex flex-col items-center justify-center space-y-2 group hover:scale-[1.02] transition-transform">
          <stat.icon className={`${stat.color} w-5 h-5 fill-current`} />
          <span className="mono-text text-xl font-black text-text-main leading-none">{stat.value}</span>
          <span className="mono-text text-[8px] text-text-muted uppercase tracking-[0.2em] font-black">{stat.label}</span>
        </div>
      ))}
    </section>

    <section className="space-y-6">
      <div className="flex justify-between items-end">
        <h2 className="sora-text font-bold text-sm tracking-widest uppercase text-outline">Word Mastery</h2>
        <span className="mono-text text-[10px] text-primary cursor-pointer">VIEW ALL</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {WORD_MASTERY.map((item, idx) => (
          <div key={idx} className="bg-surface-container p-5 rounded-xl flex flex-col items-center space-y-4 relative overflow-hidden">
            <div className="relative w-20 h-20">
              <svg className="w-full h-full" viewBox="0 0 36 36">
                <path className="text-background stroke-current" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" strokeWidth="3"></path>
                <path 
                  className={`${item.color === 'primary' ? 'text-primary' : 'text-secondary'} stroke-current`} 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  fill="none" 
                  strokeDasharray={`${item.percentage}, 100`} 
                  strokeLinecap="round" 
                  strokeWidth="3"
                  style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                ></path>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="mono-text text-xs font-bold text-text-main">{item.percentage}%</span>
              </div>
            </div>
            <div className="text-center">
              <div className="tamil-text text-2xl font-bold leading-tight text-text-main">{item.word}</div>
              <div className="mono-text text-[10px] text-text-muted uppercase">{item.transliteration}</div>
            </div>
          </div>
        ))}
      </div>
    </section>

    <section className="space-y-6">
      <h2 className="sora-text font-bold text-sm tracking-widest uppercase text-outline">Recent Activity</h2>
      <div className="space-y-4">
        {RECENT_ACTIVITY.map((activity) => (
          <div key={activity.id} className="flex items-center gap-4 p-4 bg-surface-container-low rounded-xl group transition-all duration-300">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${activity.type === 'game' ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'}`}>
              {activity.type === 'game' ? <Gamepad2 className="w-5 h-5" /> : <Star className="w-5 h-5 fill-current" />}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-text-main">{activity.title}: <span className={`mono-text ${activity.type === 'game' ? 'text-primary' : 'text-secondary'}`}>{activity.detail}</span></p>
              <p className="mono-text text-[10px] text-text-muted uppercase">{activity.time}</p>
            </div>
            {activity.xp && <div className="mono-text text-xs font-bold text-primary">+{activity.xp} XP</div>}
            {activity.type === 'badge' && <ChevronRight className="text-secondary w-5 h-5" />}
          </div>
        ))}
      </div>
    </section>
    </div>
  );
};

export default ProfileScreen;
