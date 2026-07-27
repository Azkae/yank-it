import styles from './StudyStepsList.module.css';
import { Button } from './Button';

export function StudyStepsList() {
  return (
    <section className={styles.tasksCol}>
      <div className={styles.langSelector}>
        <div className={styles.langDropdownWrap}>
          <Button label="Select language" />
        </div>
      </div>
    </section>
  );
}
