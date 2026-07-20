import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ToastProvider } from '@/contexts/ToastContext'
import ToastNotification from '@/components/ToastNotification'
import ErrorBoundary from '@/components/ErrorBoundary'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Component {...pageProps} />
        <ToastNotification />
      </ToastProvider>
    </ErrorBoundary>
  )
}
