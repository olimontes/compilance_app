import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ApiCredentials,
  ApiError,
  createAssessment,
  generateMitigationPlan,
  getExecutiveReport,
  getQuestionnaire,
  getSummary,
  hasCredentials,
  listAnswers,
  listAssessments,
  listFrameworks,
  listOrganizations,
  saveAnswer,
  submitAssessment
} from "./api";
import type {
  Assessment,
  AssessmentAnswer,
  AssessmentFramework,
  AssessmentSummary,
  ExecutiveReport,
  Organization,
  Questionnaire,
  QuestionnaireQuestion
} from "./types";

type Tab = "questionnaire" | "summary" | "report";
type AnswerDraft = string | boolean;

const emptyCredentials: ApiCredentials = {
  username: "",
  password: ""
};

function App() {
  const [credentials, setCredentials] = useState<ApiCredentials>(emptyCredentials);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [frameworks, setFrameworks] = useState<AssessmentFramework[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedAssessmentUuid, setSelectedAssessmentUuid] = useState<string>("");
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null);
  const [answers, setAnswers] = useState<AssessmentAnswer[]>([]);
  const [summary, setSummary] = useState<AssessmentSummary | null>(null);
  const [report, setReport] = useState<ExecutiveReport | null>(null);
  const [answerDrafts, setAnswerDrafts] = useState<Record<string, AnswerDraft>>({});
  const [activeTab, setActiveTab] = useState<Tab>("questionnaire");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [newAssessment, setNewAssessment] = useState({
    title: "",
    organization: "",
    framework: ""
  });

  const selectedAssessment = assessments.find((assessment) => assessment.uuid === selectedAssessmentUuid) ?? null;
  const answersByQuestion = useMemo(() => {
    return new Map(answers.map((answer) => [answer.question, answer]));
  }, [answers]);

  useEffect(() => {
    if (!hasCredentials(credentials)) {
      return;
    }
    void loadWorkspace();
  }, []);

  useEffect(() => {
    if (!selectedAssessment || !hasCredentials(credentials)) {
      setQuestionnaire(null);
      setAnswers([]);
      setSummary(null);
      setReport(null);
      return;
    }

    void loadAssessmentDetails(selectedAssessment);
  }, [selectedAssessmentUuid]);

  async function loadWorkspace() {
    if (!hasCredentials(credentials)) {
      setError("Informe usuario e senha para carregar o workspace.");
      return;
    }

    setIsLoading(true);
    setError("");
    setMessage("");

    try {
      const [organizationPage, frameworkPage, assessmentPage] = await Promise.all([
        listOrganizations(credentials),
        listFrameworks(credentials),
        listAssessments(credentials)
      ]);

      setOrganizations(organizationPage.results);
      setFrameworks(frameworkPage.results);
      setAssessments(assessmentPage.results);
      setNewAssessment((current) => ({
        title: current.title,
        organization: current.organization || organizationPage.results[0]?.uuid || "",
        framework: current.framework || frameworkPage.results[0]?.uuid || ""
      }));

      if (!selectedAssessmentUuid && assessmentPage.results.length > 0) {
        setSelectedAssessmentUuid(assessmentPage.results[0].uuid);
      }

      setMessage("Workspace carregado.");
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  async function loadAssessmentDetails(assessment: Assessment) {
    setIsLoading(true);
    setError("");
    setMessage("");
    setQuestionnaire(null);
    setSummary(null);
    setReport(null);

    try {
      const [questionnairePayload, answerPage, summaryPayload] = await Promise.all([
        getQuestionnaire(credentials, assessment.uuid),
        listAnswers(credentials),
        getSummary(credentials, assessment.uuid)
      ]);
      const assessmentAnswers = answerPage.results.filter((answer) => answer.assessment === assessment.uuid);

      setQuestionnaire(questionnairePayload);
      setAnswers(assessmentAnswers);
      setSummary(summaryPayload);
      setAnswerDrafts(buildDrafts(assessmentAnswers));

      if (assessment.status === "submitted") {
        try {
          setReport(await getExecutiveReport(credentials, assessment.uuid));
        } catch {
          setReport(null);
        }
      }
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCredentialsSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadWorkspace();
  }

  async function handleCreateAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newAssessment.title.trim()) {
      setError("Informe um titulo para o assessment.");
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const created = await createAssessment(credentials, {
        title: newAssessment.title.trim(),
        organization: newAssessment.organization,
        framework: newAssessment.framework
      });
      setAssessments((current) => [created, ...current]);
      setSelectedAssessmentUuid(created.uuid);
      setNewAssessment((current) => ({ ...current, title: "" }));
      setMessage("Assessment criado.");
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSaveAnswer(question: QuestionnaireQuestion) {
    if (!selectedAssessment) {
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const existingAnswer = answersByQuestion.get(question.uuid);
      const saved = await saveAnswer(credentials, existingAnswer, {
        assessment: selectedAssessment.uuid,
        question: question.uuid,
        value: buildAnswerValue(question, answerDrafts[question.uuid])
      });
      setAnswers((current) => {
        const withoutSaved = current.filter((answer) => answer.uuid !== saved.uuid);
        return [...withoutSaved, saved];
      });
      setMessage(`Resposta salva: ${question.code}.`);
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSubmitAssessment() {
    if (!selectedAssessment) {
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const submittedSummary = await submitAssessment(credentials, selectedAssessment.uuid);
      setSummary(submittedSummary);
      setAssessments((current) =>
        current.map((assessment) =>
          assessment.uuid === selectedAssessment.uuid
            ? {
                ...assessment,
                status: "submitted",
                submitted_at: submittedSummary.submitted_at
              }
            : assessment
        )
      );
      setActiveTab("summary");
      setMessage("Assessment submetido e score recalculado.");
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleGenerateMitigation() {
    if (!selectedAssessment) {
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      await generateMitigationPlan(credentials, selectedAssessment.uuid);
      setReport(await getExecutiveReport(credentials, selectedAssessment.uuid));
      setActiveTab("report");
      setMessage("Plano de mitigacao gerado e relatorio atualizado.");
    } catch (caughtError) {
      setError(readError(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Governance API</p>
          <h1>Assessment e relatorio executivo</h1>
        </div>
        <form className="credentials" onSubmit={handleCredentialsSubmit}>
          <label>
            Usuario
            <input
              value={credentials.username}
              autoComplete="username"
              onChange={(event) => setCredentials({ ...credentials, username: event.target.value })}
              placeholder="admin"
            />
          </label>
          <label>
            Senha
            <input
              value={credentials.password}
              type="password"
              autoComplete="current-password"
              onChange={(event) => setCredentials({ ...credentials, password: event.target.value })}
              placeholder="senha"
            />
          </label>
          <button type="submit" disabled={isLoading}>
            Conectar
          </button>
        </form>
      </header>

      {(error || message) && (
        <section className={error ? "notice error" : "notice success"} aria-live="polite">
          {error || message}
        </section>
      )}

      <section className="workspace">
        <aside className="sidebar">
          <form className="new-assessment" onSubmit={handleCreateAssessment}>
            <h2>Novo assessment</h2>
            <input
              value={newAssessment.title}
              onChange={(event) => setNewAssessment({ ...newAssessment, title: event.target.value })}
              placeholder="Titulo do assessment"
            />
            <select
              value={newAssessment.organization}
              onChange={(event) => setNewAssessment({ ...newAssessment, organization: event.target.value })}
            >
              {organizations.map((organization) => (
                <option key={organization.uuid} value={organization.uuid}>
                  {organization.name}
                </option>
              ))}
            </select>
            <select
              value={newAssessment.framework}
              onChange={(event) => setNewAssessment({ ...newAssessment, framework: event.target.value })}
            >
              {frameworks.map((framework) => (
                <option key={framework.uuid} value={framework.uuid}>
                  {framework.code} v{framework.version}
                </option>
              ))}
            </select>
            <button type="submit" disabled={isSaving || !organizations.length || !frameworks.length}>
              Criar
            </button>
          </form>

          <div className="assessment-list">
            <div className="section-heading">
              <h2>Assessments</h2>
              <button type="button" onClick={() => void loadWorkspace()} disabled={isLoading}>
                Atualizar
              </button>
            </div>
            {assessments.length === 0 ? (
              <p className="empty-state">Nenhum assessment encontrado para este usuario.</p>
            ) : (
              assessments.map((assessment) => (
                <button
                  type="button"
                  key={assessment.uuid}
                  className={
                    assessment.uuid === selectedAssessmentUuid ? "assessment-item active" : "assessment-item"
                  }
                  onClick={() => setSelectedAssessmentUuid(assessment.uuid)}
                >
                  <span>{assessment.title}</span>
                  <small>{statusLabel(assessment.status)}</small>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="content-panel">
          {selectedAssessment ? (
            <>
              <div className="content-header">
                <div>
                  <p className="eyebrow">{statusLabel(selectedAssessment.status)}</p>
                  <h2>{selectedAssessment.title}</h2>
                </div>
                <div className="header-actions">
                  <button type="button" onClick={handleSubmitAssessment} disabled={isSaving}>
                    Submeter
                  </button>
                  <button
                    type="button"
                    onClick={handleGenerateMitigation}
                    disabled={isSaving || selectedAssessment.status !== "submitted"}
                  >
                    Gerar mitigacao
                  </button>
                </div>
              </div>

              <nav className="tabs" aria-label="Views do assessment">
                <button
                  type="button"
                  className={activeTab === "questionnaire" ? "active" : ""}
                  onClick={() => setActiveTab("questionnaire")}
                >
                  Questionario
                </button>
                <button
                  type="button"
                  className={activeTab === "summary" ? "active" : ""}
                  onClick={() => setActiveTab("summary")}
                >
                  Resumo
                </button>
                <button
                  type="button"
                  className={activeTab === "report" ? "active" : ""}
                  onClick={() => setActiveTab("report")}
                >
                  Relatorio
                </button>
              </nav>

              {isLoading ? <p className="empty-state">Carregando dados...</p> : null}
              {!isLoading && activeTab === "questionnaire" ? renderQuestionnaire() : null}
              {!isLoading && activeTab === "summary" ? <SummaryView summary={summary} /> : null}
              {!isLoading && activeTab === "report" ? <ReportView report={report} /> : null}
            </>
          ) : (
            <div className="empty-panel">
              <h2>Conecte na API para carregar os assessments</h2>
              <p>Use um usuario Django com membership ativo na organizacao.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );

  function renderQuestionnaire() {
    if (!questionnaire) {
      return <p className="empty-state">Questionario indisponivel.</p>;
    }

    return (
      <div className="questionnaire">
        {questionnaire.dimensions.map((dimension) => (
          <section className="dimension-block" key={dimension.uuid}>
            <div className="dimension-title">
              <div>
                <h3>{dimension.name}</h3>
                <p>{dimension.description}</p>
              </div>
              <span>{dimension.questions.length} perguntas</span>
            </div>
            <div className="question-list">
              {dimension.questions.map((question) => (
                <article className="question-card" key={question.uuid}>
                  <div>
                    <strong>{question.code}</strong>
                    <p>{question.text}</p>
                    {question.is_required_descriptive ? <small>Descricao obrigatoria</small> : null}
                  </div>
                  <AnswerControl
                    question={question}
                    value={answerDrafts[question.uuid]}
                    onChange={(value) =>
                      setAnswerDrafts((current) => ({
                        ...current,
                        [question.uuid]: value
                      }))
                    }
                    onSave={() => void handleSaveAnswer(question)}
                    disabled={isSaving}
                  />
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    );
  }
}

function AnswerControl({
  question,
  value,
  onChange,
  onSave,
  disabled
}: {
  question: QuestionnaireQuestion;
  value: AnswerDraft | undefined;
  onChange: (value: AnswerDraft) => void;
  onSave: () => void;
  disabled: boolean;
}) {
  if (question.answer_type === "boolean") {
    return (
      <div className="answer-control compact">
        <div className="segmented">
          <button
            type="button"
            className={value === true ? "active" : ""}
            onClick={() => onChange(true)}
            disabled={disabled}
          >
            Sim
          </button>
          <button
            type="button"
            className={value === false ? "active" : ""}
            onClick={() => onChange(false)}
            disabled={disabled}
          >
            Nao
          </button>
        </div>
        <button type="button" onClick={onSave} disabled={disabled || typeof value !== "boolean"}>
          Salvar
        </button>
      </div>
    );
  }

  if (question.answer_type === "choice") {
    return (
      <div className="answer-control">
        <select value={String(value ?? "")} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
          <option value="">Selecione</option>
          <option value="yes">Sim</option>
          <option value="partial">Parcial</option>
          <option value="no">Nao</option>
        </select>
        <button type="button" onClick={onSave} disabled={disabled || !value}>
          Salvar
        </button>
      </div>
    );
  }

  return (
    <div className="answer-control">
      <textarea
        value={String(value ?? "")}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Resposta"
        disabled={disabled}
      />
      <button type="button" onClick={onSave} disabled={disabled || !String(value ?? "").trim()}>
        Salvar
      </button>
    </div>
  );
}

function SummaryView({ summary }: { summary: AssessmentSummary | null }) {
  if (!summary) {
    return <p className="empty-state">Resumo ainda indisponivel.</p>;
  }

  return (
    <div className="summary-grid">
      <section className="score-panel">
        <p className="eyebrow">Score geral</p>
        <strong>{summary.overall_score ? `${summary.overall_score.percentage}%` : "Sem score"}</strong>
        {summary.overall_score ? (
          <div className="meter">
            <span style={{ width: `${Math.min(Number(summary.overall_score.percentage), 100)}%` }} />
          </div>
        ) : null}
      </section>

      <section className="table-panel">
        <h3>Dimensoes</h3>
        <div className="rows">
          {summary.dimensions.map((dimension) => (
            <div className="data-row" key={dimension.dimension.uuid}>
              <span>{dimension.dimension.name}</span>
              <strong>{dimension.percentage}%</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="table-panel">
        <h3>Recomendacoes</h3>
        <div className="rows">
          {summary.recommendations.length ? (
            summary.recommendations.map((recommendation) => (
              <div className="data-row stacked" key={recommendation.uuid}>
                <span>{recommendation.title}</span>
                <small>
                  {recommendation.priority} - {recommendation.status}
                </small>
              </div>
            ))
          ) : (
            <p className="empty-state">Nenhuma recomendacao gerada.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function ReportView({ report }: { report: ExecutiveReport | null }) {
  if (!report) {
    return <p className="empty-state">Relatorio disponivel apos submissao e geracao do plano de mitigacao.</p>;
  }

  return (
    <div className="report-view">
      <section className="report-summary">
        <p className="eyebrow">Resumo executivo</p>
        <h3>{report.executive_summary.headline}</h3>
        <div className="kpi-row">
          <Metric label="Maturidade" value={report.executive_summary.maturity_level} />
          <Metric label="Riscos" value={String(report.executive_summary.identified_risk_count)} />
          <Metric label="Prioritarios" value={String(report.executive_summary.priority_risk_count)} />
        </div>
      </section>

      <section className="table-panel">
        <h3>Riscos identificados</h3>
        <div className="risk-list">
          {report.identified_risks.map((risk) => (
            <article className="risk-card" key={`${risk.dimension.code}-${risk.title}`}>
              <div className="risk-heading">
                <div>
                  <strong>{risk.title}</strong>
                  <small>{risk.dimension.name}</small>
                </div>
                <span className={`severity ${risk.severity}`}>{risk.severity}</span>
              </div>
              <div className="consequence-grid">
                <p>
                  <b>Legal:</b> {risk.consequences.legal}
                </p>
                <p>
                  <b>Financeiro:</b> {risk.consequences.financial}
                </p>
                <p>
                  <b>Operacional:</b> {risk.consequences.operational}
                </p>
                <p>
                  <b>Reputacional:</b> {risk.consequences.reputational}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="table-panel">
        <h3>Plano de mitigacao</h3>
        <div className="plan-list">
          {report.mitigation_plan.map((plan) => (
            <article className="plan-card" key={`${plan.title}-${plan.suggested_deadline}`}>
              <div className="risk-heading">
                <div>
                  <strong>{plan.title}</strong>
                  <small>
                    {plan.complexity} - prazo sugerido {plan.suggested_deadline ?? "a definir"}
                  </small>
                </div>
                <span>{plan.status}</span>
              </div>
              <p>{plan.objective}</p>
              <ListBlock title="Indicadores" values={plan.success_indicators} />
              <ListBlock title="Evidencias" values={plan.expected_evidence} />
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ListBlock({ title, values }: { title: string; values: string[] }) {
  return (
    <div className="list-block">
      <span>{title}</span>
      <ul>
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}

function buildDrafts(answers: AssessmentAnswer[]) {
  return answers.reduce<Record<string, AnswerDraft>>((drafts, answer) => {
    drafts[answer.question] = answerValueToDraft(answer.value);
    return drafts;
  }, {});
}

function answerValueToDraft(value: unknown): AnswerDraft {
  if (typeof value === "boolean" || typeof value === "string") {
    return value;
  }
  if (isRecord(value)) {
    if (typeof value.answer === "boolean" || typeof value.answer === "string") {
      return value.answer;
    }
    if (typeof value.text === "string") {
      return value.text;
    }
    if (typeof value.description === "string") {
      return value.description;
    }
  }
  return "";
}

function buildAnswerValue(question: QuestionnaireQuestion, value: AnswerDraft | undefined) {
  if (question.answer_type === "boolean") {
    return { answer: value === true };
  }
  if (question.answer_type === "choice") {
    return { answer: String(value ?? "") };
  }
  if (question.answer_type === "number") {
    return { score: Number(value ?? 0) };
  }
  return { text: String(value ?? "").trim() };
}

function statusLabel(status: Assessment["status"] | string) {
  const labels: Record<string, string> = {
    draft: "Rascunho",
    in_progress: "Em andamento",
    submitted: "Submetido",
    archived: "Arquivado"
  };
  return labels[status] ?? status;
}

function readError(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Erro inesperado.";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

export default App;
