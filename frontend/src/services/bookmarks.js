import { api } from './api'

export const bookmarksService = {
  list:   ()     => api.get('/bookmarks/'),
  add:    (data) => api.post('/bookmarks/', data),
  remove: (id)   => api.delete(`/bookmarks/${id}/`),
}