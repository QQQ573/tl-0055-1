import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL,
  timeout: 10000
})

export const getTickets = (params) => api.get('/tickets', { params })
export const getTicket = (id) => api.get(`/tickets/${id}`)
export const createTicket = (data) => api.post('/tickets', data)
export const updateTicket = (id, data) => api.put(`/tickets/${id}`, data)
export const deleteTicket = (id) => api.delete(`/tickets/${id}`)
export const transitionStatus = (id, data) => api.post(`/tickets/${id}/transition`, data)
export const getOperationLogs = (id, params) => api.get(`/tickets/${id}/logs`, { params })
export const uploadImages = (id, formData) => api.post(`/tickets/${id}/images`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getBrands = () => api.get('/brands')
export const getComplaintTypes = () => api.get('/complaint-types')
export const getCompensationTypes = () => api.get('/compensation-types')
export const getStatuses = () => api.get('/statuses')
export const getSlaConfig = () => api.get('/sla-config')
export const getActions = () => api.get('/actions')

export default api
