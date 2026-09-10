import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Skeleton } from '../components/Skeleton'
import { MarketEducationArt } from '../components/illustrations/MarketEducationArt'
import type { EducationModule, EducationProgress, EducationLesson } from '../lib/types'

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

function LessonRow({
  lesson,
  completed,
  onToggle,
}: {
  lesson: EducationLesson
  completed: boolean
  onToggle: (lessonId: string) => void
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-3 p-4 text-left">
        <span
          className={`flex h-6 w-6 flex-none items-center justify-center rounded-full border text-xs ${
            completed ? 'border-primary bg-primary text-white' : 'border-border text-transparent'
          }`}
        >
          ✓
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-heading">{lesson.title}</div>
          <p className="mt-0.5 truncate text-xs text-muted">{lesson.source}</p>
        </div>
        <svg
          width="16"
          height="16"
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
        <div className="border-t border-hairline bg-canvas px-4 py-4">
          <p className="mb-3 text-sm text-secondary">{lesson.description}</p>
          <div className="aspect-video w-full overflow-hidden rounded-lg bg-black">
            <iframe
              className="h-full w-full"
              src={`https://www.youtube.com/embed/${lesson.youtube_id}`}
              title={lesson.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
          <button
            onClick={() => onToggle(lesson.id)}
            className={`mt-3 rounded-sm px-4 py-2 text-sm font-semibold transition-colors ${
              completed ? 'bg-hairline text-secondary hover:bg-border' : 'bg-primary text-white hover:brightness-110'
            }`}
          >
            {completed ? 'Mark as not watched' : 'Mark as watched'}
          </button>
        </div>
      )}
    </div>
  )
}

export function MarketEducationPage() {
  const { profile } = useAuth()
  const recommendedLevel = profile?.literacy_level ?? null
  const [modules, setModules] = useState<EducationModule[] | null>(null)
  const [progress, setProgress] = useState<EducationProgress | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([api.get<EducationModule[]>('/api/education/curriculum'), api.get<EducationProgress>('/api/education/progress')])
      .then(([modulesRes, progressRes]) => {
        setModules(modulesRes.data)
        setProgress(progressRes.data)
      })
      .catch(() => setError(true))
  }, [])

  async function toggleLesson(lessonId: string) {
    const res = await api.post<EducationProgress>('/api/education/progress/toggle', { lesson_id: lessonId })
    setProgress(res.data)
  }

  if (error) {
    return (
      <div className="card-lifted px-6 py-16 text-center text-sm text-muted">
        Couldn't load the learning path. Try refreshing the page.
      </div>
    )
  }

  if (!modules || !progress) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
      </div>
    )
  }

  const completedSet = new Set(progress.completed_lesson_ids)
  const overallPct = progress.total_lesson_count > 0 ? Math.round((progress.completed_lesson_ids.length / progress.total_lesson_count) * 100) : 0

  // Surface the module matching the onboarding-derived literacy_level first
  // — a starting-point suggestion, not a restriction; every module stays
  // fully visible and reachable regardless of profile.
  const orderedModules = recommendedLevel
    ? [...modules].sort((a, b) => (a.level === recommendedLevel ? -1 : 0) - (b.level === recommendedLevel ? -1 : 0))
    : modules

  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <MarketEducationArt size={44} />
        <div>
          <h1 className="font-heading text-h2 font-bold text-heading">Market education</h1>
          <p className="mt-1.5 text-sm text-muted">A structured path from the basics upward — watch a lesson, mark it done, move on.</p>
        </div>
      </div>

      <div className="card mb-8 p-5">
        <div className="mb-2 flex items-baseline justify-between text-sm">
          <span className="font-medium text-heading">Overall progress</span>
          <span className="text-muted">
            {progress.completed_lesson_ids.length} / {progress.total_lesson_count} lessons
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-hairline">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${overallPct}%` }} />
        </div>
      </div>

      <div className="space-y-10">
        {orderedModules.map((module) => {
          const moduleCompleted = module.lessons.filter((l) => completedSet.has(l.id)).length
          const isRecommended = module.level === recommendedLevel
          return (
            <div key={module.id}>
              <div className="mb-3 flex items-baseline justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading text-lg font-semibold text-heading">{module.title}</h2>
                    <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-semibold text-primary">
                      {LEVEL_LABEL[module.level] ?? module.level}
                    </span>
                    {isRecommended && (
                      <span className="rounded-full bg-[var(--color-positive-soft)] px-2 py-0.5 text-[11px] font-semibold text-[var(--color-positive-ink)]">
                        Recommended for you
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-sm text-muted">{module.description}</p>
                </div>
                <span className="flex-none text-xs text-muted">
                  {moduleCompleted}/{module.lessons.length}
                </span>
              </div>
              <div className="space-y-2.5">
                {module.lessons.map((lesson) => (
                  <LessonRow key={lesson.id} lesson={lesson} completed={completedSet.has(lesson.id)} onToggle={toggleLesson} />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
