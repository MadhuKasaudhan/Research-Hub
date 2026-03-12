import { create } from 'zustand';
import type { Workspace } from '../types';

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  isLoading: boolean;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setActiveWorkspace: (workspace: Workspace | null) => void;
  addWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (id: string, updates: Partial<Workspace>) => void;
  deleteWorkspace: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  activeWorkspace: null,
  isLoading: false,

  setWorkspaces: (workspaces) => set({ workspaces }),
  
  setActiveWorkspace: (workspace) => set({ activeWorkspace: workspace }),
  
  addWorkspace: (workspace) =>
    set((state) => ({ workspaces: [...state.workspaces, workspace] })),
  
  updateWorkspace: (id, updates) =>
    set((state) => ({
      workspaces: state.workspaces.map((w) =>
        w.id === id ? { ...w, ...updates } : w
      ),
      activeWorkspace:
        state.activeWorkspace?.id === id
          ? { ...state.activeWorkspace, ...updates }
          : state.activeWorkspace,
    })),
  
  deleteWorkspace: (id) =>
    set((state) => ({
      workspaces: state.workspaces.filter((w) => w.id !== id),
      activeWorkspace: state.activeWorkspace?.id === id ? null : state.activeWorkspace,
    })),
  
  setLoading: (loading) => set({ isLoading: loading }),
}));
