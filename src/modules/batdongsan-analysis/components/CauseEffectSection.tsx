'use client';

import React, { useState, useMemo } from 'react';
import { CauseEffectItem, ImpactType } from '../types';
import { INITIAL_CAUSE_EFFECT_DATA } from '../data/constants';
import { Search, TrendingUp, TrendingDown, Snowflake, Filter, Compass } from 'lucide-react';

export const CauseEffectSection: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedImpact, setSelectedImpact] = useState<ImpactType | 'all'>('all');

  const filteredItems = useMemo(() => {
    return INITIAL_CAUSE_EFFECT_DATA.filter((item) => {
      const matchesSearch =
        item.cause.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.effect.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.detail.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.impactGroup.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesImpact = selectedImpact === 'all' || item.impactType === selectedImpact;

      return matchesSearch && matchesImpact;
    });
  }, [searchTerm, selectedImpact]);

  const getImpactBadge = (type: ImpactType) => {
    switch (type) {
      case 'increase':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
            <TrendingUp className="w-4 h-4" /> Tăng Giá / Kích Thích
          </span>
        );
      case 'decrease':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/40">
            <TrendingDown className="w-4 h-4" /> Giảm Giá / Ép Bán
          </span>
        );
      case 'freeze':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
            <Snowflake className="w-4 h-4" /> Đóng Băng Thanh Khoản
          </span>
        );
    }
  };

  return (
    <section id="cause-effect" className="py-12 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Section Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold text-sm">
            <Compass className="w-4 h-4" /> KHUNG TƯ DUY NGUYÊN NHÂN - KẾT QUẢ
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            1. Bảng Ma Trận Nhân - Quả Chi Phối Thị Trường BĐS
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Giá và thanh khoản bất động sản luôn là kết quả của các xung lực kinh tế vĩ mô. Hiểu rõ mối liên hệ nhân - quả giúp nhà đầu tư chủ động ứng phó trước mọi diễn biến biến động của thị trường.
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-slate-900 p-4 sm:p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4 sm:space-y-0 sm:flex sm:items-center sm:justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm kiếm tác động (Lãi suất, Tỷ giá, Đòn bẩy, Đầu tư công...)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-base focus:outline-none focus:border-amber-500 transition-colors"
            />
          </div>

          {/* Impact Filter Buttons */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
            <span className="text-sm font-semibold text-slate-400 flex items-center gap-1.5 mr-1 hidden md:flex">
              <Filter className="w-4 h-4" /> Lọc:
            </span>
            <button
              onClick={() => setSelectedImpact('all')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                selectedImpact === 'all'
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-md'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Tất cả ({INITIAL_CAUSE_EFFECT_DATA.length})
            </button>
            <button
              onClick={() => setSelectedImpact('increase')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                selectedImpact === 'increase'
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-md'
                  : 'bg-slate-800 text-emerald-400 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Tăng giá ⬆️
            </button>
            <button
              onClick={() => setSelectedImpact('decrease')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                selectedImpact === 'decrease'
                  ? 'bg-rose-500 text-slate-950 font-bold shadow-md'
                  : 'bg-slate-800 text-rose-400 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Giảm giá ⬇️
            </button>
            <button
              onClick={() => setSelectedImpact('freeze')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                selectedImpact === 'freeze'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                  : 'bg-slate-800 text-cyan-400 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Đóng băng ❄️
            </button>
          </div>
        </div>

        {/* Cause-Effect Cards Matrix Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900 border border-slate-800 hover:border-amber-500/40 rounded-2xl p-6 space-y-4 shadow-lg transition-all duration-200 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
                    {item.impactGroup}
                  </span>
                  {getImpactBadge(item.impactType)}
                </div>

                {/* Cause */}
                <div className="space-y-1">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">⚡ NGUYÊN NHÂN (TÁC ĐỘNG VĨ MÔ)</div>
                  <h3 className="text-lg font-bold text-slate-100 leading-snug">
                    {item.cause}
                  </h3>
                </div>

                {/* Effect */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                  <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">🎯 KẾT QUẢ ĐẦU RA</div>
                  <div className="text-base font-bold text-slate-200">
                    {item.effect}
                  </div>
                </div>

                {/* Detail */}
                <p className="text-slate-300 text-base leading-relaxed pt-1">
                  {item.detail}
                </p>

                {/* Real Example */}
                {item.realExample && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm font-medium leading-relaxed">
                    {item.realExample}
                  </div>
                )}
              </div>
            </div>
          ))}

          {filteredItems.length === 0 && (
            <div className="col-span-full py-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400 space-y-3">
              <Compass className="w-10 h-10 mx-auto text-slate-500" />
              <p className="text-lg font-semibold">Không tìm thấy kịch bản phù hợp với từ khóa tìm kiếm.</p>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSelectedImpact('all');
                }}
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-xl text-sm"
              >
                Xóa bộ lọc
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
