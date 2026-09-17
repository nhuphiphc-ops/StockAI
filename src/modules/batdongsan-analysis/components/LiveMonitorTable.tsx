'use client';

import React, { useState, useEffect } from 'react';
import { MonitorMetric, TrendDirection, MonitorRiskLevel } from '../types';
import { INITIAL_MONITOR_METRICS } from '../data/constants';
import {
  Activity,
  Save,
  RotateCcw,
  Download,
  Edit3,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  X,
} from 'lucide-react';

const LOCAL_MONITOR_KEY = 'bds_live_monitor_metrics_v1';

export const LiveMonitorTable: React.FC = () => {
  const [metrics, setMetrics] = useState<MonitorMetric[]>(INITIAL_MONITOR_METRICS);
  const [isEditingModalOpen, setIsEditingModalOpen] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<MonitorMetric | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string>('');

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LOCAL_MONITOR_KEY);
      if (saved) {
        setMetrics(JSON.parse(saved));
      }
    } catch (e) {
      console.error('Error loading monitor metrics from localStorage:', e);
    }
  }, []);

  const saveToLocalStorage = (newMetrics: MonitorMetric[]) => {
    setMetrics(newMetrics);
    try {
      localStorage.setItem(LOCAL_MONITOR_KEY, JSON.stringify(newMetrics));
      showToast('Đã lưu dữ liệu vào LocalStorage thành công!');
    } catch (e) {
      console.error('Error saving metrics to localStorage:', e);
    }
  };

  const resetToDefault = () => {
    saveToLocalStorage(INITIAL_MONITOR_METRICS);
    showToast('Đã khôi phục dữ liệu mẫu ban đầu!');
  };

  const showToast = (msg: string) => {
    setSaveSuccessMsg(msg);
    setTimeout(() => setSaveSuccessMsg(''), 3000);
  };

  const handleOpenEditModal = (metric: MonitorMetric) => {
    setEditingItem({ ...metric });
    setIsEditingModalOpen(true);
  };

  const handleSaveModalItem = () => {
    if (!editingItem) return;
    const now = new Date();
    const dateStr = `${String(now.getDate()).padStart(2, '0')}/${String(now.getMonth() + 1).padStart(2, '0')}/${now.getFullYear()}`;
    
    const updated = metrics.map((m) =>
      m.id === editingItem.id ? { ...editingItem, lastUpdated: dateStr } : m
    );
    saveToLocalStorage(updated);
    setIsEditingModalOpen(false);
    setEditingItem(null);
  };

  // CSV Export with UTF-8 BOM
  const exportToCSV = () => {
    try {
      const headers = ['Mã ID', 'Tên Chỉ Số', 'Giá Trị Hiện Tại', 'Xu Hướng', 'Mức Rủi Ro', 'Kết Luận Vĩ Mô', 'Gợi Ý Hành Động', 'Ngày Cập Nhật'];
      
      const rows = metrics.map((m) => [
        `"${m.id}"`,
        `"${m.name.replace(/"/g, '""')}"`,
        `"${m.currentValue.replace(/"/g, '""')}"`,
        `"${m.trend === 'up' ? 'Tăng ⬆️' : m.trend === 'down' ? 'Giảm ⬇️' : 'Đi ngang ➡️'}"`,
        `"${m.riskLevel.toUpperCase()}"`,
        `"${m.macroConclusion.replace(/"/g, '""')}"`,
        `"${m.actionSuggestion.replace(/"/g, '""')}"`,
        `"${m.lastUpdated}"`,
      ]);

      const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `Bang_Theo_Doi_BDS_Vi%CC%A3t_Nam_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast('Đã xuất file CSV thành công!');
    } catch (e) {
      console.error('CSV Export Error:', e);
    }
  };

  const getRiskBadge = (risk: MonitorRiskLevel) => {
    switch (risk) {
      case 'green':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">AN TOÀN</span>;
      case 'yellow':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-500/20 text-amber-400 border border-amber-500/40">CẢNH BÁO</span>;
      case 'orange':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-orange-500/20 text-orange-400 border border-orange-500/40">NGUY CƠ</span>;
      case 'red':
        return <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-rose-500/20 text-rose-400 border border-rose-500/40">NGHIÊM TRỌNG</span>;
    }
  };

  const getTrendIcon = (trend: TrendDirection) => {
    switch (trend) {
      case 'up':
        return <span className="inline-flex items-center gap-1 text-emerald-400 font-bold"><TrendingUp className="w-4 h-4" /> Tăng</span>;
      case 'down':
        return <span className="inline-flex items-center gap-1 text-rose-400 font-bold"><TrendingDown className="w-4 h-4" /> Giảm</span>;
      case 'flat':
        return <span className="inline-flex items-center gap-1 text-cyan-400 font-bold"><Minus className="w-4 h-4" /> Đi ngang</span>;
    }
  };

  return (
    <section id="live-monitor" className="py-12 border-b border-slate-800 space-y-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold text-sm">
            <Activity className="w-4 h-4" /> THEO DÕI THỰC TẾ & TƯƠNG TÁC
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            6. Bảng Theo Dõi Chỉ Số Thị Trường Thực Tế (Live Monitor)
          </h2>
          <p className="text-slate-300 text-base leading-relaxed max-w-4xl">
            Cập nhật và theo dõi biến động các chỉ số thị trường cốt lõi. Cho phép chỉnh sửa số liệu thực tế, tự động đánh giá mức rủi ro và xuất dữ liệu báo cáo dạng CSV.
          </p>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900 p-4 sm:p-6 rounded-2xl border border-slate-800 shadow-xl">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-400">Trạng thái dữ liệu:</span>
            <span className="text-sm font-bold text-amber-400">Đã đồng bộ LocalStorage</span>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={() => saveToLocalStorage(metrics)}
              className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-colors flex items-center gap-2 shadow-lg"
            >
              <Save className="w-4 h-4" />
              <span>Lưu Cập Nhật</span>
            </button>

            <button
              onClick={exportToCSV}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 font-bold text-sm border border-slate-700 transition-colors flex items-center gap-2 shadow-md"
            >
              <Download className="w-4 h-4 text-cyan-400" />
              <span>Xuất File CSV</span>
            </button>

            <button
              onClick={resetToDefault}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 font-bold text-sm border border-slate-700 transition-colors flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Khôi Phục Mặc Định</span>
            </button>
          </div>
        </div>

        {/* Toast Message Notification */}
        {saveSuccessMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-semibold text-base flex items-center gap-2 animate-in fade-in duration-200">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{saveSuccessMsg}</span>
          </div>
        )}

        {/* Monitor Metrics Table */}
        <div className="overflow-x-auto rounded-2xl border border-slate-800 shadow-xl bg-slate-900">
          <table className="w-full text-left border-collapse min-w-[900px]">
            <thead>
              <tr className="bg-slate-950 text-slate-300 text-sm font-bold uppercase tracking-wider border-b border-slate-800">
                <th className="p-4">Chỉ Số Theo Dõi</th>
                <th className="p-4">Giá Trị Hiện Tại</th>
                <th className="p-4">Xu Hướng</th>
                <th className="p-4">Mức Rủi Ro</th>
                <th className="p-4">Kết Luận Vĩ Mô</th>
                <th className="p-4">Gợi Ý Hành Động</th>
                <th className="p-4 text-center">Thao Tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-base">
              {metrics.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 font-bold text-slate-100">{item.name}</td>
                  <td className="p-4 font-bold text-amber-300 font-mono whitespace-nowrap">{item.currentValue}</td>
                  <td className="p-4 font-medium whitespace-nowrap">{getTrendIcon(item.trend)}</td>
                  <td className="p-4 font-medium whitespace-nowrap">{getRiskBadge(item.riskLevel)}</td>
                  <td className="p-4 text-slate-300 text-sm leading-relaxed max-w-xs">{item.macroConclusion}</td>
                  <td className="p-4 text-slate-300 text-sm leading-relaxed max-w-xs">{item.actionSuggestion}</td>
                  <td className="p-4 text-center">
                    <button
                      onClick={() => handleOpenEditModal(item)}
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 transition-colors"
                      title="Chỉnh sửa chỉ số này"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Modal Inline Editor */}
        {isEditingModalOpen && editingItem && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative animate-in zoom-in-95 duration-200">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <h3 className="text-xl font-bold text-slate-100">Cập Nhật Chỉ Số Thực Tế</h3>
                <button
                  onClick={() => setIsEditingModalOpen(false)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 text-base">
                <div>
                  <label className="block text-sm font-semibold text-slate-400 mb-1">Tên chỉ số</label>
                  <input
                    type="text"
                    value={editingItem.name}
                    onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 font-semibold focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-400 mb-1">Giá trị hiện tại</label>
                    <input
                      type="text"
                      value={editingItem.currentValue}
                      onChange={(e) => setEditingItem({ ...editingItem, currentValue: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-amber-300 font-mono font-bold focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-400 mb-1">Xu hướng</label>
                    <select
                      value={editingItem.trend}
                      onChange={(e) => setEditingItem({ ...editingItem, trend: e.target.value as TrendDirection })}
                      className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 font-semibold focus:outline-none focus:border-amber-500"
                    >
                      <option value="up">Tăng ⬆️</option>
                      <option value="down">Giảm ⬇️</option>
                      <option value="flat">Đi ngang ➡️</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-400 mb-1">Mức độ Rủi ro</label>
                  <select
                    value={editingItem.riskLevel}
                    onChange={(e) => setEditingItem({ ...editingItem, riskLevel: e.target.value as MonitorRiskLevel })}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 font-semibold focus:outline-none focus:border-amber-500"
                  >
                    <option value="green">AN TOÀN (Xanh)</option>
                    <option value="yellow">CẢNH BÁO (Vàng)</option>
                    <option value="orange">NGUY CƠ (Cam)</option>
                    <option value="red">NGHIÊM TRỌNG (Đỏ)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-400 mb-1">Kết luận vĩ mô</label>
                  <textarea
                    rows={2}
                    value={editingItem.macroConclusion}
                    onChange={(e) => setEditingItem({ ...editingItem, macroConclusion: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 font-medium focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-400 mb-1">Gợi ý hành động</label>
                  <textarea
                    rows={2}
                    value={editingItem.actionSuggestion}
                    onChange={(e) => setEditingItem({ ...editingItem, actionSuggestion: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 font-medium focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-slate-800 pt-4">
                <button
                  onClick={() => setIsEditingModalOpen(false)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm"
                >
                  Hủy bỏ
                </button>
                <button
                  onClick={handleSaveModalItem}
                  className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  <span>Lưu Thay Đổi</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
