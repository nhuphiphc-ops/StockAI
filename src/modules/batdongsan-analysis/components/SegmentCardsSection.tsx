'use client';

import React from 'react';
import { SEGMENTS_DATA } from '../data/constants';
import { Trees, Building2, Home, Factory, ShieldAlert, Zap, Compass, Check } from 'lucide-react';
import { SpeakerButton } from './SpeakerButton';

export const SegmentCardsSection: React.FC = () => {
  const getSegmentIcon = (iconName: string) => {
    switch (iconName) {
      case 'Trees':
        return <Trees className="w-7 h-7 text-amber-400" />;
      case 'Building2':
        return <Building2 className="w-7 h-7 text-cyan-400" />;
      case 'Home':
        return <Home className="w-7 h-7 text-emerald-400" />;
      case 'Factory':
        return <Factory className="w-7 h-7 text-purple-400" />;
      default:
        return <Building2 className="w-7 h-7 text-amber-400" />;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'Cao':
      case 'Rất cao':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-rose-500/20 text-rose-400 border border-rose-500/40">Mức Rủi Ro: {risk}</span>;
      case 'Trung bình':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-500/20 text-amber-400 border border-amber-500/40">Mức Rủi Ro: {risk}</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">Mức Rủi Ro: {risk}</span>;
    }
  };

  return (
    <section id="segments" className="py-12 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold text-sm">
            <Building2 className="w-4 h-4" /> PHÂN TÍCH CHUYÊN SÂU PHÂN KHÚC
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            3. Đặc Tính Vận Hành của 4 Phân Khúc BĐS Cốt Lõi
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Mỗi phân khúc bất động sản có chu kỳ tăng trưởng, mức độ nhạy cảm rủi ro và nhóm khách hàng mục tiêu hoàn toàn riêng biệt. Không có phân khúc tốt nhất, chỉ có phân khúc phù hợp nhất với khẩu vị rủi ro và quy mô vốn.
          </p>
        </div>

        {/* 4 Segment Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {SEGMENTS_DATA.map((seg) => (
            <div
              key={seg.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 sm:p-7 space-y-6 shadow-xl flex flex-col justify-between"
            >
              <div className="space-y-5">
                {/* Title Bar */}
                <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3.5">
                    <div className="p-3 rounded-2xl bg-slate-800 border border-slate-700">
                      {getSegmentIcon(seg.iconName)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-extrabold text-slate-100">{seg.title}</h3>
                        <SpeakerButton text={`${seg.title}. ${seg.subtitle}. Độ nhạy: ${seg.sensitivity}. Tóm tắt: ${seg.summary}. Lời khuyên đầu tư: ${seg.strategicAdvice}. ${seg.historicalCase || ''}`} />
                      </div>
                      <p className="text-sm font-medium text-slate-400 mt-0.5">{seg.subtitle}</p>
                    </div>
                  </div>
                  {getRiskBadge(seg.riskLevel)}
                </div>

                {/* Sensitivity */}
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-2.5 text-amber-300 text-sm font-semibold">
                  <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>{seg.sensitivity}</span>
                </div>

                {/* Key Drivers */}
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-cyan-400" /> ĐỘNG LỰC TĂNG GIÁ CHÍNH:
                  </div>
                  <ul className="space-y-2">
                    {seg.keyDrivers.map((driver, dIdx) => (
                      <li key={dIdx} className="flex items-start gap-2.5 text-base text-slate-200 leading-snug">
                        <Check className="w-4 h-4 text-emerald-400 mt-1 shrink-0" />
                        <span>{driver}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Summary */}
                <div className="space-y-1">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">ĐÁNH GIÁ CHU KỲ:</div>
                  <p className="text-base text-slate-300 leading-relaxed">
                    {seg.summary}
                  </p>
                </div>
              </div>

              {/* Strategic Advice */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1 mt-2">
                <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-emerald-400" /> LỜI KHUYÊN NGUYÊN TẮC ĐẦU TƯ:
                </div>
                <p className="text-base font-medium text-slate-200 leading-relaxed">
                  {seg.strategicAdvice}
                </p>
              </div>

              {/* Historical Case */}
              {seg.historicalCase && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm font-medium leading-relaxed">
                  {seg.historicalCase}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
