import React from 'react';
import { SubNavbar } from '@/modules/batdongsan-analysis/components/SubNavbar';
import { CauseEffectSection } from '@/modules/batdongsan-analysis/components/CauseEffectSection';
import { FactorTabsSection } from '@/modules/batdongsan-analysis/components/FactorTabsSection';
import { SegmentCardsSection } from '@/modules/batdongsan-analysis/components/SegmentCardsSection';
import { FormulaPrinciplesSection } from '@/modules/batdongsan-analysis/components/FormulaPrinciplesSection';
import { GlobalRiskSection } from '@/modules/batdongsan-analysis/components/GlobalRiskSection';
import { LiveMonitorTable } from '@/modules/batdongsan-analysis/components/LiveMonitorTable';
import { Building2, Compass, ShieldCheck } from 'lucide-react';

export const metadata = {
  title: 'Tư Duy Thị Trường Bất Động Sản — Nhìn Nhận & Phân Tích Vĩ Mô',
  description: 'Hệ thống hóa mối liên hệ nhân - quả giữa vĩ mô, lãi suất, chu kỳ khủng hoảng và từng phân khúc tài sản bất động sản Việt Nam.',
};

export default function BatDongSanAnalysisPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-amber-500 selection:text-slate-950">
      {/* Top Hero Brand Header */}
      <header className="bg-slate-900 border-b border-slate-800 py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <Building2 className="w-8 h-8" />
            </div>
            <div>
              <div className="text-xs font-extrabold uppercase tracking-widest text-amber-400">
                CHUYÊN NGHÀNH VĨ MÔ & BẤT ĐỘNG SẢN VIỆT NAM
              </div>
              <h1 className="text-2xl sm:text-4xl font-black text-slate-100 tracking-tight leading-tight">
                Tư Duy Thị Trường Bất Động Sản — Nhìn Nhận & Phân Tích
              </h1>
            </div>
          </div>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed max-w-4xl">
            Hệ thống hóa mối liên hệ nhân - quả giữa vĩ mô, lãi suất, chu kỳ khủng hoảng kinh tế toàn cầu và vận hành thực tế của từng phân khúc tài sản bất động sản.
          </p>

          <div className="flex items-center gap-4 pt-2 text-xs font-semibold text-slate-400 flex-wrap">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <ShieldCheck className="w-4 h-4" /> Zero-Backend & LocalStorage Auto-Sync
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <Compass className="w-4 h-4" /> Chuẩn Vercel Deployment Ready
            </span>
          </div>
        </div>
      </header>

      {/* Sticky SubNavbar */}
      <SubNavbar />

      {/* Main Content Sections */}
      <main className="space-y-4">
        {/* Section 1: Cause Effect Matrix */}
        <CauseEffectSection />

        {/* Section 2: 4 Factor Groups */}
        <FactorTabsSection />

        {/* Section 3: 4 Real Estate Segments */}
        <SegmentCardsSection />

        {/* Section 4: Valuation Formula & 4 Gold Rules */}
        <FormulaPrinciplesSection />

        {/* Section 5: Global Economic Crisis Signs (7.1 to 7.6) */}
        <GlobalRiskSection />

        {/* Section 6: Live Market Monitor Table */}
        <LiveMonitorTable />
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-10 text-center text-slate-400 text-sm space-y-2">
        <p className="font-semibold text-slate-300">
          © 2026 Antigravity Real Estate Architecture Terminal. All rights reserved.
        </p>
        <p className="text-xs text-slate-500 max-w-2xl mx-auto px-4">
          Dữ liệu phân tích mang tính chất hệ thống hóa tư duy đầu tư. Nhà đầu tư cần chủ động nghiên cứu pháp lý và cân đối dòng tiền cá nhân trước khi ra quyết định.
        </p>
      </footer>
    </div>
  );
}
