import styles from './Button.module.css';

export function Button({ label }: { label: string }) {
  return (
    <button className={styles.button}>
      {label}
    </button>
  );
}
