import React, { useMemo, useState } from 'react';
import { User, Lock, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

const FLOATING_LETTERS = ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'எ'];

const SPEECH = {
  default: 'மொழிசென்ஸ்க்கு வரவேற்கிறோம்!',
  username: 'உங்கள் பெயரைச் சொல்லுங்கள்!',
  password: 'ரகசியக் குறியீட்டை உள்ளிடுங்கள்...',
  success: 'வரவேற்கிறோம்! விளையாட்டைத் தொடங்கலாம்!',
};

const LoginScreen = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [speechKey, setSpeechKey] = useState('default');
  const [submitting, setSubmitting] = useState(false);

  const floating = useMemo(
    () =>
      Array.from({ length: 20 }).map((_, i) => ({
        id: i,
        letter: FLOATING_LETTERS[i % FLOATING_LETTERS.length],
        left: `${(i * 13) % 100}%`,
        top: `${(i * 19) % 100}%`,
        delay: (i % 7) * 0.4,
        duration: 8 + (i % 5) * 2,
      })),
    []
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSpeechKey('success');

    await new Promise((resolve) => setTimeout(resolve, 450));

    onAuthSuccess({
      username,
      password,
      mode,
    });
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-text-main px-6 py-10 md:px-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(250,204,21,0.09),transparent_45%),radial-gradient(circle_at_80%_80%,rgba(250,204,21,0.05),transparent_40%)]" />

      <div className="absolute inset-0 pointer-events-none">
        {floating.map((item) => (
          <motion.span
            key={item.id}
            className="absolute text-yellow-300/20 tamil-text font-black select-none"
            style={{ left: item.left, top: item.top }}
            initial={{ opacity: 0.25, y: 0 }}
            animate={{ opacity: [0.2, 0.55, 0.2], y: [0, -18, 0] }}
            transition={{
              duration: item.duration,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: item.delay,
            }}
          >
            {item.letter}
          </motion.span>
        ))}
      </div>

      <div className="relative z-10 max-w-6xl mx-auto min-h-[calc(100vh-5rem)] grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        <motion.section
          initial={{ opacity: 0, x: -24, y: 8 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
          className="order-2 lg:order-1"
        >
          <div className="relative w-full rounded-3xl border border-yellow-400/25 bg-surface-container-high/40 backdrop-blur-md p-8 shadow-[0_0_45px_rgba(250,204,21,0.12)]">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="w-5 h-5 text-yellow-300" />
              <p className="mono-text text-[10px] tracking-[0.3em] uppercase text-yellow-300 font-black">Tamil Guru</p>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.12 }}
              className="mx-auto w-44 h-44 rounded-full bg-gradient-to-b from-yellow-400/20 to-yellow-700/10 border border-yellow-300/35 flex items-center justify-center"
            >
              <span className="text-6xl">🧑‍🏫</span>
            </motion.div>

            <AnimatePresence mode="wait">
              <motion.div
                key={speechKey}
                initial={{ opacity: 0, y: 10, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.22 }}
                className="mt-6 rounded-2xl border border-yellow-300/40 bg-yellow-300/10 px-5 py-4"
              >
                <p className="tamil-text text-lg text-yellow-200 font-bold leading-relaxed">
                  {SPEECH[speechKey]}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, x: 24, y: 8 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          transition={{ duration: 0.55, ease: 'easeOut', delay: 0.1 }}
          className="order-1 lg:order-2"
        >
          <div className="rounded-3xl border border-outline-variant/20 bg-surface-container-high/40 backdrop-blur-md p-8 md:p-10 shadow-[0_0_45px_rgba(0,0,0,0.35)]">
            <div className="text-center mb-8">
              <h1 className="sora-text text-4xl font-black tracking-tight mb-2">
                MozhiSense
              </h1>
              <p className="mono-text text-[10px] uppercase tracking-[0.35em] text-text-muted font-black">
                Gamified Tamil Semantics
              </p>
            </div>

            <div className="flex items-center gap-2 p-1 rounded-2xl bg-surface-container border border-outline-variant/20 mb-6">
              <button
                onClick={() => setMode('signin')}
                className={`flex-1 py-3 rounded-xl mono-text text-[10px] tracking-[0.25em] uppercase font-black transition-all ${
                  mode === 'signin' ? 'bg-text-main text-background' : 'text-text-muted hover:text-primary'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => setMode('register')}
                className={`flex-1 py-3 rounded-xl mono-text text-[10px] tracking-[0.25em] uppercase font-black transition-all ${
                  mode === 'register' ? 'bg-text-main text-background' : 'text-text-muted hover:text-primary'
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onFocus={() => setSpeechKey('username')}
                    className="w-full pl-11 pr-4 py-4 rounded-2xl border border-outline-variant/20 bg-surface-container-high/40 backdrop-blur-md text-text-main placeholder:text-text-muted/60 outline-none transition-all focus:border-yellow-400 focus:shadow-[0_0_0_3px_rgba(250,204,21,0.12)]"
                  />
                </div>
              </label>

              <label className="block">
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setSpeechKey('password')}
                    className="w-full pl-11 pr-4 py-4 rounded-2xl border border-outline-variant/20 bg-surface-container-high/40 backdrop-blur-md text-text-main placeholder:text-text-muted/60 outline-none transition-all focus:border-yellow-400 focus:shadow-[0_0_0_3px_rgba(250,204,21,0.12)]"
                  />
                </div>
              </label>

              <motion.button
                whileTap={{ scale: 0.95 }}
                type="submit"
                disabled={submitting}
                className="w-full mt-3 py-4 rounded-2xl bg-gradient-to-b from-yellow-300 to-yellow-500 text-black font-black mono-text text-xs tracking-[0.28em] uppercase shadow-[0_10px_25px_rgba(250,204,21,0.35)] active:scale-95 disabled:opacity-70"
              >
                {submitting ? 'Launching...' : 'Play Now'}
              </motion.button>
            </form>
          </div>
        </motion.section>
      </div>
    </div>
  );
};

export default LoginScreen;
