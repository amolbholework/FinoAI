/** A one-line plain-language reading of the chart above it — required so a
 * user who can't (or doesn't want to) parse a chart still gets the answer.
 * Every chart on the dashboard should be followed by one of these. */
export function ChartCaption({ children }: { children: React.ReactNode }) {
  return <p className="mt-3 text-sm leading-relaxed text-secondary">{children}</p>
}
