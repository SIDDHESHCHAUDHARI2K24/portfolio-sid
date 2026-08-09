import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { setNavigate } from './lib/api.ts'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof Error && error.name === 'AuthRedirect') return false
        return failureCount < 1
      },
    },
    mutations: {
      onError: (error) => {
        if (error instanceof Error && error.name === 'AuthRedirect') {
          return
        }
      },
    },
  },
})

function Root() {
  const navigate = useNavigate()
  setNavigate(navigate)
  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Root />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
