import styles from './SegmentedControl.module.css';

export function SegmentedControl({ options, value, onChange, disabled }) {
  return (
    <div className={styles.segmented}>
      {options.map((opt) => {
        const active = opt.value === value;
        const role = "button";
        const selectedAttr = active ? { "aria-selected": true } : {};
        return (
          <button
            key={opt.value}
            type="button"
            role={role}
            {...selectedAttr}
            className={`${styles.segment} ${active ? styles.segmentActive : ""}`}
            onClick={() => onChange(opt.value)}
            disabled={disabled}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
