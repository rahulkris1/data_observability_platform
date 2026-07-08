import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ToastProvider } from '@/contexts/ToastContext'
import ToastNotification from '@/components/ToastNotification'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ToastProvider>
      <Component {...pageProps} />
      <ToastNotification />
    </ToastProvider>
  )
}
