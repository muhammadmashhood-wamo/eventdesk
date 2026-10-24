import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

export function useNotifCount() {
  const { user } = useAuth()

  const query = useQuery({
    queryKey: ['notifications-count'],
    queryFn: async () => {
      const data = await api.listNotifications({ limit: 1 })
      return data?.unread_count ?? 0
    },
    enabled: !!user,
    staleTime: 10000,
    refetchInterval: 30000,
  })

  return query.data ?? 0
}
