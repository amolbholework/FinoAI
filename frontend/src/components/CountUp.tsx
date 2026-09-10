import { useEffect, useRef, useState } from 'react'
import { animate, useMotionValue, useMotionValueEvent } from 'framer-motion'

export function CountUp({ value, formatter }: { value: number; formatter: (n: number) => string }) {
  const motionValue = useMotionValue(0)
  const [display, setDisplay] = useState(formatter(0))
  const prevValue = useRef(0)

  useMotionValueEvent(motionValue, 'change', (latest) => setDisplay(formatter(Math.round(latest))))

  useEffect(() => {
    const controls = animate(motionValue, value, { duration: 0.8, ease: [0.16, 1, 0.3, 1] })
    prevValue.current = value
    return () => controls.stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return <span className="tabular-nums">{display}</span>
}
