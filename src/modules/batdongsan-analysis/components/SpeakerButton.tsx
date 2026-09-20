'use client';

import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface SpeakerButtonProps {
  text: string;
  className?: string;
}

export const SpeakerButton: React.FC<SpeakerButtonProps> = ({ text, className = '' }) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const toggleSpeech = (e: React.MouseEvent) => {
    e.stopPropagation();

    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      alert('Trình duyệt của bạn không hỗ trợ đọc giọng nói (Text-to-Speech).');
      return;
    }

    const synth = window.speechSynthesis;

    if (isPlaying) {
      synth.cancel();
      setIsPlaying(false);
    } else {
      synth.cancel(); // Stop any existing speech

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'vi-VN';
      utterance.rate = 1.0;

      // Select Vietnamese voice if available
      const voices = synth.getVoices();
      const viVoice = voices.find((v) => v.lang.toLowerCase().includes('vi'));
      if (viVoice) {
        utterance.voice = viVoice;
      }

      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);

      synth.speak(utterance);
      setIsPlaying(true);
    }
  };

  return (
    <button
      onClick={toggleSpeech}
      type="button"
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold transition-all duration-200 select-none ${
        isPlaying
          ? 'bg-amber-500 text-slate-950 shadow-md animate-pulse ring-2 ring-amber-400'
          : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-amber-400 border border-slate-700'
      } ${className}`}
      title={isPlaying ? 'Bấm để dừng đọc' : 'Bấm để nghe đọc nội dung bằng giọng nói'}
    >
      {isPlaying ? (
        <>
          <VolumeX className="w-3.5 h-3.5 text-slate-950" />
          <span>Dừng nghe</span>
        </>
      ) : (
        <>
          <Volume2 className="w-3.5 h-3.5 text-amber-400" />
          <span>Nghe đọc 🔊</span>
        </>
      )}
    </button>
  );
};
