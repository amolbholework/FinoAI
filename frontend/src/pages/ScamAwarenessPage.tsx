import { useState } from 'react'
import { ScamAwarenessArt } from '../components/illustrations/ScamAwarenessArt'
import { scamTypes, whatToDoIfTargeted, reportingChannels, scamQuiz, type QuizQuestion } from '../mockdata/scamAwareness'

function ScamTypeCard({ scam }: { scam: (typeof scamTypes)[number] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 p-5 text-left"
      >
        <div>
          <div className="font-heading text-base font-semibold text-heading">{scam.title}</div>
          <p className="mt-1 text-sm text-secondary">{scam.summary}</p>
        </div>
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`flex-none text-muted transition-transform ${open ? 'rotate-180' : ''}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="border-t border-hairline bg-canvas px-5 py-4">
          <div className="mb-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted">A real-world example</div>
            <p className="mt-1 text-sm text-body">{scam.example}</p>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-muted">Red flags</div>
            <ul className="mt-1.5 space-y-1">
              {scam.redFlags.map((flag) => (
                <li key={flag} className="flex items-start gap-2 text-sm text-body">
                  <span className="mt-1.5 h-1 w-1 flex-none rounded-full bg-[var(--color-warning)]" />
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

function QuizSection() {
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)

  const allAnswered = scamQuiz.every((q) => answers[q.id])
  const correctCount = scamQuiz.filter((q) => answers[q.id] === q.correctOptionId).length

  function selectOption(question: QuizQuestion, optionId: string) {
    if (submitted) return
    setAnswers((prev) => ({ ...prev, [question.id]: optionId }))
  }

  function reset() {
    setAnswers({})
    setSubmitted(false)
  }

  return (
    <div className="card p-6">
      <div className="mb-1 font-heading text-base font-semibold text-heading">Self-check quiz</div>
      <p className="mb-5 text-sm text-secondary">Four quick scenarios — see how well you can spot the scam.</p>

      <div className="space-y-6">
        {scamQuiz.map((question, i) => {
          const selected = answers[question.id]
          return (
            <div key={question.id}>
              <div className="mb-2.5 text-sm font-medium text-heading">
                {i + 1}. {question.prompt}
              </div>
              <div className="flex flex-col gap-2">
                {question.options.map((option) => {
                  const isSelected = selected === option.id
                  const isCorrect = option.id === question.correctOptionId
                  const showResult = submitted
                  let style = 'border-border text-body hover:bg-hairline'
                  if (showResult && isCorrect) {
                    style = 'border-[var(--color-positive)] bg-[var(--color-positive-soft)] text-heading font-medium'
                  } else if (showResult && isSelected && !isCorrect) {
                    style = 'border-[var(--color-warning)] bg-[var(--color-warning-soft)] text-heading'
                  } else if (isSelected) {
                    style = 'border-primary bg-primary-soft text-heading font-medium'
                  }
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectOption(question, option.id)}
                      disabled={submitted}
                      className={`rounded-sm border px-3.5 py-2.5 text-left text-sm transition-colors disabled:cursor-default ${style}`}
                    >
                      {option.label}
                    </button>
                  )
                })}
              </div>
              {submitted && (
                <p className="mt-2 text-xs text-secondary">{question.explanation}</p>
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-6 flex items-center gap-3">
        {!submitted ? (
          <button
            onClick={() => setSubmitted(true)}
            disabled={!allAnswered}
            className="rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Check my answers
          </button>
        ) : (
          <>
            <div className="text-sm font-semibold text-heading">
              {correctCount} / {scamQuiz.length} correct
            </div>
            <button onClick={reset} className="text-sm font-medium text-primary hover:underline">
              Try again
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export function ScamAwarenessPage() {
  return (
    <div>
      <div className="mb-8 flex items-center gap-3">
        <ScamAwarenessArt size={44} />
        <div>
          <h1 className="font-heading text-h2 font-bold text-heading">Scam awareness</h1>
          <p className="mt-1.5 text-sm text-muted">
            Educational content on common digital fraud patterns in India — not a substitute for your bank's or the police's guidance.
          </p>
        </div>
      </div>

      <div className="mb-10">
        <h2 className="font-heading mb-4 text-lg font-semibold text-heading">Common scam types</h2>
        <div className="space-y-3">
          {scamTypes.map((scam) => (
            <ScamTypeCard key={scam.id} scam={scam} />
          ))}
        </div>
      </div>

      <div className="mb-10 grid grid-cols-1 gap-5 lg:grid-cols-[1.3fr_1fr]">
        <div className="card p-6">
          <h2 className="font-heading mb-4 text-lg font-semibold text-heading">If you think you've been targeted</h2>
          <ol className="space-y-4">
            {whatToDoIfTargeted.map((step, i) => (
              <li key={step.title} className="flex gap-3">
                <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
                  {i + 1}
                </span>
                <div>
                  <div className="text-sm font-semibold text-heading">{step.title}</div>
                  <p className="mt-0.5 text-sm text-secondary">{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <div className="card flex flex-col justify-between p-6" style={{ background: 'var(--color-heading)' }}>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-white/60">Report fraud — India</div>
            <div className="mt-3 font-heading text-3xl font-bold text-white">{reportingChannels.helplineNumber}</div>
            <p className="mt-1 text-sm text-white/70">National Cyber Crime Helpline</p>
          </div>
          <div className="mt-6">
            <a
              href={reportingChannels.portalUrl}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-semibold text-white underline decoration-white/40 underline-offset-4 hover:decoration-white"
            >
              {reportingChannels.portalName} →
            </a>
            <p className="mt-2 text-xs leading-relaxed text-white/60">{reportingChannels.note}</p>
          </div>
        </div>
      </div>

      <QuizSection />
    </div>
  )
}
