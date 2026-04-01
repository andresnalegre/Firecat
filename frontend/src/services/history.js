import { api } from './api'

export const historyService = {
  list:      ()     => api.get('/history/'),
  add:       (data) => api.post('/history/', data),
  clear:     ()     => api.delete('/history/'),
  deleteOne: (id)   => api.delete(`/history/${id}/`),
}