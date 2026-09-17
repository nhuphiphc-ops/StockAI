export type ImpactType = 'increase' | 'decrease' | 'freeze';

export interface CauseEffectItem {
  id: string;
  cause: string;
  effect: string;
  impactType: ImpactType;
  impactGroup: string;
  detail: string;
}

export interface FactorDetail {
  name: string;
  bullScenario: string;
  bullImpact: string;
  bearScenario: string;
  bearImpact: string;
  impactedSegments: string[];
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
}

export interface PrincipleItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  bulletPoints: string[];
}

export interface IndicatorMetric {
  id: string;
  name: string;
  normalVal: string;
  warningVal: string;
  dangerVal: string;
  realEstateImpact: string;
}

export interface CrisisStage {
  stageNumber: number;
  stageTitle: string;
  timeHorizon: string;
  description: string;
  keySignals: string[];
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
}

export interface TransmissionChannel {
  id: string;
  channelTitle: string;
  iconName: string;
  description: string;
  realEstateConsequence: string;
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
}
