import React from 'react';
import { Home as HomeIcon, Gamepad2, Compass, User } from 'lucide-react';
import { motion } from 'motion/react';

const BottomNav = ({ currentScreen, setScreen }) => {
  const navItems = [
    { id: 'home', label: 'HOME', icon: HomeIcon },
    { id: 'play', label: 'PLAY', icon: Gamepad2 },
    { id: 'explore', label: 'EXPLORE', icon: Compass },
    { id: 'profile', label: 'PROFILE', icon: User },
  ];

  return (
    <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-lg z-50 flex justify-around items-center h-16 px-6 glass-nav rounded-2xl shadow-2xl">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = currentScreen === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setScreen(item.id)}
            className={`relative flex flex-col items-center justify-center transition-all duration-500 ${
              isActive ? 'text-primary' : 'text-text-muted hover:text-text-main'
            }`}
          >
            <Icon className={`w-5 h-5 mb-1 transition-transform duration-500 ${isActive ? 'scale-110' : ''}`} />
            <span className="font-mono text-[8px] font-black tracking-[0.2em]">{item.label}</span>
            {isActive && (
              <motion.div 
                layoutId="nav-indicator"
                className="absolute -bottom-2 w-1 h-1 bg-primary rounded-full shadow-[0_0_8px_var(--primary)]"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
};

export default BottomNav;
