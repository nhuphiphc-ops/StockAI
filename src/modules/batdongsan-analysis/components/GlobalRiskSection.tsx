'use client';

import React, { useState, useEffect } from 'react';
import { GLOBAL_CRISIS_DATA } from '../data/constants';
import { ChecklistItem } from '../types';
import { SpeakerButton } from './SpeakerButton';
import {
  Globe2,
  AlertTriangle,
  Activity,
  GitCommit,
  Shield,
  ArrowRightLeft,
  CheckSquare,
  Square,
  RotateCcw,
} from 'lucide-react';

const LOCAL_CHECKLIST_KEY = 'bds_global_crisis_checklist_v1';

export const GlobalRiskSection: React.FC = () => {
  const [checklist, setChecklist] = useState<ChecklistItem[]>(GLOBAL_CRISIS_DATA.defaultChecklist);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  // Sync state with LocalStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LOCAL_CHECKLIST_KEY);
      if (saved) {
        setChecklist(JSON.parse(saved));
      }
    } catch (e) {
      console.error('Error loading checklist from localStorage:', e);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  const toggleChecklist = (id: string) => {
    const updated = checklist.map((item) =>
      item.id === id ? { ...item, checked: !item.checked } : item
    );
    setChecklist(updated);
    try {
      localStorage.setItem(LOCAL_CHECKLIST_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Error saving checklist to localStorage:', e);
    }
  };

  const resetChecklist = () => {
    setChecklist(GLOBAL_CRISIS_DATA.defaultChecklist);
    try {
      localStorage.setItem(LOCAL_CHECKLIST_KEY, JSON.stringify(GLOBAL_CRISIS_DATA.defaultChecklist));
    } catch (e) {
      console.error('Error resetting checklist:', e);
    }
  };

  const checkedCount = checklist.filter((item) => item.checked).length;
  const riskPercentage = Math.round((checkedCount / checklist.length) * 100);

  const getRiskStatusBadge = () => {
    if (checkedCount <= 1) {
      return <span className="px-3.5 py-1.5 rounded-full text-sm font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">AN TOÀN (Ít rủi ro)</span>;
    } else if (checkedCount <= 3) {
      return <span className="px-3.5 py-1.5 rounded-full text-sm font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40">CẢNH BÁO (Cần phòng thủ)</span>;
    } else if (checkedCount <= 4) {
      return <span className="px-3.5 py-1.5 rounded-full text-sm font-bold bg-orange-500/20 text-orange-400 border border-orange-500/40">NGUY CƠ CAO (Hạn chế nợ)</span>;
    } else {
      return <span className="px-3.5 py-1.5 rounded-full text-sm font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse">KHỦNG HOẢNG (Giữ tiền mặt)</span>;
    }
  };

  return (
    <section id="global-risk" className="py-12 border-b border-slate-800 space-y-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Main Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold text-sm">
            <Globe2 className="w-4 h-4" /> BÁO ĐỘNG KHỦNG HOẢNG KINH TẾ TOÀN CẦU
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            5. 🌍 Dấu Hiệu Khủng Hoảng Toàn Cầu & Kênh Tác Động Đến BĐS Việt Nam
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Trong nền kinh tế mở hội nhập sâu rộng, bất động sản Việt Nam không bao giờ đứng ngoài tác động của làn sóng chấn động vĩ mô quốc tế. Hệ thống hóa 6 khối phân tích nguy cơ khủng hoảng kinh tế toàn diện.
          </p>
        </div>

        {/* 7.1 Crisis Principle Banner */}
        <div className="bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border border-rose-500/40 rounded-3xl p-6 sm:p-8 space-y-4 shadow-2xl">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 text-rose-400 font-extrabold text-lg sm:text-xl">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <span>{GLOBAL_CRISIS_DATA.principleBanner.title}</span>
            </div>
            <SpeakerButton text={`${GLOBAL_CRISIS_DATA.principleBanner.title}. ${GLOBAL_CRISIS_DATA.principleBanner.description}`} />
          </div>
          <p className="text-slate-200 text-base leading-relaxed font-medium">
            {GLOBAL_CRISIS_DATA.principleBanner.description}
          </p>
        </div>

        {/* 7.2 Daily Alert Indicator Table */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-amber-400" />
              <span>7.2 BẢNG CHỈ SỐ BÁO ĐỘNG HÀNG NGÀY & NGƯỠNG RỦI RO</span>
            </h3>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 shadow-xl bg-slate-900">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-slate-950 text-slate-300 text-sm font-bold uppercase tracking-wider border-b border-slate-800">
                  <th className="p-4">Tên Chỉ Số Vĩ Mô</th>
                  <th className="p-4 text-emerald-400">Ngưỡng Bình Thường</th>
                  <th className="p-4 text-amber-400">Ngưỡng Cảnh Báo</th>
                  <th className="p-4 text-rose-400">Ngưỡng Nguy Cơ</th>
                  <th className="p-4">Tác Động Trực Tiếp BĐS Việt Nam</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-base">
                {GLOBAL_CRISIS_DATA.indicatorMetrics.map((ind) => (
                  <tr key={ind.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-bold text-slate-100">{ind.name}</td>
                    <td className="p-4 font-medium text-emerald-400 bg-emerald-950/10">{ind.normalVal}</td>
                    <td className="p-4 font-medium text-amber-400 bg-amber-950/10">{ind.warningVal}</td>
                    <td className="p-4 font-bold text-rose-400 bg-rose-950/10">{ind.dangerVal}</td>
                    <td className="p-4 text-slate-300 leading-relaxed text-sm space-y-1">
                      <div>{ind.realEstateImpact}</div>
                      {ind.historicalCase && (
                        <div className="text-xs text-amber-300 font-medium italic pt-1">{ind.historicalCase}</div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 7.3 4-Stage Crisis Timeline */}
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-cyan-400" />
            <span>7.3 CHUỖI DIỄN BIẾN KHỦNG HOẢNG TÍCH TỤ THEO 4 GIAI ĐOẠN</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {GLOBAL_CRISIS_DATA.stages.map((st) => (
              <div
                key={st.stageNumber}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between relative overflow-hidden"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center justify-center font-black text-sm">
                      0{st.stageNumber}
                    </span>
                    <div className="flex items-center gap-2">
                      <SpeakerButton text={`${st.stageTitle}. Khung thời gian: ${st.timeHorizon}. Mô tả: ${st.description}. Tín hiệu: ${st.keySignals.join(', ')}. ${st.historicalExample || ''}`} />
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider bg-slate-800 px-2.5 py-1 rounded-md">
                        {st.timeHorizon}
                      </span>
                    </div>
                  </div>

                  <h4 className="text-lg font-bold text-slate-100 leading-snug">{st.stageTitle}</h4>

                  <p className="text-sm text-slate-300 leading-relaxed">{st.description}</p>
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">TÍN HIỆU NHẬN BIẾT:</div>
                    <div className="space-y-1">
                      {st.keySignals.map((sig, sIdx) => (
                        <div key={sIdx} className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                          <span>{sig}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {st.historicalExample && (
                    <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium leading-relaxed">
                      {st.historicalExample}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 7.4 Action Matrix by Risk Level */}
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            <span>7.4 MA TRẬN 4 CẤP ĐỘ RỦI RO & KHUYẾN NGHỊ HÀNH ĐỘNG</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {GLOBAL_CRISIS_DATA.actionLevels.map((act) => (
              <div
                key={act.level}
                className={`${act.bgClass} border ${act.borderClass} rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className={`px-3 py-1 rounded-full text-xs font-extrabold border ${act.badgeColor}`}>
                      {act.levelName}
                    </span>
                    <SpeakerButton text={`${act.levelName}. Mô tả: ${act.description}. Chiến lược hành động: ${act.actionStrategy.join('. ')}. ${act.vividStrategyExample || ''}`} />
                  </div>
                  <p className="text-base font-semibold text-slate-200 leading-relaxed">
                    {act.description}
                  </p>
                </div>

                <div className="space-y-2 pt-3 border-t border-slate-800/60">
                  <div className={`text-xs font-bold uppercase tracking-wider ${act.textClass}`}>
                    STRATEGY: KHUYẾN NGHỊ HÀNH ĐỘNG TƯƠNG ỨNG
                  </div>
                  <ul className="space-y-1.5">
                    {act.actionStrategy.map((strat, stIdx) => (
                      <li key={stIdx} className="text-sm font-medium text-slate-200 flex items-start gap-2 leading-relaxed">
                        <span className={`${act.textClass} mt-1`}>•</span>
                        <span>{strat}</span>
                      </li>
                    ))}
                  </ul>

                  {act.vividStrategyExample && (
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium leading-relaxed mt-2">
                      {act.vividStrategyExample}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 7.5 Direct Transmission Channels into VN Real Estate */}
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-purple-400" />
            <span>7.5 4 KÊNH TRUYỀN DẪN TRỰC TIẾP VÀO BĐS VIỆT NAM</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {GLOBAL_CRISIS_DATA.transmissionChannels.map((tc) => (
              <div
                key={tc.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl"
              >
                <div className="flex items-center justify-between gap-3">
                  <h4 className="text-lg font-bold text-amber-300">{tc.channelTitle}</h4>
                  <SpeakerButton text={`${tc.channelTitle}. Mô tả: ${tc.description}. Hệ quả Bất động sản Việt Nam: ${tc.realEstateConsequence}. ${tc.vividExample || ''}`} />
                </div>
                <p className="text-base text-slate-300 leading-relaxed">{tc.description}</p>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">HỆ QUẢ TRỰC TIẾP BĐS VN:</div>
                  <p className="text-sm font-medium text-slate-200 leading-relaxed">{tc.realEstateConsequence}</p>
                  {tc.vividExample && (
                    <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium leading-relaxed mt-1">
                      {tc.vividExample}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 7.6 Interactive Early Warning Sign Checklist */}
        <div className="bg-slate-900 border border-amber-500/30 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <CheckSquare className="w-6 h-6 text-amber-400" />
                <span>7.6 CHECKLIST DẤU HIỆU CẢNH BÁO TỰ ĐỘNG TƯƠNG TÁC</span>
              </h3>
              <p className="text-sm text-slate-400">
                Đánh dấu các tín hiệu báo động hiện có trên thị trường. Trạng thái được lưu tự động vào bộ nhớ trình duyệt (LocalStorage).
              </p>
            </div>

            <div className="flex items-center gap-3 self-start sm:self-center">
              {getRiskStatusBadge()}
              <button
                onClick={resetChecklist}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-sm font-semibold transition-colors flex items-center gap-1.5"
                title="Reset về mặc định"
              >
                <RotateCcw className="w-4 h-4" />
                <span className="hidden sm:inline">Khôi phục</span>
              </button>
            </div>
          </div>

          {/* Risk Level Progress Indicator */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm font-semibold text-slate-300">
              <span>Chỉ số Cảnh báo Rủi ro Hiện tại:</span>
              <span className="font-bold text-amber-400">{checkedCount} / {checklist.length} tín hiệu ({riskPercentage}%)</span>
            </div>
            <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden p-0.5 border border-slate-800">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  riskPercentage > 65
                    ? 'bg-rose-500'
                    : riskPercentage > 45
                    ? 'bg-orange-500'
                    : riskPercentage > 25
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${riskPercentage}%` }}
              ></div>
            </div>
          </div>

          {/* Checklist Items Interactive List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {checklist.map((item) => (
              <div
                key={item.id}
                onClick={() => toggleChecklist(item.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex items-start gap-3.5 select-none ${
                  item.checked
                    ? 'bg-amber-950/30 border-amber-500/50 text-slate-100 shadow-md'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {item.checked ? (
                    <CheckSquare className="w-5 h-5 text-amber-400" />
                  ) : (
                    <Square className="w-5 h-5 text-slate-600" />
                  )}
                </div>
                <span className={`text-base font-medium leading-snug ${item.checked ? 'text-slate-100 font-semibold' : 'text-slate-300'}`}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
