import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { BrandMark } from '../components/BrandMark'
import { DotGridDivider } from '../components/illustrations/DotGridDivider'
import type { OnboardingProfile, OnboardingQuestion } from '../lib/types'

export function OnboardingPage() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()

  const [questions, setQuestions] = useState<OnboardingQuestion[] | null>(null)
  const [profile, setProfile] = useState<OnboardingProfile | null>(null)
  const [stepIndex, setStepIndex] = useState(0)
  const [selection, setSelection] = useState<string | string[] | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    Promise.all([api.get<OnboardingQuestion[]>('/api/onboarding/questions'), api.get<OnboardingProfile>('/api/onboarding/profile')]).then(
      ([questionsRes, profileRes]) => {
        setQuestions(questionsRes.data)
        setProfile(profileRes.data)
        const resumeAt = Math.min(profileRes.data.current_step, questionsRes.data.length - 1)
        setStepIndex(resumeAt)
        const question = questionsRes.data[resumeAt]
        setSelection(question ? (profileRes.data.answers[question.id] ?? null) : null)
      },
    )
  }, [])

  const question = questions?.[stepIndex]
  const totalSteps = questions?.length ?? 0
  const progressPct = totalSteps > 0 ? Math.round((stepIndex / totalSteps) * 100) : 0

  const isMulti = question?.type === 'multi_choice'
  const selectedList = useMemo(() => (Array.isArray(selection) ? selection : []), [selection])

  function loadAnswerFor(index: number) {
    if (!questions || !profile) return
    const q = questions[index]
    setSelection(profile.answers[q.id] ?? null)
  }

  async function goToStep(index: number) {
    setStepIndex(index)
    loadAnswerFor(index)
  }

  async function submitCurrent(value: string | string[] | null) {
    if (!question) return
    setSubmitting(true)
    try {
      const res = await api.post<OnboardingProfile>('/api/onboarding/answer', { question_id: question.id, value })
      setProfile(res.data)
      if (stepIndex + 1 >= totalSteps) {
        await finishQuiz()
      } else {
        await goToStep(stepIndex + 1)
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function finishQuiz() {
    await api.post('/api/onboarding/complete')
    await refreshUser()
    navigate('/dashboard', { replace: true })
  }

  async function handleSkipWholeQuiz() {
    setSubmitting(true)
    try {
      await api.post('/api/onboarding/skip')
      await refreshUser()
      navigate('/dashboard', { replace: true })
    } finally {
      setSubmitting(false)
    }
  }

  function toggleMultiOption(value: string) {
    const current = selectedList
    const max = question?.max_selections
    if (current.includes(value)) {
      setSelection(current.filter((v) => v !== value))
      return
    }
    if (max && current.length >= max) return
    setSelection([...current, value])
  }

  if (!questions || !profile || !question) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <div className="skeleton h-8 w-48" />
      </div>
    )
  }

  const canContinue = isMulti ? selectedList.length > 0 : !!selection

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-canvas">
      <DotGridDivider className="pointer-events-none absolute inset-0 z-0" />
      <header className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10">
        <BrandMark size={22} />
        <button
          onClick={handleSkipWholeQuiz}
          disabled={submitting}
          className="text-sm font-medium text-muted hover:text-secondary"
        >
          Skip for now
        </button>
      </header>

      <div className="relative z-10 px-6 sm:px-10">
        <div className="mx-auto h-1.5 w-full max-w-lg overflow-hidden rounded-full bg-hairline">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="mx-auto mt-2 max-w-lg text-xs text-muted">
          Question {stepIndex + 1} of {totalSteps}
        </div>
      </div>

      <main className="relative z-10 flex flex-1 items-center justify-center px-6 py-8 sm:px-10">
        <div className="w-full max-w-lg rounded-lg bg-card p-8 shadow-[var(--shadow-card)]">
          <h1 className="font-heading text-h4 font-bold text-heading">{question.prompt}</h1>
          {question.help_text && <p className="mt-2 text-sm text-muted">{question.help_text}</p>}

          <div className="mt-6 flex flex-col gap-2.5">
            {question.options.map((option) => {
              const selected = isMulti ? selectedList.includes(option.value) : selection === option.value
              return (
                <button
                  key={option.value}
                  onClick={() => (isMulti ? toggleMultiOption(option.value) : setSelection(option.value))}
                  className={`rounded-sm border px-4 py-3 text-left text-sm transition-colors ${
                    selected
                      ? 'border-primary bg-primary-soft text-heading font-medium'
                      : 'border-border text-body hover:bg-hairline'
                  }`}
                >
                  {isMulti && selected && (
                    <span className="mr-2 text-xs font-semibold text-primary">
                      {selectedList.indexOf(option.value) + 1}
                    </span>
                  )}
                  {option.label}
                </button>
              )
            })}
          </div>

          <div className="mt-8 flex items-center justify-between">
            <button
              onClick={() => stepIndex > 0 && goToStep(stepIndex - 1)}
              disabled={stepIndex === 0 || submitting}
              className="text-sm font-medium text-secondary hover:text-heading disabled:cursor-not-allowed disabled:opacity-40"
            >
              Back
            </button>

            <div className="flex items-center gap-3">
              {question.skippable && (
                <button
                  onClick={() => submitCurrent(null)}
                  disabled={submitting}
                  className="text-sm font-medium text-muted hover:text-secondary"
                >
                  Skip
                </button>
              )}
              <button
                onClick={() => submitCurrent(selection)}
                disabled={!canContinue || submitting}
                className="rounded-sm bg-primary px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                {stepIndex + 1 >= totalSteps ? 'Finish' : 'Continue'}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
