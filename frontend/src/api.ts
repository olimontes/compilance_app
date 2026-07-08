import type {
  Assessment,
  AssessmentAnswer,
  AssessmentFramework,
  AssessmentSummary,
  ExecutiveReport,
  Organization,
  PaginatedResponse,
  Questionnaire
} from "./types";

export type ApiCredentials = {
  username: string;
  password: string;
};

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export function hasCredentials(credentials: ApiCredentials) {
  return Boolean(credentials.username.trim() && credentials.password);
}

export async function listOrganizations(credentials: ApiCredentials) {
  return request<PaginatedResponse<Organization>>("/organizations/", credentials);
}

export async function listFrameworks(credentials: ApiCredentials) {
  return request<PaginatedResponse<AssessmentFramework>>("/assessment-frameworks/", credentials);
}

export async function listAssessments(credentials: ApiCredentials) {
  return request<PaginatedResponse<Assessment>>("/assessments/", credentials);
}

export async function createAssessment(
  credentials: ApiCredentials,
  payload: { organization: string; framework: string; title: string }
) {
  return request<Assessment>("/assessments/", credentials, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getQuestionnaire(credentials: ApiCredentials, assessmentUuid: string) {
  return request<Questionnaire>(`/assessments/${assessmentUuid}/questionnaire/`, credentials);
}

export async function listAnswers(credentials: ApiCredentials) {
  return request<PaginatedResponse<AssessmentAnswer>>("/assessment-answers/", credentials);
}

export async function saveAnswer(
  credentials: ApiCredentials,
  existingAnswer: AssessmentAnswer | undefined,
  payload: { assessment: string; question: string; value: unknown }
) {
  if (existingAnswer) {
    return request<AssessmentAnswer>(`/assessment-answers/${existingAnswer.uuid}/`, credentials, {
      method: "PATCH",
      body: JSON.stringify({ value: payload.value })
    });
  }

  return request<AssessmentAnswer>("/assessment-answers/", credentials, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function submitAssessment(credentials: ApiCredentials, assessmentUuid: string) {
  return request<AssessmentSummary>(`/assessments/${assessmentUuid}/submit/`, credentials, {
    method: "POST"
  });
}

export async function generateMitigationPlan(credentials: ApiCredentials, assessmentUuid: string) {
  return request<unknown>(`/assessments/${assessmentUuid}/generate-mitigation-plan/`, credentials, {
    method: "POST"
  });
}

export async function getSummary(credentials: ApiCredentials, assessmentUuid: string) {
  return request<AssessmentSummary>(`/assessments/${assessmentUuid}/summary/`, credentials);
}

export async function getExecutiveReport(credentials: ApiCredentials, assessmentUuid: string) {
  return request<ExecutiveReport>(`/assessments/${assessmentUuid}/executive-report/`, credentials);
}

async function request<T>(path: string, credentials: ApiCredentials, init: RequestInit = {}) {
  if (!hasCredentials(credentials)) {
    throw new ApiError("Informe usuario e senha para consultar a API.", 0, null);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Authorization: `Basic ${btoa(`${credentials.username}:${credentials.password}`)}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers
    }
  });

  if (!response.ok) {
    const details = await parseResponse(response);
    throw new ApiError(errorMessage(details, response.status), response.status, details);
  }

  return parseResponse(response) as Promise<T>;
}

async function parseResponse(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function errorMessage(details: unknown, status: number) {
  if (typeof details === "string" && details.trim()) {
    return details;
  }
  if (isRecord(details) && typeof details.detail === "string") {
    return details.detail;
  }
  if (isRecord(details)) {
    return Object.entries(details)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
      .join(" | ");
  }
  return `Erro ${status} ao consultar a API.`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}
