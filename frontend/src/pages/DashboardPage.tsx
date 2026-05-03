import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useToast } from '../hooks/useToast'
import { getTasks, createTask, updateTask, deleteTask, getStats } from '../api/tasks'
import type { Task, Stats, TaskCreate } from '../types'
import TaskCard from '../components/TaskCard'
import TaskModal from '../components/TaskModal'

const STATUS_FILTERS = ['all', 'pending', 'completed'] as const
type StatusFilter = (typeof STATUS_FILTERS)[number]

const PRIORITY_FILTERS = ['all', 'low', 'medium', 'high'] as const
type PriorityFilter = (typeof PRIORITY_FILTERS)[number]

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'due_date', label: 'Due date' },
  { value: 'priority', label: 'Priority' },
] as const
type SortOption = (typeof SORT_OPTIONS)[number]['value']

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 }

function sortTasks(tasks: Task[], sort: SortOption): Task[] {
  return [...tasks].sort((a, b) => {
    if (sort === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    if (sort === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    if (sort === 'priority') return PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
    if (sort === 'due_date') {
      if (!a.due_date && !b.due_date) return 0
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
    }
    return 0
  })
}

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const toast = useToast()
  const [tasks, setTasks] = useState<Task[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all')
  const [sort, setSort] = useState<SortOption>('newest')
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [loadingTasks, setLoadingTasks] = useState(true)

  const fetchAll = useCallback(async () => {
    const params: { status?: string; priority?: string } = {}
    if (statusFilter !== 'all') params.status = statusFilter
    if (priorityFilter !== 'all') params.priority = priorityFilter
    const [t, s] = await Promise.all([getTasks(params), getStats()])
    setTasks(t)
    setStats(s)
    setLoadingTasks(false)
  }, [statusFilter, priorityFilter])

  useEffect(() => { fetchAll() }, [fetchAll])

  const displayedTasks = useMemo(() => {
    const q = search.trim().toLowerCase()
    const filtered = q ? tasks.filter(t => t.title.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q)) : tasks
    return sortTasks(filtered, sort)
  }, [tasks, search, sort])

  const handleCreate = async (data: TaskCreate) => {
    await createTask(data)
    await fetchAll()
    toast.success('Task created')
  }

  const handleEdit = async (data: TaskCreate) => {
    if (!editingTask) return
    await updateTask(editingTask.id, data)
    await fetchAll()
    toast.success('Task updated')
  }

  const handleToggle = async (task: Task) => {
    await updateTask(task.id, { status: task.status === 'completed' ? 'pending' : 'completed' })
    await fetchAll()
  }

  const handleDelete = async (id: number) => {
    await deleteTask(id)
    await fetchAll()
    toast.success('Task deleted')
  }

  const openCreate = () => { setEditingTask(null); setShowModal(true) }
  const openEdit = (task: Task) => { setEditingTask(task); setShowModal(true) }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white">TaskManager</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">{user?.email}</span>
          <Link
            to="/settings"
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Settings"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </Link>
          <button
            onClick={logout}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            {[
              { label: 'Total', value: stats.total, color: 'text-gray-900 dark:text-white' },
              { label: 'Pending', value: stats.pending, color: 'text-yellow-600 dark:text-yellow-400' },
              { label: 'Completed', value: stats.completed, color: 'text-green-600 dark:text-green-400' },
              { label: 'Overdue', value: stats.overdue, color: 'text-red-500 dark:text-red-400' },
            ].map((s) => (
              <div key={s.label} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
                <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Search */}
        <div className="relative mb-4">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tasks…"
            className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex gap-2 flex-wrap">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
                  statusFilter === f
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {f}
              </button>
            ))}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as PriorityFilter)}
              className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortOption)}
              className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <button
            onClick={openCreate}
            className="flex items-center gap-1.5 bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New task
          </button>
        </div>

        {/* Task list */}
        {loadingTasks ? (
          <div className="text-center py-16 text-gray-400 text-sm">Loading…</div>
        ) : displayedTasks.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-400 dark:text-gray-500 text-sm">
              {search ? `No tasks match "${search}"` : 'No tasks found.'}
            </p>
            {!search && (
              <button onClick={openCreate} className="mt-3 text-indigo-600 dark:text-indigo-400 text-sm hover:underline">
                Create your first task
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {displayedTasks.map((task) => (
              <TaskCard key={task.id} task={task} onToggle={handleToggle} onEdit={openEdit} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <TaskModal task={editingTask} onClose={() => setShowModal(false)} onSave={editingTask ? handleEdit : handleCreate} />
      )}
    </div>
  )
}
