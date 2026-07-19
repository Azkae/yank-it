import styles from './Task.module.css';

export function Task({ summary }: { summary: string }) {
  return (
    <div className="taskRow">
      <p className={styles.taskSummary}>{summary}</p>
    </div>
  );
}
