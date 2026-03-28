import React from 'react';
import { Flame, Menu } from 'lucide-react';

const TopBar = ({ xp }) => (
  <header className="fixed top-0 w-full z-50 flex justify-between items-center px-8 h-20 bg-background/60 backdrop-blur-xl border-b border-outline-variant/5">
    <div className="flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
        <Flame className="text-primary w-6 h-6 fill-current" />
      </div>
      <h1 className="text-text-main font-headline font-black tracking-tighter text-2xl">MozhiSense</h1>
    </div>
    <div className="flex items-center gap-4">
      <div className="bg-surface-container-high px-4 py-2 rounded-xl flex items-center gap-2 border border-outline-variant/10 shadow-[0_0_15px_rgba(var(--primary),0.1)]">
        <span className="text-primary font-mono font-black text-xs uppercase tracking-widest">{xp} XP</span>
      </div>
      <Menu className="text-text-muted w-6 h-6 cursor-pointer hover:text-primary transition-colors" />
    </div>
  </header>
);

export default TopBar;
