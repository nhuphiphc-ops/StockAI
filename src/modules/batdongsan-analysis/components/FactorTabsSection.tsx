'use client';

import React, { useState } from 'react';
import { FACTOR_TABS_DATA } from '../data/constants';
import { Landmark, FileText, TrendingUp, HardHat, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

export const FactorTabsSection: React.FC = () => {
  const [activeTabId, setActiveTabId] = useState<string>('financial');

  const activeGroup = FACTOR_TABS_DATA.find((tab) => tab.id === activeTabId) || FACTOR_TABS_DATA[0];

  const getTabIcon = (iconName: string) => {
    switch (iconName) {
      case 'Landmark':
        return <Landmark className="w-5 h-5" />;
      case 'FileText':
        return <FileText className="w-5 h-5" />;
      case 'TrendingUp':
        return <TrendingUp className="w-5 h-5" />;
      case 'HardHat':
        return <HardHat className="w-5 h-5" />;
      default:
        return <Layers className="w-5 h-5" />;
    }
  };

  return (
    <section id="factors" className="py-12 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-semibold text-sm">
            <Layers className="w-4 h-4" /> 4 TRỤ CỘT ẢNH HƯỞNG VĨ MÔ
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            2. Phân Tích Chi Tiết 4 Nhóm Yếu Tố Ảnh Hưởng BĐS
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Phân tích 2 chiều (Kịch bản Tăng điểm vs Kịch bản Suy giảm) của từng nhóm chỉ số tác động giúp xác định chính xác phân khúc bất động sản nào sẽ được thụ hưởng lợi ích hoặc chịu ảnh hưởng nặng nề nhất.
          </p>
        </div>

        {/* 4 Tabs Selector Navigation */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-900 p-2 rounded-2xl border border-slate-800">
          {FACTOR_TABS_DATA.map((tab) => {
            const isActive = tab.id === activeTabId;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTabId(tab.id)}
                className={`flex items-center justify-center gap-2.5 px-4 py-3.5 rounded-xl font-bold text-base transition-all duration-200 ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 shadow-lg scale-[1.02]'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/80'
                }`}
              >
                {getTabIcon(tab.iconName)}
                <span className="truncate">{tab.title}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Header Description Banner */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-start gap-4">
          <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 shrink-0">
            {getTabIcon(activeGroup.iconName)}
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-extrabold text-slate-100">{activeGroup.title}</h3>
            <p className="text-slate-300 text-base leading-relaxed">{activeGroup.description}</p>
          </div>
        </div>

        {/* Factors List Cards */}
        <div className="space-y-6">
          {activeGroup.factors.map((factor, index) => (
            <div
              key={index}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl"
            >
              {/* Factor Name & Target Segments */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800 pb-4">
                <h4 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                  {factor.name}
                </h4>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Phân khúc ảnh hưởng:</span>
                  {factor.impactedSegments.map((seg, sIdx) => (
                    <span
                      key={sIdx}
                      className="px-2.5 py-1 rounded-md text-xs font-bold bg-slate-800 text-amber-300 border border-slate-700"
                    >
                      {seg}
                    </span>
                  ))}
                </div>
              </div>

              {/* 2 Scenarios Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Bullish Scenario */}
                <div className="p-5 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-base">
                    <CheckCircle2 className="w-5 h-5 shrink-0" />
                    <span>KỊCH BẢN TÍCH CỰC (TĂNG ĐIỂM / NỚI LỎNG)</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {factor.bullScenario}
                  </div>
                  <p className="text-slate-300 text-base leading-relaxed">
                    <span className="text-emerald-400 font-semibold">Tác động: </span>
                    {factor.bullImpact}
                  </p>
                </div>

                {/* Bearish Scenario */}
                <div className="p-5 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-3">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-base">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span>KỊCH BẢN TIÊU CỰC (SUY GIẢM / THẮT CHẶT)</span>
                  </div>
                  <div className="text-base font-bold text-slate-100">
                    {factor.bearScenario}
                  </div>
                  <p className="text-slate-300 text-base leading-relaxed">
                    <span className="text-rose-400 font-semibold">Tác động: </span>
                    {factor.bearImpact}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
