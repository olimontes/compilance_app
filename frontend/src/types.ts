export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Organization = {
  uuid: string;
  name: string;
  slug: string;
};

export type AssessmentFramework = {
  uuid: string;
  code: string;
  name: string;
  version: string;
  status: string;
};

export type Assessment = {
  uuid: string;
  organization: string;
  framework: string;
  created_by: string;
  title: string;
  status: "draft" | "in_progress" | "submitted" | "archived";
  started_at: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type QuestionnaireQuestion = {
  uuid: string;
  code: string;
  text: string;
  answer_type: "boolean" | "choice" | "number" | "text" | "json";
  weight: string;
  is_required: boolean;
  is_required_descriptive: boolean;
  display_order: number;
};

export type QuestionnaireDimension = {
  uuid: string;
  code: string;
  name: string;
  description: string;
  display_order: number;
  questions: QuestionnaireQuestion[];
};

export type Questionnaire = {
  framework: {
    uuid: string;
    code: string;
    version: string;
    name: string;
  };
  dimensions: QuestionnaireDimension[];
};

export type AssessmentAnswer = {
  uuid: string;
  assessment: string;
  question: string;
  value: unknown;
  score: string | null;
  notes: string;
};

export type AssessmentSummary = {
  uuid: string;
  title: string;
  status: Assessment["status"];
  submitted_at: string | null;
  overall_score: ScorePayload | null;
  dimensions: Array<
    ScorePayload & {
      dimension: {
        uuid: string;
        code: string;
        name: string;
      };
    }
  >;
  recommendations: Array<{
    uuid: string;
    dimension: string | null;
    title: string;
    description: string;
    priority: string;
    status: string;
  }>;
};

export type ScorePayload = {
  score: string;
  max_score: string;
  percentage: string;
  computed_at: string;
};

export type ExecutiveReport = {
  assessment: {
    uuid: string;
    title: string;
    status: string;
    submitted_at: string | null;
  };
  executive_summary: {
    headline: string;
    overall_score: ScorePayload | null;
    maturity_level: string;
    identified_risk_count: number;
    priority_risk_count: number;
    recommended_focus: Array<{
      dimension: string;
      name: string;
      maturity_percentage: string;
      severity: string;
    }>;
  };
  identified_risks: Array<{
    uuid: string | null;
    title: string;
    dimension: {
      uuid: string;
      code: string;
      name: string;
    };
    maturity_percentage: string;
    likelihood: number;
    impact: number;
    severity: string;
    status: string;
    consequences: {
      legal: string;
      financial: string;
      operational: string;
      reputational: string;
    };
  }>;
  mitigation_plan: Array<{
    uuid: string | null;
    title: string;
    status: string;
    due_date: string | null;
    suggested_deadline: string | null;
    objective: string;
    justification: string;
    expected_benefits: string[];
    complexity: string;
    impacted_areas: string[];
    success_indicators: string[];
    expected_evidence: string[];
    items: Array<{
      uuid: string | null;
      title: string;
      status: string;
      due_date: string | null;
    }>;
  }>;
  recommended_next_steps: string[];
};
