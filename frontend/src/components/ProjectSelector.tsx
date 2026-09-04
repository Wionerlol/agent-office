import { useAgentStore } from "../store/agents";

export function ProjectSelector() {
  const projects = useAgentStore((state) => state.projects);
  const selected = useAgentStore((state) => state.selectedProjectPath);
  const select = useAgentStore((state) => state.selectProject);
  if (projects.length < 2) return null;
  return (
    <label className="project-selector">
      Project
      <select value={selected ?? ""} onChange={(event) => select(event.target.value || null)}>
        <option value="">All projects</option>
        {projects.map((project) => <option key={project.path} value={project.path}>{project.name}</option>)}
      </select>
    </label>
  );
}
