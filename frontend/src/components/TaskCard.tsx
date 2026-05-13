import { useState } from 'react'
import type { Task } from '../types'

interface Props {
  task: Task
  onToggle: (task: Task) => Promise<void>
  onEdit: (task: Task) => void
  onDelete: (id: number) => Promise<void>
}

const priorityColors = {
  low: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400',
  high: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
}

export default function TaskCard({ task, onToggle, onEdit, onDelete }: Props) {
  const [confirming, setConfirming] = useState(false)
  const [toggling, setToggling] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const isOverdue =
    task.status !== 'completed' &&
    task.due_date &&
    new Date(task.due_date) < new Date()

  const handleToggle = async () => {
    setToggling(true)
    try { await onToggle(task) } finally { setToggling(false) }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try { await onDelete(task.id) } finally { setDeleting(false) }
  }

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 flex gap-3 items-start transition-opacity ${task.status === 'completed' ? 'opacity-60' : ''}`}>
      <button
        onClick={handleToggle}
        disabled={toggling}
        className={`mt-0.5 w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center transition-colors disabled:opacity-50 ${
          task.status === 'completed'
            ? 'bg-indigo-600 border-indigo-600'
            : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400'
        }`}
      >
        {toggling ? (
          <svg className="w-3 h-3 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
          </svg>
        ) : task.status === 'completed' ? (
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : null}
      </button>

      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium text-gray-900 dark:text-gray-100 ${task.status === 'completed' ? 'line-through' : ''}`}>
          {task.title}
        </p>
        {task.description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{task.description}</p>
        )}
        <div className="flex flex-wrap items-center gap-2 mt-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priorityColors[task.priority]}`}>
            {task.priority}
          </span>
          {task.recurrence && task.recurrence !== 'none' && (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
              {task.recurrence}
            </span>
          )}
          {task.due_date && (
            <span className={`text-xs ${isOverdue ? 'text-red-500 dark:text-red-400 font-medium' : 'text-gray-400 dark:text-gray-500'}`}>
              Due {new Date(task.due_date).toLocaleDateString()}
              {isOverdue && ' · overdue'}
            </span>
          )}
          {task.note_count > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h6m-6 4h10M5 4h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z" />
              </svg>
              {task.note_count}
            </span>
          )}
        </div>
      </div>

      <div className="flex gap-1 shrink-0 items-center">
        {confirming ? (
          <>
            <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">Delete?</span>
            <button
              onClick={() => setConfirming(false)}
              className="px-2 py-1 text-xs rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="px-2 py-1 text-xs rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {deleting ? '…' : 'Delete'}
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onEdit(task)}
              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Edit"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a2 2 0 01-1.414.586H9v-2a2 2 0 01.586-1.414z" />
              </svg>
            </button>
            <button
              onClick={() => setConfirming(true)}
              className="p-1.5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7h6m2 0a1 1 0 00-1-1h-4a1 1 0 00-1 1H5" />
              </svg>
            </button>
          </>
        )}
      </div>
    </div>
  )
}
