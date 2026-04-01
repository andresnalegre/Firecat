import { api } from './api'

export const preferencesService = {
  get:  ()      => api.get('/preferences/'),
  save: (prefs) => api.post('/preferences/', prefs),
}