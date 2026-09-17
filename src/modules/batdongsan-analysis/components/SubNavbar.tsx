'use client';

import React, { useState, useEffect } from 'react';
import {
  Compass,
  Layers,
  Building,
  Scale,
  Globe2,
  Activity,
  Menu,
  X,
} from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

export const SubNavbar: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('cause-effect');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const navItems: NavItem[] = [
    { id: 'cause-effect', label: 'Khung Tư Duy', icon: <Compass className="w-4 h-4" /> },
    { id: 'factors', label: 'Nhóm Yếu Tố', icon: <Layers className="w-4 h-4" /> },
    { id: 'segments', label: 'Phân Khúc BĐS', icon: <Building className="w-4 h-4" /> },
    { id: 'principles', label: 'Công Thức Vàng', icon: <Scale className="w-4 h-4" /> },
    { id: 'global-risk', label: '🌍 Rủi Ro Toàn Cầu', icon: <Globe2 className="w-4 h-4" /> },
    { id: 'live-monitor', label: 'Bảng Theo Dõi Thực Tế', icon: <Activity className="w-4 h-4" /> },
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 200;
      for (const item of navItems) {
        const element = document.getElementById(item.id);
        if (element) {
          const top = element.offsetTop;
          const height = element.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(item.id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      const yOffset = -80;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Section Indicator Label */}
          <div className="flex items-center gap-2 text-amber-400 font-bold text-base">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
            <span className="hidden sm:inline">Đang xem:</span>
            <span className="text-slate-100 font-semibold truncate max-w-[200px] sm:max-w-none">
              {navItems.find((item) => item.id === activeSection)?.label}
            </span>
          </div>

          {/* Desktop Nav Items */}
          <div className="hidden lg:flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
            {navItems.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-base font-medium transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                      : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/80 border border-transparent'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="flex lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2.5 rounded-xl bg-slate-800 text-slate-200 hover:text-amber-400 border border-slate-700 focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-slate-900 border-b border-slate-800 px-4 pt-2 pb-4 space-y-2 shadow-2xl animate-in slide-in-from-top duration-200">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                  isActive
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
};
