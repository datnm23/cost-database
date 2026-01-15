import apiClient from './api'

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    user_id: number
    username: string
    email: string
    full_name: string
    role: string
  }
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    const response = await apiClient.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}
