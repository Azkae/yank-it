import { Task } from './Task';

export function Page() {
  return (
    <section className="page">
      <div className="taskList">
        <Task summary="hello" />
      </div>
    </section>
  );
}
