export function TaskMultiline({ summary }: { summary: string }) {
  return (
    <div className="taskRow">
      <p
        className="taskSummary"
      >
        {summary}
      </p>
    </div>
  );
}
