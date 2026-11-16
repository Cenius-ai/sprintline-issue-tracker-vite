export type IssueStatus = 'backlog' | 'todo' | 'in_progress' | 'in_review' | 'done';
export type IssuePriority = 'urgent' | 'high' | 'medium' | 'low' | 'none';
export type SprintStatus = 'planned' | 'active' | 'completed';
export type ActivityKind =
  | 'created'
  | 'status_changed'
  | 'priority_changed'
  | 'assignee_changed'
  | 'sprint_changed'
  | 'comment_added';

export interface User {
  id: number;
  email: string;
  name: string;
  avatar_color: string;
}

export interface Project {
  id: number;
  key: string;
  name: string;
  description: string;
  color: string;
}

export interface Label {
  id: number;
  name: string;
  color: string;
}

export interface SprintRef {
  id: number;
  name: string;
  status: SprintStatus;
}

export interface Sprint {
  id: number;
  project_id: number;
  project_key: string;
  project_name: string;
  name: string;
  goal: string;
  start_date: string;
  end_date: string;
  status: SprintStatus;
  issue_count: number;
  point_count: number;
  done_count: number;
}

export interface Issue {
  id: number;
  key: string;
  title: string;
  description: string;
  status: IssueStatus;
  priority: IssuePriority;
  estimate: number;
  project: Project;
  sprint: SprintRef | null;
  assignee: User | null;
  created_by: User | null;
  labels: Label[];
  comment_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface IssueList {
  items: Issue[];
  total: number;
  limit: number;
  offset: number;
}

export interface Comment {
  id: number;
  issue_id: number;
  body: string;
  author: User;
  created_at: string;
}

export interface Activity {
  id: number;
  issue_id: number;
  issue_key: string;
  issue_title: string;
  kind: ActivityKind;
  field: string | null;
  from_value: string | null;
  to_value: string | null;
  actor: User;
  created_at: string;
}

export interface ActivityList {
  items: Activity[];
  total: number;
}

export interface BurndownPoint {
  date: string;
  ideal: number;
  actual: number;
}

export interface Burndown {
  sprint_id: number;
  sprint_name: string;
  sprint_status: SprintStatus;
  start_date: string;
  end_date: string;
  total_points: number;
  completed_points: number;
  days: number;
  points: BurndownPoint[];
}

export interface RoadmapCard {
  id: number;
  key: string;
  title: string;
  status: IssueStatus;
  priority: IssuePriority;
  estimate: number;
  assignee: User | null;
}

export type RoadmapLaneKey = 'now' | 'next' | 'later' | 'done';

export interface RoadmapProject {
  project: Project;
  lanes: Record<RoadmapLaneKey, RoadmapCard[]>;
  counts: Record<RoadmapLaneKey, number>;
}

export interface Roadmap {
  lanes: RoadmapLaneKey[];
  projects: RoadmapProject[];
}

export interface LoginResponse {
  token: string;
  token_type: string;
  expires_at: string;
  user: User;
}
