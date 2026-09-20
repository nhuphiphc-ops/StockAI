export type ImpactType = 'increase' | 'decrease' | 'freeze';

export interface CauseEffectItem {
  id: string;
  cause: string;
  effect: string;
  impactType: ImpactType;
  impactGroup: string;
  detail: string;
  realExample?: string; // Ví dụ sống động thực tế lịch sử / thị trường
}

export interface FactorDetail {
  name: string;
  bullScenario: string;
  bullImpact: string;
  bearScenario: string;
  bearImpact: string;
  impactedSegments: string[];
  realCaseStudy?: string; // Bài học thực chiến / Ví dụ minh họa thực tế
}

export interface FactorGroup {
  id: string;
  title: string;
  iconName: string;
  description: string;
  factors: FactorDetail[];
}

export interface SegmentItem {
  id: string;
  title: string;
  subtitle: string;
  iconName: string;
  sensitivity: string;
  keyDrivers: string[];
  riskLevel: 'Thấp' | 'Trung bình' | 'Cao' | 'Rất cao';
  summary: string;
  strategicAdvice: string;
  historicalCase?: string; // Ví dụ thực tế lịch sử phân khúc
}

export interface PrincipleItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  bulletPoints: string[];
  vividIllustration?: string; // Minh họa sống động thực tế
}

export interface IndicatorMetric {
  id: string;
  name: string;
  normalVal: string;
  warningVal: string;
  dangerVal: string;
  realEstateImpact: string;
  historicalCase?: string; // Ví dụ lịch sử chỉ số
}

export interface CrisisStage {
  stageNumber: number;
  stageTitle: string;
  timeHorizon: string;
  description: string;
  keySignals: string[];
  historicalExample?: string; // Ví dụ thực tế giai đoạn
}

export type RiskLevel = 'normal' | 'warning' | 'high' | 'crisis';

export interface ActionMatrixLevel {
  level: RiskLevel;
  levelName: string;
  badgeColor: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  description: string;
  actionStrategy: string[];
  vividStrategyExample?: string; // Ví dụ hành động thực chiến
}

export interface TransmissionChannel {
  id: string;
  channelTitle: string;
  iconName: string;
  description: string;
  realEstateConsequence: string;
  vividExample?: string; // Minh họa kênh truyền dẫn thực tế
}

export interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
}

export type TrendDirection = 'up' | 'down' | 'flat';
export type MonitorRiskLevel = 'green' | 'yellow' | 'orange' | 'red';

export interface MonitorMetric {
  id: string;
  name: string;
  currentValue: string;
  trend: TrendDirection;
  riskLevel: MonitorRiskLevel;
  macroConclusion: string;
  actionSuggestion: string;
  lastUpdated: string;
  realWorldContext?: string; // Bối cảnh thực tế thời điểm
}
