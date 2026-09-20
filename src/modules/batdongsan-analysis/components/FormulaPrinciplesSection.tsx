'use client';

import React from 'react';
import { FORMULA_PRINCIPLES_DATA } from '../data/constants';
import { Scale, Calculator, CheckCircle2, Clock, Split, Award } from 'lucide-react';
import { SpeakerButton } from './SpeakerButton';

export const FormulaPrinciplesSection: React.FC = () => {
  return (
    <section id="principles" className="py-12 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold text-sm">
            <Scale className="w-4 h-4" /> ĐỊNH GIÁ & NGUYÊN TẮC VÀNG
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            4. Công Thức Định Giá Cốt Lõi & 4 Nguyên Tắc Thực Chiến
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Công thức nền tảng giúp tháo gỡ cảm xúc bốc đồng khi giao dịch và 4 quy luật bất biến của dòng tiền bất động sản trong mọi giai đoạn chu kỳ.
          </p>
        </div>

        {/* Core Formula Visual Card */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/40 border border-amber-500/40 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
            <Calculator className="w-64 h-64 text-amber-400" />
          </div>

          <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3 text-amber-400 font-bold text-lg">
              <Calculator className="w-6 h-6" />
              <span>CÔNG THỨC CỐT LÕI ĐỊNH GIÁ BẤT ĐỘNG SẢN</span>
            </div>
            <SpeakerButton text="Công thức định giá cốt lõi: Giá Bất động sản bằng Giá trị sử dụng cộng Kỳ vọng tương lai cộng Chi phí tài chính. Giá trị sử dụng thực bao gồm khả năng ở thực tế và dòng tiền khai thác. Kỳ vọng tương lai bao gồm quy hoạch hạ tầng. Chi phí tài chính bao gồm lãi suất vay ngân hàng." />
          </div>

          {/* Formula Equation Banner */}
          <div className="p-6 rounded-2xl bg-slate-950/90 border border-amber-500/30 text-center space-y-4 shadow-inner">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">
              CÔNG THỨC ĐỊNH GIÁ THỰC TẾ
            </div>
            <div className="text-xl sm:text-3xl font-black text-amber-300 tracking-wide font-mono leading-tight">
              GIÁ BĐS = GIÁ TRỊ SỬ DỤNG + KỲ VỌNG TƯƠNG LAI + CHI PHÍ TÀI CHÍNH
            </div>
          </div>

          {/* 3 Components Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            {/* Component 1 */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-base font-bold text-emerald-400 flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-black text-sm">1</span>
                GIÁ TRỊ SỬ DỤNG THỰC
              </div>
              <p className="text-slate-300 text-base leading-relaxed">
                Khả năng ở thực tế, dòng tiền khai thác cho thuê (Shop, căn hộ), chất lượng môi trường sống và tiện ích hạ tầng hiện hữu xung quanh.
              </p>
            </div>

            {/* Component 2 */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-base font-bold text-cyan-400 flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-black text-sm">2</span>
                KỲ VỌNG TƯƠNG LAI
              </div>
              <p className="text-slate-300 text-base leading-relaxed">
                Tiềm năng từ quy hoạch đường mở rộng, công trình hạ tầng quốc gia hoàn thành, khả năng chuyển đổi mục đích sử dụng đất trong 3-5 năm tới.
              </p>
            </div>

            {/* Component 3 */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-base font-bold text-rose-400 flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center font-black text-sm">3</span>
                CHI PHÍ TÀI CHÍNH
              </div>
              <p className="text-slate-300 text-base leading-relaxed">
                Lãi suất vay trả góp ngân hàng, kỳ vọng lợi nhuận bù đắp lạm phát và chi phí cơ hội nắm giữ tiền mặt của nhà đầu tư.
              </p>
            </div>
          </div>
        </div>

        {/* 4 Practical Principles Grid */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            <span>4 NGUYÊN TẮC THỰC CHIẾN BẤT BIẾN</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {FORMULA_PRINCIPLES_DATA.map((pr) => (
              <div
                key={pr.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      {pr.id === 'pr-1' && <Clock className="w-6 h-6" />}
                      {pr.id === 'pr-2' && <CheckCircle2 className="w-6 h-6" />}
                      {pr.id === 'pr-3' && <Scale className="w-6 h-6" />}
                      {pr.id === 'pr-4' && <Split className="w-6 h-6" />}
                    </div>
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <h4 className="text-lg font-bold text-slate-100">{pr.title}</h4>
                        <p className="text-xs font-semibold text-amber-400 mt-0.5">{pr.subtitle}</p>
                      </div>
                      <SpeakerButton text={`${pr.title}. ${pr.subtitle}. ${pr.description}. ${pr.bulletPoints.join('. ')}. ${pr.vividIllustration || ''}`} />
                    </div>
                  </div>

                  <p className="text-slate-300 text-base leading-relaxed">
                    {pr.description}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">LƯU Ý THỰC TẾ:</div>
                  <ul className="space-y-1.5">
                    {pr.bulletPoints.map((bp, bIdx) => (
                      <li key={bIdx} className="text-sm font-medium text-slate-200 flex items-start gap-2 leading-relaxed">
                        <span className="text-amber-400 mt-1">•</span>
                        <span>{bp}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {pr.vividIllustration && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm font-medium leading-relaxed">
                    {pr.vividIllustration}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
